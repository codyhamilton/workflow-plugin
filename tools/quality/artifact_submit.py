#!/usr/bin/env python3
"""Fail-open backstop for plan artifact writes. The HTTP ledger is authoritative."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import time
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import quote

import quality as q
import hooklog


@dataclass
class Artifact:
    file: Path
    repo: Path
    path: str
    kind: str
    project: str
    plan: str
    text: str
    sha: str


def read_artifact(file: str | Path, cwd: str | Path | None = None) -> Artifact | None:
    full = Path(file).expanduser()
    if not full.is_absolute():
        full = Path(cwd or Path.cwd()) / full
    full = full.resolve()
    repo = q.repo_root(full).resolve()
    if not full.is_relative_to(repo):
        return None
    path = full.relative_to(repo).as_posix()
    match = re.fullmatch(r"docs/plans/([^/]+)/(DESIGN\.md|briefs/[^/]+\.md)", path)
    if not match:
        return None
    text = full.read_text(encoding="utf-8")
    sha = hashlib.sha256(q.split_frontmatter(text)[1].encode()).hexdigest()[:16]
    return Artifact(full, repo, path, q.kind_of(full), q.project_name(repo), match[1], text, sha)


class Client:
    """One endpoint, bearer token and timeout for both checks and posts.

    The hook's total HTTP budget leaves room inside the host's five-second limit.
    A caller can omit the deadline when using the helper outside a hook.
    """

    def __init__(self, deadline: float | None = None):
        self.base = os.environ.get("WORKFLOW_QUALITY_URL", "http://127.0.0.1:8765").rstrip("/")
        self.token = os.environ.get("WORKFLOW_QUALITY_TOKEN")
        self.timeout = float(os.environ.get("WORKFLOW_QUALITY_TIMEOUT", "2"))
        self.deadline = deadline

    def request(self, method: str, path: str, body: dict | None = None):
        if not self.base:
            raise ValueError("WORKFLOW_QUALITY_URL is empty")
        timeout = self.timeout
        if self.deadline is not None:
            timeout = min(timeout, self.deadline - time.monotonic())
        if timeout <= 0:
            raise TimeoutError("artifact-submit HTTP budget exhausted")
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        req = urllib.request.Request(self.base + path,
                                     json.dumps(body).encode() if body is not None else None,
                                     headers, method=method)
        with urllib.request.urlopen(req, timeout=timeout) as response:
            return json.load(response)


def is_submitted(artifact: Artifact, conversation_id: str, client: Client | None = None) -> bool:
    client = client or Client()
    session = client.request("GET", "/v1/sessions/" + quote(conversation_id, safe=""))
    for row in session.get("artifacts", []):
        if (row.get("kind"), row.get("project"), row.get("path")) != (artifact.kind, artifact.project, artifact.path):
            continue
        # Session joins also include executions and unrelated lifecycle events.
        # Only score, direct artifact bind, or post/patch evidence qualifies.
        if not row.get("submission_bound"):
            continue
        body = client.request("GET", f"/v1/{artifact.kind}s/{row['id']}/body")
        if body.get("sha") == artifact.sha:
            return True
    return False


def ensure_posted(artifact: Artifact, conversation_id: str, harness: str,
                  client: Client | None = None) -> dict:
    result = {"path": artifact.path, "kind": artifact.kind}
    try:
        client = client or Client()
        try:
            if is_submitted(artifact, conversation_id, client):
                return {**result, "ok": True, "posted": False, "reason": "already submitted"}
        except Exception as exc:
            # A failed check must not stop the best-effort post (upsert is safe).
            result["check_error"] = str(exc)
        try:
            version = json.loads((q.ROOT / ".claude-plugin/plugin.json").read_text()).get("version")
        except Exception:
            version = None
        payload = {"text": artifact.text, "project": artifact.project, "plan": artifact.plan,
                   "path": artifact.path, "repo_path": str(artifact.repo),
                   "conversation_id": conversation_id, "harness": harness, "workflow_version": version}
        if artifact.kind == "brief":
            fm = q.split_frontmatter(artifact.text)[0]
            design_id = fm.get("design_id")
            if not design_id:
                design = artifact.repo / "docs/plans" / artifact.plan / "DESIGN.md"
                if design.is_file():
                    design_id = q.split_frontmatter(design.read_text())[0].get("design_id")
            if design_id and design_id.isdigit():
                payload["design_id"] = int(design_id)
        response = client.request("POST", f"/v1/{artifact.kind}s", payload)
        if not isinstance(response, dict) or not isinstance(response.get("id"), int):
            raise ValueError("workflow-quality returned no artifact id")
        return {**result, "ok": True, "posted": True, "response": response}
    except Exception as exc:
        return {**result, "ok": False, "reason": f"{type(exc).__name__}: {exc}"}


WRITE_TOOLS = {"write", "edit", "multiedit", "write_file", "edit_file", "create_file",
               "str_replace_editor", "apply_patch", "applypatch"}


def write_paths(payload: dict, harness: str) -> list[str]:
    event = str(payload.get("hook_event_name") or payload.get("event") or "")
    if harness == "cursor" and event == "afterFileEdit":
        return [payload["file_path"]] if isinstance(payload.get("file_path"), str) else []
    expected = {"claude": "PostToolUse", "codex": "PostToolUse", "cursor": "postToolUse",
                "opencode": "tool.execute.after"}
    if event != expected.get(harness) or payload.get("source") == "bus":
        return []
    name = str(payload.get("tool_name") or "").rsplit(".", 1)[-1].lower()
    if name not in WRITE_TOOLS:
        return []
    args = payload.get("tool_input") or {}
    if isinstance(args, str):
        try:
            args = json.loads(args)
        except ValueError:
            args = {"patch": args} if name in ("apply_patch", "applypatch") else {}
    if not isinstance(args, dict):
        return []
    paths = [args[key] for key in ("file_path", "path", "filePath", "target_file")
             if isinstance(args.get(key), str)]
    for edit in args.get("edits", []) if isinstance(args.get("edits"), list) else []:
        if isinstance(edit, dict):
            paths.extend(edit[key] for key in ("file_path", "path", "filePath") if isinstance(edit.get(key), str))
    if name in ("apply_patch", "applypatch"):
        patch = args.get("patch") or args.get("input") or ""
        if isinstance(patch, str):
            paths.extend(re.findall(r"^\*\*\* (?:Add File|Update File|Move to): (.+)$", patch, re.M))
    return list(dict.fromkeys(paths))


def record_outcome(result: dict, payload: dict, harness: str, conversation_id: str, client: Client):
    row = {"v": 1, "ts": time.time(), "kind": "tool_call", "tool_name": "artifact_submit",
           "ok": result["ok"], "input": {"path": result["path"], "kind": result["kind"]},
           "output": hooklog.clip(result.get("response") or result), "session_id": conversation_id,
           "harness": harness, "hook_event": payload.get("hook_event_name"),
           "cwd": payload.get("cwd") or (payload.get("workspace_roots") or [None])[0]}
    try:
        client.request("POST", "/v1/hook-events", {"rows": [row]})
    except Exception:
        # This is hooklog's outcome spool, never a submission/check store.
        try:
            hooklog.append(row)
        except Exception:
            pass


def run_hook(payload: dict, harness: str, event: str | None = None) -> dict | None:
    if event:
        payload = {**payload, "hook_event_name": event}
    if harness == "auto":
        harness = hooklog.detect_harness(payload)
    outcomes = []
    conversation_id = str(payload.get("conversation_id") or payload.get("session_id") or payload.get("sessionID") or "unknown")
    cwd = payload.get("cwd") or (payload.get("workspace_roots") or [None])[0]
    client = Client(deadline=time.monotonic() + 4)
    seen = set()
    for path in write_paths(payload, harness):
        try:
            artifact = read_artifact(path, cwd)
            if artifact is None or artifact.file in seen:
                continue
            seen.add(artifact.file)
            result = ensure_posted(artifact, conversation_id, harness, client)
        except Exception as exc:
            # Failed reads of plan paths still leave an advisory attempt.
            if not re.search(r"(?:^|/)docs/plans/[^/]+/(?:DESIGN\.md|briefs/[^/]+\.md)$", path):
                continue
            result = {"path": path, "kind": "design" if path.endswith("/DESIGN.md") else "brief",
                      "ok": False, "reason": f"{type(exc).__name__}: {exc}"}
        record_outcome(result, payload, harness, conversation_id, client)
        if result.get("posted"):
            outcomes.append(f"posted {result['kind']}_id={result['response']['id']} for {result['path']}; adopt the returned identity in frontmatter deliberately")
        elif not result["ok"]:
            outcomes.append(f"workflow-quality unavailable; posting still owed for {result['path']} ({result['reason']})")
    if harness in ("claude", "cursor") and outcomes and payload.get("hook_event_name") in ("PostToolUse", "postToolUse"):
        if harness == "cursor":
            return {"additionalContext": "\n".join(outcomes)}
        return {"hookSpecificOutput": {"hookEventName": "PostToolUse", "additionalContext": "\n".join(outcomes)}}
    return {} if harness == "cursor" else None


def main() -> int:
    response = None
    harness = "auto"
    try:
        parser = argparse.ArgumentParser(description=__doc__)
        parser.add_argument("command", choices=["hook"])
        parser.add_argument("--harness", default="auto", choices=["auto", "claude", "cursor", "codex", "opencode"])
        parser.add_argument("--event")
        args = parser.parse_args()
        harness = args.harness
        payload = json.loads(sys.stdin.read() or "{}")
        if isinstance(payload, dict):
            response = run_hook(payload, harness, args.event)
    except (Exception, SystemExit):
        pass  # no error, including malformed input/config, may fail the editor write
    if response is not None or harness == "cursor":
        print(json.dumps(response or {}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
