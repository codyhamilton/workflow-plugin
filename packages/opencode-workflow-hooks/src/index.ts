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

const pendingBySession = new Map<string, PendingCall[]>()

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

function recordHooklog(payload: Record<string, unknown>) {
  if (/^(0|off|false)$/i.test(process.env.WORKFLOW_HOOKLOG || "")) return
  try {
    const child = spawn(process.env.PYTHON || process.env.WORKFLOW_PYTHON || "python3", [hooklogPath(), "record", "--harness", "opencode"], {
      stdio: ["pipe", "ignore", "ignore"],
    })
    child.on("error", () => {})
    child.stdin?.on("error", () => {})
    child.stdin?.end(JSON.stringify(payload))
  } catch {
    // capture is advisory — never throw into the hook chain
  }
}

function flushBatch(sessionID: string, ctxDir: string, transcriptPath?: string) {
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
    const stdin = child.stdin
    if (stdin) {
      stdin.write(JSON.stringify(payload))
      stdin.end()
    }
  } catch {
    // advisory — never throw into hook chain
  }
}

function sessionIdFromEvent(event: { type: string; sessionID?: string; properties?: Record<string, unknown> }) {
  if (event.sessionID) return event.sessionID
  const props = event.properties
  if (props && typeof props.sessionID === "string") return props.sessionID
  if (props && typeof props.session_id === "string") return props.session_id
  return undefined
}

export const WorkflowSignalsPlugin: Plugin = async (ctx) => {
  const enabled = process.env.WORKFLOW_OPENCODE_SIGNALS !== "0"
  if (!enabled) return {}

  const ctxDir = ctx.directory

  const callsThisStep = new Map<string, string[]>()

  return {
    "chat.message": async (input, output) => {
      const text = (output.parts || [])
        .filter((p: { type?: string }) => p.type === "text")
        .map((p: { text?: string }) => p.text || "")
        .join("\n")
      if (text) recordHooklog({ hook_event_name: "UserPromptSubmit", session_id: input.sessionID, cwd: ctxDir, prompt: text })
    },

    "tool.execute.after": async (input, output) => {
      recordHooklog({
        hook_event_name: "PostToolUse",
        session_id: input.sessionID,
        cwd: ctxDir,
        tool_name: input.tool,
        tool_use_id: input.callID,
        tool_input: input.args ?? {},
        tool_response: typeof output.output === "string" ? output.output : output.title ?? "",
      })
      callsThisStep.set(input.sessionID, [...(callsThisStep.get(input.sessionID) || []), input.callID])
      const list = pendingBySession.get(input.sessionID) || []
      const text =
        typeof output.output === "string"
          ? output.output
          : output.title || JSON.stringify(output.output ?? "").slice(0, 500)
      list.push({
        tool: input.tool,
        callID: input.callID,
        title: output.title ?? "",
        output: text,
      })
      pendingBySession.set(input.sessionID, list)
    },

    event: async ({ event }) => {
      const e = event as { type: string; properties?: { part?: { type?: string }; sessionID?: string } }
      const hsid = sessionIdFromEvent(event as { type: string; sessionID?: string; properties?: Record<string, unknown> })
      if (hsid && e.type === "message.part.updated" && e.properties?.part?.type === "step-finish") {
        // one model response finished: close its tool batch (Claude PostToolBatch equivalent)
        recordHooklog({ hook_event_name: "PostToolBatch", session_id: hsid, cwd: ctxDir,
                        tool_calls: (callsThisStep.get(hsid) || []).map((id) => ({ tool_use_id: id })) })
        callsThisStep.set(hsid, [])
      } else if (hsid && e.type === "session.idle") {
        recordHooklog({ hook_event_name: "Stop", session_id: hsid, cwd: ctxDir })
      }
      if (event.type === "message.updated" || event.type === "session.idle") {
        const sid = sessionIdFromEvent(event as { type: string; sessionID?: string; properties?: Record<string, unknown> })
        if (sid) flushBatch(sid, ctxDir)
      }
    },
  }
}

export default WorkflowSignalsPlugin
