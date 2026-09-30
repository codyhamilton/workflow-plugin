/**
 * Lab sketch — use packages/opencode-workflow-hooks/src/index.ts for product wiring.
 *
 * This file mirrors the subscription pattern; see package README for opencode.json.
 */
import type { Plugin } from "@opencode-ai/plugin"
import { spawn } from "child_process"
import path from "path"

type PendingCall = { tool: string; callID: string; title: string; output: string }

const pendingBySession = new Map<string, PendingCall[]>()

function repoRootFrom(ctxDir: string): string {
  return process.env.WORKFLOW_REPO_ROOT || path.join(ctxDir, "..", "..")
}

function flushBatch(sessionID: string, ctxDir: string, transcriptPath?: string) {
  const batch = pendingBySession.get(sessionID)
  if (!batch?.length) return
  pendingBySession.set(sessionID, [])

  const helper = path.join(
    repoRootFrom(ctxDir),
    "packages/opencode-workflow-hooks/python/batch_flush_cli.py",
  )
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
  try {
    const child = spawn(process.env.PYTHON || "python3", [helper], {
      stdio: ["pipe", "ignore", "ignore"],
      env: {
        ...process.env,
        WORKFLOW_INSTALL_MODE: process.env.WORKFLOW_INSTALL_MODE || "opencode",
      },
    })
    child.on("error", () => {})
    child.stdin?.write(JSON.stringify(payload))
    child.stdin?.end()
  } catch {
    // advisory
  }
}

export const WorkflowSignalsPlugin: Plugin = async (ctx) => {
  const enabled = process.env.WORKFLOW_OPENCODE_SIGNALS !== "0"
  if (!enabled) return {}

  return {
    "tool.execute.after": async (input, output) => {
      const list = pendingBySession.get(input.sessionID) || []
      list.push({
        tool: input.tool,
        callID: input.callID,
        title: output.title,
        output: output.output,
      })
      pendingBySession.set(input.sessionID, list)
    },

    event: async ({ event }) => {
      if (event.type === "message.updated" || event.type === "session.idle") {
        const sid = (event as { sessionID?: string }).sessionID
        if (sid) flushBatch(sid, ctx.directory)
      }
    },
  }
}

export default WorkflowSignalsPlugin
