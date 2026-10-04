/**
 * OpenCode workflow soft signals — approximates Claude PostToolBatch via
 * tool.execute.after buffering and flush on message.updated / session.idle.
 *
 * Advisory only: never blocks the agent loop. Gate + log via Python helper.
 */
import type { Plugin } from "@opencode-ai/plugin"
import { spawn } from "node:child_process"
import { fileURLToPath } from "node:url"
import path from "node:path"

type PendingCall = { tool: string; callID: string; title: string; output: string }

function packageRoot(): string {
  return path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..")
}

function defaultRepoRoot(ctxDir: string): string {
  return path.join(packageRoot(), "..", "..")
}

function flushHelperPath(): string {
  if (process.env.WORKFLOW_BATCH_FLUSH_CLI) {
    return process.env.WORKFLOW_BATCH_FLUSH_CLI
  }
  return path.join(packageRoot(), "python", "batch_flush_cli.py")
}

// hooklog capture (tools/hooklog): same rows Claude and Cursor hooks write, so the corpus loader treats all harnesses alike.
function hooklogPath(): string {
  return process.env.WORKFLOW_HOOKLOG_CLI || path.join(packageRoot(), "..", "..", "tools", "hooklog", "hooklog.py")
}

async function recordHooklog(payload: Record<string, unknown>): Promise<void> {
  if (/^(0|off|false)$/i.test(process.env.WORKFLOW_HOOKLOG || "")) return
  await runPythonHook(hooklogPath(), ["record", "--harness", "opencode"], payload)
}

async function submitArtifact(payload: Record<string, unknown>): Promise<void> {
  const tool = String(payload.tool_name || "").split(".").at(-1) || ""
  if (!/^(write|edit|multiedit|write_file|edit_file|create_file|str_replace_editor|apply_patch|applypatch)$/i.test(tool)) return
  const helper = process.env.WORKFLOW_ARTIFACT_SUBMIT_CLI || path.join(packageRoot(), "..", "..", "tools", "quality", "artifact_submit.py")
  await runPythonHook(helper, ["hook", "--harness", "opencode"], payload)
}

async function runPythonHook(helper: string, args: string[], payload: Record<string, unknown>): Promise<void> {
  try {
    // Providers/config can contain cycles; capture a snapshot without touching live objects.
    const seen = new WeakSet<object>()
    const snapshot = JSON.stringify(payload, (_key, value) => {
      if (value && typeof value === "object") {
        if (seen.has(value)) return "[Circular]"
        seen.add(value)
      }
      return value
    })
    await new Promise<void>((resolve) => {
      const child = spawn(process.env.PYTHON || process.env.WORKFLOW_PYTHON || "python3", [helper, ...args], {
        stdio: ["pipe", "ignore", "ignore"],
      })
      const timeout = setTimeout(() => { child.kill("SIGKILL"); resolve() }, 5000)
      const finish = () => { clearTimeout(timeout); resolve() }
      child.on("error", finish)
      child.on("close", finish)
      child.stdin?.on("error", () => {})
      child.stdin?.end(snapshot)
    })
  } catch {
    // capture is advisory — never throw into the hook chain
  }
}

function flushBatch(sessionID: string, ctxDir: string, transcriptPath: string | undefined, pendingBySession: Map<string, PendingCall[]>) {
  const batch = pendingBySession.get(sessionID)
  if (!batch?.length) return
  pendingBySession.set(sessionID, [])

  const helper = flushHelperPath()
  const payload = {
    session_id: sessionID,
    transcript_path: transcriptPath || "",
    cwd: ctxDir,
    tool_calls: batch.map((c) => ({
      tool_name: c.tool,
      tool_use_id: c.callID,
      tool_input: {},
      tool_response: c.output.slice(0, 500),
    })),
  }

  const python = process.env.PYTHON || process.env.WORKFLOW_PYTHON || "python3"
  const env = {
    ...process.env,
    WORKFLOW_REPO_ROOT: process.env.WORKFLOW_REPO_ROOT || defaultRepoRoot(ctxDir),
    WORKFLOW_INSTALL_MODE: process.env.WORKFLOW_INSTALL_MODE || "opencode",
  }

  try {
    const child = spawn(python, [helper], {
      stdio: ["pipe", "ignore", "ignore"],
      env,
    })
    child.on("error", () => {})
    child.stdin?.on("error", () => {})
    const stdin = child.stdin
    if (stdin) {
      stdin.write(JSON.stringify(payload))
      stdin.end()
    }
  } catch {
    // advisory — never throw into hook chain
  }
}

