/**
 * Lab sketch — workflow soft signals for OpenCode (not published npm).
 *
 * Approximates Claude PostToolBatch by buffering tool.execute.after until the
 * assistant message for the step is complete, then appends JSONL via a small
 * Python helper (or inlined TS gate logic in a real package).
 *
 * Install (manual, lab): copy to .opencode/plugin/workflow-signals.ts and
 * register in opencode.json — see opencode.json.example.
 */
import type { Plugin } from "@opencode-ai/plugin"
import { spawn } from "child_process"
import path from "path"

type PendingCall = { tool: string; callID: string; title: string; output: string }

const pendingBySession = new Map<string, PendingCall[]>()

function repoRootFrom(ctxDir: string): string {
  // consuming repo root; override with WORKFLOW_REPO_ROOT
  return process.env.WORKFLOW_REPO_ROOT || ctxDir
}

function flushBatch(sessionID: string, ctxDir: string, transcriptPath?: string) {
  const batch = pendingBySession.get(sessionID)
  if (!batch?.length) return
  pendingBySession.set(sessionID, [])

  const helper = path.join(
    repoRootFrom(ctxDir),
    "docs/lab/RESEARCH/2026-09-30-opencode-hooks-plugin/proofs/batch_flush_cli.py",
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
  // Non-blocking, advisory — never throw into hook chain
  spawn(process.env.PYTHON || "python3", [helper], {
    stdio: ["pipe", "ignore", "ignore"],
  })
    .stdin?.write(JSON.stringify(payload))
    .end()
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
      // Flush when the assistant finishes a step (heuristic — validate on host).
      if (event.type === "message.updated" || event.type === "session.idle") {
        const sid = (event as { sessionID?: string }).sessionID
        if (sid) flushBatch(sid, ctx.directory)
      }
    },
  }
}

export default WorkflowSignalsPlugin