// Session IDs live at different depths for message, part and session lifecycle events.
function sessionId(value: unknown, seen = new WeakSet<object>()): string | undefined {
  if (!value || typeof value !== "object") return undefined
  if (seen.has(value)) return undefined
  seen.add(value)
  const v = value as Record<string, unknown>
  for (const key of ["sessionID", "session_id"]) {
    if (typeof v[key] === "string") return v[key] as string
  }
  for (const key of ["properties", "part", "info", "message"]) {
    const nested = v[key] as Record<string, unknown> | undefined
    const found = sessionId(nested, seen)
    if (found) return found
    // Session objects use `id`; message/part IDs must never become session IDs.
    if (key === "info" && typeof nested?.id === "string" && nested.directory) return nested.id
  }
  return undefined
}

export const WorkflowSignalsPlugin: Plugin = async (ctx) => {
  const enabled = process.env.WORKFLOW_OPENCODE_SIGNALS !== "0"
  const ctxDir = ctx.directory
  const pendingBySession = new Map<string, PendingCall[]>()
  const callsThisStep = new Map<string, string[]>()
  // Serial writes retain callback/marker order even when the bus dispatches concurrently.
  let writes = Promise.resolve()
  const record = (...payloads: Record<string, unknown>[]) => {
    writes = writes.then(async () => {
      for (const payload of payloads) await recordHooklog({ cwd: ctxDir, ...payload })
    }).catch(() => {})
    return writes
  }
  const observe = (name: string) => async (input?: unknown, output?: unknown) => {
    await record({ hook_event_name: name, session_id: sessionId(input) || sessionId(output),
                   source: "hook", input, output })
  }

  return {
    config: observe("config"),
    dispose: async () => {
      await observe("dispose")()
      pendingBySession.clear()
      callsThisStep.clear()
    },
    "chat.params": observe("chat.params"),
    "chat.headers": observe("chat.headers"),
    "permission.ask": observe("permission.ask"),
    "command.execute.before": observe("command.execute.before"),
    "tool.definition": observe("tool.definition"),
    "shell.env": observe("shell.env"),
    "experimental.chat.messages.transform": observe("experimental.chat.messages.transform"),
    "experimental.chat.system.transform": observe("experimental.chat.system.transform"),
    "experimental.session.compacting": observe("experimental.session.compacting"),
    "experimental.compaction.autocontinue": observe("experimental.compaction.autocontinue"),
    "experimental.provider.small_model": observe("experimental.provider.small_model"),
    "experimental.text.complete": async (input, output) => {
      await record({ hook_event_name: "experimental.text.complete", session_id: input.sessionID,
                     source: "hook", text: output.text, input, output })
    },
    "chat.message": async (input, output) => {
      const text = (output.parts || [])
        .filter((p: { type?: string }) => p.type === "text")
        .map((p: { text?: string }) => p.text || "")
        .join("\n")
      await record({ hook_event_name: "chat.message", session_id: input.sessionID,
                     source: "hook", prompt: text, input, output })
    },
    "tool.execute.before": async (input, output) => {
      await record({ hook_event_name: "tool.execute.before", session_id: input.sessionID,
                     source: "hook", tool_name: input.tool, tool_use_id: input.callID,
                     tool_input: output.args, input, output })
    },
    "tool.execute.after": async (input, output) => {
      const payload = {
        hook_event_name: "tool.execute.after", session_id: input.sessionID, source: "hook",
        tool_name: input.tool, tool_use_id: input.callID, tool_input: input.args ?? {},
        tool_response: output.output ?? output.title ?? "", input, output,
      }
      await record(payload)
      await submitArtifact({ cwd: ctxDir, ...payload })
      callsThisStep.set(input.sessionID, [...(callsThisStep.get(input.sessionID) || []), input.callID])
      if (!enabled) return
      const list = pendingBySession.get(input.sessionID) || []
      list.push({ tool: input.tool, callID: input.callID, title: output.title ?? "", output: output.output ?? "" })
      pendingBySession.set(input.sessionID, list)
    },
    event: async ({ event }) => {
      // Catch all 28 catalog bus types, plus future/undocumented types without a whitelist.
      const sid = sessionId(event)
      const rows: Record<string, unknown>[] = [{ hook_event_name: event.type, session_id: sid, source: "bus", event }]
      const e = event as { type: string; properties?: { part?: { type?: string } } }
      if (sid && e.type === "message.part.updated" && e.properties?.part?.type === "step-finish") {
        rows.push({ hook_event_name: "PostToolBatch", session_id: sid, source: "derived",
                       tool_calls: (callsThisStep.get(sid) || []).map((id) => ({ tool_use_id: id })) })
        callsThisStep.set(sid, [])
      } else if (sid && e.type === "session.idle") {
        rows.push({ hook_event_name: "Stop", session_id: sid, source: "derived" })
      }
      await record(...rows)  // queue derived markers before teardown can drain the queue
      if (enabled && sid && (event.type === "message.updated" || event.type === "session.idle")) {
        flushBatch(sid, ctxDir, undefined, pendingBySession)
      }
    },
  }
}

export default WorkflowSignalsPlugin
