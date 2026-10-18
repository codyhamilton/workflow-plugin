#!/usr/bin/env python3
"""Yakka plugin client: config, keys, secrets, and command dispatch (stdlib only)."""

from __future__ import annotations

import fcntl
import hashlib
import json
import os
import random
import re
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from typing import Any, Callable, List, Optional, Tuple, Union

# --- clientconfig ---

LocalEndpoint = "http://127.0.0.1:8770"

_ENV_ENDPOINT = "YAKKA_ENDPOINT"
_ENV_KEY = "YAKKA_KEY"


class ErrPartialEnv(Exception):
    def __init__(self) -> None:
        super().__init__(
            "clientconfig: YAKKA_ENDPOINT and YAKKA_KEY must both be set or both unset"
        )


class Config:
    def __init__(self, Endpoint: str = "", Key: str = "", Local: bool = False) -> None:
        self.Endpoint = Endpoint
        self.Key = Key
        self.Local = Local

    def Mode(self) -> str:
        return "local" if self.Local else "remote"


_line_re = re.compile(
    r'^([A-Za-z_][A-Za-z0-9_-]*)\s*=\s*("(?:[^"\\]|\\.)*")\s*(?:#.*)?$'
)


def Path() -> str:
    p = os.environ.get("YAKKA_CLIENT_CONFIG", "")
    if p:
        return p
    home = os.environ.get("HOME", "")
    if not home:
        home = os.path.expanduser("~")
    return os.path.join(home, ".config", "yakka", "client.toml")


def Load() -> Config:
    ep = os.environ.get(_ENV_ENDPOINT, "").strip()
    key = os.environ.get(_ENV_KEY, "").strip()
    ep_set = ep != ""
    key_set = key != ""
    if ep_set and key_set:
        return Config(Endpoint=ep, Key=key)
    if ep_set or key_set:
        raise ErrPartialEnv()
    path = Path()
    try:
        with open(path, encoding="utf-8") as f:
            data = f.read()
    except FileNotFoundError:
        return Config(Endpoint=LocalEndpoint, Local=True)
    except OSError as err:
        raise OSError(f"clientconfig: read {path}: {err}") from err
    return _parse_config(path, data)


def _parse_config(path: str, text: str) -> Config:
    vals: dict[str, str] = {}
    for i, line in enumerate(text.split("\n")):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        m = _line_re.match(line)
        if not m:
            raise ValueError(
                f'clientconfig: {path}: line {i + 1} is not a `name = "string"` line'
            )
        try:
            v = json.loads(m.group(2))
        except json.JSONDecodeError:
            raise ValueError(
                f"clientconfig: {path}: line {i + 1} has an invalid string"
            ) from None
        vals[m.group(1)] = v
    cfg = Config(Endpoint=vals.get("endpoint", ""), Key=vals.get("key", ""))
    if not cfg.Endpoint:
        raise ValueError(f"clientconfig: {path}: missing endpoint")
    if not cfg.Key:
        raise ValueError(f"clientconfig: {path}: missing key")
    return cfg


# --- keys ---


class _Number:
    __slots__ = ("s",)

    def __init__(self, s: str) -> None:
        self.s = s


def ContentHash(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def _serialize_json_value(v: Any) -> str:
    if isinstance(v, dict):
        keys = sorted(v.keys())
        inner = ",".join(
            json.dumps(k, ensure_ascii=False) + ":" + _serialize_json_value(v[k])
            for k in keys
        )
        return "{" + inner + "}"
    if isinstance(v, list):
        return "[" + ",".join(_serialize_json_value(x) for x in v) + "]"
    if isinstance(v, _Number):
        return v.s
    if v is True:
        return "true"
    if v is False:
        return "false"
    if v is None:
        return "null"
    if isinstance(v, int):
        return str(v)
    if isinstance(v, str):
        return json.dumps(v, ensure_ascii=False)
    raise TypeError(f"keys: unsupported JSON value type {type(v)}")


def Canonical(raw: bytes) -> bytes:
    text = raw.decode("utf-8") if isinstance(raw, bytes) else raw
    dec = json.JSONDecoder(parse_float=lambda s: _Number(s))
    try:
        obj, end = dec.raw_decode(text)
    except json.JSONDecodeError as err:
        raise ValueError(f"keys: not a JSON object: {err}") from err
    if text[end:].strip():
        raise ValueError("keys: trailing data after JSON object")
    if obj is None:
        raise ValueError("keys: not a JSON object: null")
    if not isinstance(obj, dict):
        raise ValueError(f"keys: not a JSON object: {type(obj).__name__}")
    obj = dict(obj)
    obj.pop("id", None)
    obj.pop("content", None)
    return _serialize_json_value(obj).encode("utf-8")


def RowHash(raw: bytes) -> Tuple[str, Optional[BaseException]]:
    try:
        c = Canonical(raw)
    except (ValueError, TypeError) as err:
        return "", err
    return ContentHash(c), None


_scheme_re = re.compile(r"^[A-Za-z][A-Za-z0-9+.-]*://")


def NormalizeRemote(url: str) -> str:
    u = url.strip()
    loc = _scheme_re.match(u)
    if loc:
        u = u[loc.end() :]
    else:
        i = u.find(":")
        if i > 0 and "/" not in u[:i]:
            u = u[:i] + "/" + u[i + 1 :]
    end = u.find("/")
    if end < 0:
        end = len(u)
    authority = u[:end]
    at = authority.rfind("@")
    if at >= 0:
        u = u[at + 1 :]
        end -= at + 1
    u = u[:end].lower() + u[end:]
    u = u.rstrip("/")
    if u.endswith(".git"):
        u = u[: -len(".git")]
    return u.rstrip("/")


def _git(dir_path: str, *args: str) -> str:
    cmd = ["git", "-C", dir_path, *args]
    try:
        out = subprocess.run(
            cmd,
            check=True,
            capture_output=True,
            text=True,
        )
    except subprocess.CalledProcessError as err:
        stderr = (err.stderr or "").strip()
        raise RuntimeError(
            f"git {' '.join(args)}: {err}: {stderr}"
        ) from err
    return out.stdout.strip()


def RepoID(dir_path: str) -> Tuple[str, Optional[Exception]]:
    try:
        out = _git(dir_path, "remote")
    except RuntimeError as err:
        return "", err
    remotes = out.split()
    if remotes:
        remotes.sort()
        name = remotes[0]
        for r in remotes:
            if r == "origin":
                name = r
        try:
            u = _git(dir_path, "remote", "get-url", name)
        except RuntimeError as err:
            return "", err
        return NormalizeRemote(u), None
    try:
        out = _git(dir_path, "rev-list", "--max-parents=0", "HEAD")
    except RuntimeError as err:
        return "", err
    roots = out.split()
    if not roots:
        return "", ValueError("keys: repository has no remote and no commits")
    roots.sort()
    return "root:" + roots[0], None


def RepoPath(file: str) -> Tuple[str, str, bool, Optional[Exception]]:
    try:
        abs_path = os.path.abspath(file)
        dir_path = os.path.realpath(os.path.dirname(abs_path))
    except OSError as err:
        return "", "", False, err
    if not shutil.which("git"):
        return "", "", False, FileNotFoundError("git not found")
    try:
        top = _git(dir_path, "rev-parse", "--show-toplevel")
    except RuntimeError:
        return "", "", False, None
    try:
        top = os.path.realpath(top)
    except OSError as err:
        return "", "", False, err
    full = os.path.join(dir_path, os.path.basename(abs_path))
    try:
        full = os.path.realpath(full)
    except OSError:
        pass
    try:
        rel = os.path.relpath(full, top)
    except ValueError:
        return "", "", False, None
    if rel == ".." or rel.startswith(".." + os.sep):
        return "", "", False, None
    return top, rel.replace(os.sep, "/"), True, None


_kind_rules = [
    (re.compile(r"^docs/plans/[^/]+/DESIGN\.md$"), "design"),
    (re.compile(r"^docs/plans/[^/]+/briefs/[^/]+\.md$"), "brief"),
    (re.compile(r"^docs/plans/[^/]+/reports/[^/]+\.md$"), "report"),
]


def Kind(rel: str) -> str:
    rel = rel.replace("\\", "/")
    rel = os.path.normpath(rel).replace("\\", "/")
    if rel == ".":
        rel = ""
    if rel.startswith("./"):
        rel = rel[2:]
    for pattern, kind in _kind_rules:
        if pattern.match(rel):
            return kind
    return ""


# --- secrets ---


class Hit:
    def __init__(self, Pattern: str, Line: int) -> None:
        self.Pattern = Pattern
        self.Line = Line

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Hit):
            return NotImplemented
        return self.Pattern == other.Pattern and self.Line == other.Line

    def __repr__(self) -> str:
        return f"Hit(Pattern={self.Pattern!r}, Line={self.Line})"


def _placeholder(v: str, length_rule: bool) -> bool:
    if length_rule and len(v) < 8:
        return True
    for p in ("$", "<", "{", "`", "…", "...", "*"):
        if v.startswith(p):
            return True
    if _x_run.match(v) or v.lower().startswith("xxxx"):
        return True
    if v.lower() in ("password", "pass", "pwd", "secret", "changeme"):
        return True
    return False


def _secret_like(v: str) -> bool:
    return len(v) >= 16 and any(c in v for c in "0123456789")


_x_run = re.compile(r"^[xX*.\-_]{3,}$")

_patterns: List[Tuple[str, re.Pattern[str], int, Optional[Callable[[str], bool]]]] = [
    (
        "private_key_block",
        re.compile(
            r"-----BEGIN [A-Z ]*PRIVATE KEY-----(?:[\s\S]*?-----END [A-Z ]*PRIVATE KEY-----)?"
        ),
        0,
        None,
    ),
    ("sk_key", re.compile(r"\bsk-[A-Za-z0-9_\-]{16,}"), 0, None),
    ("github_token", re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}"), 0, None),
    ("github_pat", re.compile(r"\bgithub_pat_[A-Za-z0-9_]{20,}"), 0, None),
    ("aws_access_key", re.compile(r"\bAKIA[0-9A-Z]{16}\b"), 0, None),
    ("slack_token", re.compile(r"\bxox[abprs]-[A-Za-z0-9\-]{10,}"), 0, None),
    ("google_api_key", re.compile(r"\bAIza[0-9A-Za-z_\-]{35}"), 0, None),
    ("stripe_key", re.compile(r"\b[sr]k_live_[0-9A-Za-z]{16,}"), 0, None),
    ("workflow_api_token", re.compile(r"\bwk_[A-Za-z0-9_-]{32,}"), 0, None),
    (
        "jwt",
        re.compile(
            r"\beyJ[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{10,}"
        ),
        0,
        None,
    ),
    (
        "bearer_token",
        re.compile(r"(?i)\bbearer[ \t]+[A-Za-z0-9._~+/\-]{20,}=*"),
        0,
        None,
    ),
    (
        "connection_string",
        re.compile(r"\b[A-Za-z][A-Za-z0-9+.\-]*://[^\s:/@]+:([^\s@/]+)@[^\s/]+"),
        1,
        lambda v: not _placeholder(v, False),
    ),
    (
        "env_assignment",
        re.compile(
            r"(?m)(?:^|[ \t\"'`(])(?:export[ \t]+)?[A-Z0-9_]*(?:KEY|SECRET|TOKEN|PASSWORD)[ \t]*=[ \t]*[\"']?([^\s\"']+)"
        ),
        1,
        lambda v: not _placeholder(v, True),
    ),
    (
        "env_assignment",
        re.compile(
            r"(?mi)(?:^[ \t]*(?:-[ \t]+)?|[\"'])[A-Za-z0-9_\-]*(?:KEY|SECRET|TOKEN|PASSWORD)[\"']?[ \t]*:[ \t]*[\"']?([^\s\"',]+)"
        ),
        1,
        lambda v: not _placeholder(v, True) and _secret_like(v),
    ),
]


class _Match:
    __slots__ = ("name", "start", "end")

    def __init__(self, name: str, start: int, end: int) -> None:
        self.name = name
        self.start = start
        self.end = end


def _matches(text: str) -> List[_Match]:
    all_m: List[_Match] = []
    for name, pattern, group, ok in _patterns:
        for m in pattern.finditer(text):
            if ok is not None and group:
                v = m.group(group)
                if v is None or not ok(v):
                    continue
            all_m.append(_Match(name, m.start(), m.end()))
    all_m.sort(key=lambda x: (x.start, -(x.end - x.start)))
    out: List[_Match] = []
    for m in all_m:
        if out and m.start < out[-1].end:
            continue
        out.append(m)
    return out


def Scan(text: str) -> List[Hit]:
    hits: List[Hit] = []
    for m in _matches(text):
        line = 1 + text[: m.start].count("\n")
        hits.append(Hit(m.name, line))
    return hits


def Redact(text: str) -> str:
    parts: List[str] = []
    last = 0
    for m in _matches(text):
        parts.append(text[last : m.start])
        parts.append(f"[REDACTED:{m.name}]")
        last = m.end
    parts.append(text[last:])
    return "".join(parts)


def Patterns() -> List[str]:
    names: List[str] = []
    for name, _, _, _ in _patterns:
        if not names or names[-1] != name:
            names.append(name)
    return names


# --- facts ---


@dataclass
class File:
    Name: str = ""
    Data: bytes = b""


@dataclass
class Output:
    Name: str = ""
    Facts: List[bytes] = field(default_factory=list)
    Reasons: List[str] = field(default_factory=list)


@dataclass
class _Parsed:
    name: str
    payload: dict[str, Any]
    conv: str = ""
    harness: str = ""
    event: str = ""
    ts: Any = 0
    base: str = ""
    refs: List["_Ref"] = field(default_factory=list)
    reasons: List[str] = field(default_factory=list)
    bad: bool = True


@dataclass
class _Ref:
    key: str
    abs: str
    rel: str
    repo: str


@dataclass
class _ReadResult:
    content: str = ""
    raw: bytes = b""
    ok: bool = False


def _fact_json(v: dict[str, Any]) -> bytes:
    def _default(o: Any) -> Any:
        if isinstance(o, _Number):
            if any(c in o.s for c in ".eE"):
                return float(o.s)
            try:
                return int(o.s)
            except ValueError:
                return float(o.s)
        raise TypeError(type(o))

    return (
        json.dumps(v, ensure_ascii=False, sort_keys=True, default=_default).encode(
            "utf-8"
        )
    )


def Build(ctx: Any, files: List[File]) -> List[Output]:
    ps = [_parse_file(f) for f in files]
    reads: dict[str, _ReadResult] = {}
    last: dict[str, int] = {}
    for i, p in enumerate(ps):
        if p.bad:
            continue
        for abs_path in _write_paths(p):
            r = reads.get(abs_path)
            if r is None:
                r = _read_file(abs_path)
                reads[abs_path] = r
            if not r.ok:
                continue
            top, rel, in_repo, err = RepoPath(abs_path)
            if err is not None or not in_repo or Kind(rel) == "":
                continue
            repo_id, err = RepoID(top)
            if err is not None:
                continue
            k = p.conv + "\x00" + repo_id + "\x00" + rel
            p.refs.append(_Ref(key=k, abs=abs_path, rel=rel, repo=repo_id))
            last[k] = i
    out: List[Output] = []
    commits: dict[str, bool] = {}
    for i, p in enumerate(ps):
        o = Output(Name=p.name)
        if p.bad:
            o.Reasons = list(p.reasons)
            out.append(o)
            continue

        def add(v: dict[str, Any]) -> None:
            v["id"] = f"{p.name}#{len(o.Facts)}"
            o.Facts.append(_fact_json(v))

        def common(typ: str) -> dict[str, Any]:
            return {
                "type": typ,
                "conversation_id": p.conv,
                "harness": p.harness,
                "event": p.event,
                "ts": p.ts,
            }

        hv = common("hook_event")
        hv["payload"] = _redact_payload(p.payload)
        add(hv)
        seen: dict[str, bool] = {}
        for r in p.refs:
            if last[r.key] != i or seen.get(r.key):
                continue
            seen[r.key] = True
            rd = reads[r.abs]
            hits = Scan(rd.content)
            if hits:
                o.Reasons.append(
                    f"secret: {hits[0].Pattern} at line {hits[0].Line} in {r.rel}"
                )
                continue
            v = common("artifact_version")
            v["repo_id"] = r.repo
            v["path"] = r.rel
            v["content_hash"] = ContentHash(rd.raw)
            v["content"] = rd.content
            v["source"] = "worktree"
            add(v)
        _build_commits(ctx, p, commits, common, add, o)
        out.append(o)
    return out


def _parse_file(f: File) -> _Parsed:
    p = _Parsed(name=f.Name, payload={})
    if not f.Data:
        p.reasons = ["unparseable: envelope is not JSON"]
        return p
    line, rest = f.Data.split(b"\n", 1) if b"\n" in f.Data else (f.Data, b"")
    try:
        env = json.loads(
            line.decode("utf-8"),
            parse_float=lambda s: _Number(s),
        )
    except (json.JSONDecodeError, UnicodeDecodeError):
        p.reasons = ["unparseable: envelope is not JSON"]
        return p
    if not isinstance(env, dict):
        p.reasons = ["unparseable: envelope is not JSON"]
        return p
    try:
        payload = json.loads(
            rest.decode("utf-8"),
            parse_float=lambda s: _Number(s),
        )
    except (json.JSONDecodeError, UnicodeDecodeError):
        p.reasons = ["unparseable: payload is not JSON"]
        return p
    if not isinstance(payload, dict):
        p.reasons = ["unparseable: payload is not an object"]
        return p
    p.payload = payload
    p.harness = env.get("harness", "")
    p.ts = env.get("ts", 0)
    if p.ts == "":
        p.ts = 0
    for key in ("session_id", "conversation_id", "sessionID"):
        s = payload.get(key)
        if isinstance(s, str) and s:
            p.conv = s
            break
    if not p.conv:
        p.reasons = ["invalid: no conversation id"]
        return p
    p.event = env.get("event", "")
    if not p.event:
        hen = payload.get("hook_event_name")
        if isinstance(hen, str):
            p.event = hen
    cwd = payload.get("cwd")
    if isinstance(cwd, str) and cwd:
        p.base = cwd
    else:
        roots = payload.get("workspace_roots")
        if isinstance(roots, list) and roots:
            first = roots[0]
            if isinstance(first, str):
                p.base = first
    p.bad = False
    return p


def _redact_payload(v: Any) -> Any:
    if isinstance(v, str):
        return Redact(v)
    if isinstance(v, dict):
        return {k: _redact_payload(e) for k, e in v.items()}
    if isinstance(v, list):
        return [_redact_payload(e) for e in v]
    return v


def _read_file(abs_path: str) -> _ReadResult:
    try:
        with open(abs_path, "rb") as rf:
            b = rf.read()
    except OSError:
        return _ReadResult()
    try:
        text = b.decode("utf-8")
    except UnicodeDecodeError:
        return _ReadResult()
    return _ReadResult(content=text, raw=b, ok=True)


_write_tools = {
    "write": True,
    "edit": True,
    "multiedit": True,
    "write_file": True,
    "edit_file": True,
    "create_file": True,
    "str_replace_editor": True,
    "apply_patch": True,
    "applypatch": True,
}

_patch_re = re.compile(r"(?m)^\*\*\* (?:Add File|Update File|Move to): (.+)$")

_expected_event = {
    "claude": "PostToolUse",
    "codex": "PostToolUse",
    "cursor": "postToolUse",
    "opencode": "tool.execute.after",
}


def _write_paths(p: _Parsed) -> List[str]:
    raw: List[str] = []
    payload = p.payload
    event = p.event
    hen = payload.get("hook_event_name")
    if isinstance(hen, str) and hen:
        event = hen
    else:
        ev = payload.get("event")
        if isinstance(ev, str) and ev:
            event = ev
    if p.harness == "cursor" and event == "afterFileEdit":
        fp = payload.get("file_path")
        if isinstance(fp, str):
            raw = [fp]
    else:
        exp = _expected_event.get(p.harness, "")
        if event != exp or payload.get("source") == "bus":
            return []
        tn = payload.get("tool_name", "")
        if not isinstance(tn, str):
            tn = ""
        name = tn[tn.rfind(".") + 1 :].lower()
        if not _write_tools.get(name):
            return []
        is_patch = name in ("apply_patch", "applypatch")
        args: dict[str, Any] = {}
        ti = payload.get("tool_input")
        if isinstance(ti, dict):
            args = ti
        elif isinstance(ti, str):
            if ti:
                try:
                    v = json.loads(ti, parse_float=lambda s: _Number(s))
                except json.JSONDecodeError:
                    if is_patch:
                        args = {"patch": ti}
                    else:
                        return []
                else:
                    if not isinstance(v, dict):
                        return []
                    args = v
        elif ti is not None:
            return []
        for k in ("file_path", "path", "filePath", "target_file"):
            s = args.get(k)
            if isinstance(s, str):
                raw.append(s)
        edits = args.get("edits")
        if isinstance(edits, list):
            for e in edits:
                if isinstance(e, dict):
                    for k in ("file_path", "path", "filePath"):
                        s = e.get(k)
                        if isinstance(s, str):
                            raw.append(s)
        if is_patch:
            patch = args.get("patch", "")
            if not isinstance(patch, str) or not patch:
                patch = args.get("input", "")
            if isinstance(patch, str):
                for m in _patch_re.finditer(patch):
                    raw.append(m.group(1))
    out: List[str] = []
    seen: dict[str, bool] = {}
    for r in raw:
        abs_path = r
        if not os.path.isabs(r):
            if not p.base:
                continue
            abs_path = os.path.join(p.base, r)
        abs_path = os.path.normpath(abs_path)
        if not seen.get(abs_path):
            seen[abs_path] = True
            out.append(abs_path)
    return out


_git_commit_re = re.compile(
    r"(?:^|[\s;&|(])git((?:\s+(?:-C\s+(?:\"[^\"]*\"|'[^']*'|\S+)|-c\s+\S+|--[\w-]+(?:=\S+)?))*)\s+commit(?:[\s;&|)]|$)"
)
_dir_re = re.compile(r'-C\s+("[^"]*"|\'[^\']*\'|\S+)')
_sha_re = re.compile(r"(?m)^\[(?:[^\]]*\s)?([0-9a-f]{7,40})\]")
_post_events = {
    "PostToolUse": True,
    "postToolUse": True,
    "afterShellExecution": True,
    "tool.execute.after": True,
}


def _as_object(v: Any) -> Optional[dict[str, Any]]:
    if isinstance(v, dict):
        return v
    if isinstance(v, str):
        try:
            m = json.loads(v, parse_float=lambda s: _Number(s))
        except json.JSONDecodeError:
            return None
        if isinstance(m, dict):
            return m
    return None


def _command_text(payload: dict[str, Any]) -> str:
    c: Any = None
    ti = _as_object(payload.get("tool_input"))
    if ti is not None:
        c = ti.get("command")
    if c is None:
        c = payload.get("command")
    if isinstance(c, str):
        return c
    if isinstance(c, list):
        parts = [e for e in c if isinstance(e, str)]
        return " ".join(parts)
    return ""


def _non_zero(v: Any) -> bool:
    if isinstance(v, _Number):
        try:
            return float(v.s) != 0
        except ValueError:
            return False
    if isinstance(v, (int, float)):
        return v != 0
    return False


def _output_and_failed(payload: dict[str, Any]) -> tuple[str, bool]:
    failed = _non_zero(payload.get("exit_code")) or _non_zero(payload.get("exitCode"))
    texts: List[str] = []
    for k in ("tool_response", "tool_output", "output"):
        v = payload.get(k)
        if isinstance(v, str):
            m = _as_object(v)
            if m is not None:
                v = m
            else:
                texts.append(v)
                continue
        if isinstance(v, dict):
            failed = failed or _non_zero(v.get("exit_code")) or _non_zero(
                v.get("exitCode")
            )
            for f in ("stdout", "output", "stderr"):
                s = v.get(f)
                if isinstance(s, str):
                    texts.append(s)
    return "\n".join(texts), failed


def _unquote(s: str) -> str:
    if len(s) >= 2 and s[0] in ('"', "'") and s[-1] == s[0]:
        return s[1:-1]
    return s


def _facts_git(ctx: Any, dir_path: str, *args: str) -> bytes:
    cmd = ["git", "-C", dir_path, *args]
    env = {**os.environ, "GIT_TERMINAL_PROMPT": "0"}
    try:
        out = subprocess.run(
            cmd,
            check=True,
            capture_output=True,
            timeout=10,
            env=env,
        )
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
        raise OSError("git failed")
    return out.stdout


def _build_commits(
    ctx: Any,
    p: _Parsed,
    done: dict[str, bool],
    common: Callable[[str], dict[str, Any]],
    add: Callable[[dict[str, Any]], None],
    o: Output,
) -> None:
    event = p.payload.get("hook_event_name", "")
    if not isinstance(event, str) or not event:
        event = p.event
    if not _post_events.get(event):
        return
    cmd_text = _command_text(p.payload)
    matches = list(_git_commit_re.finditer(cmd_text))
    if not matches:
        return
    text, failed = _output_and_failed(p.payload)
    if failed:
        return
    sm = _sha_re.search(text)
    if not sm:
        return
    for m in matches:
        dir_path = p.base
        for d in _dir_re.finditer(m.group(1)):
            c = _unquote(d.group(1))
            if os.path.isabs(c):
                dir_path = c
            elif dir_path:
                dir_path = os.path.join(dir_path, c)
            else:
                dir_path = ""
        if not dir_path:
            continue
        try:
            b = _facts_git(ctx, dir_path, "rev-parse", "--verify", sm.group(1) + "^{commit}")
        except OSError:
            continue
        sha = b.decode().strip()
        repo_id, err = RepoID(dir_path)
        if err is not None:
            continue
        dk = p.conv + "\x00" + repo_id + "\x00" + sha
        if done.get(dk):
            return
        try:
            b = _facts_git(
                ctx,
                dir_path,
                "diff-tree",
                "-M",
                "--name-status",
                "-r",
                "--root",
                "--no-commit-id",
                "-z",
                sha,
            )
        except OSError:
            continue
        done[dk] = True
        paths: List[str] = []
        renames: List[dict[str, str]] = []
        catchup: List[str] = []
        toks = b.decode("latin-1").split("\x00")
        i = 0
        while i < len(toks):
            st = toks[i]
            if not st:
                i += 1
                continue
            if st[0] in ("R", "C"):
                if i + 2 >= len(toks):
                    break
                from_p, to_p = toks[i + 1], toks[i + 2]
                i += 3
                paths.append(to_p)
                if st[0] == "R":
                    renames.append({"from": from_p, "to": to_p})
                    catchup.append(to_p)
            else:
                if i + 1 >= len(toks):
                    break
                path = toks[i + 1]
                i += 2
                paths.append(path)
                if st[0] in ("A", "M", "T"):
                    catchup.append(path)
        c = common("commit")
        c["repo_id"] = repo_id
        c["sha"] = sha
        c["paths"] = paths
        c["renames"] = renames
        add(c)
        for path in catchup:
            if Kind(path) == "":
                continue
            try:
                blob = _facts_git(ctx, dir_path, "show", f"{sha}:{path}")
            except OSError:
                continue
            try:
                blob_text = blob.decode("utf-8")
            except UnicodeDecodeError:
                continue
            hits = Scan(blob_text)
            if hits:
                o.Reasons.append(
                    f"secret: {hits[0].Pattern} at line {hits[0].Line} in {path}"
                )
                continue
            v = common("artifact_version")
            v["repo_id"] = repo_id
            v["path"] = path
            v["content_hash"] = ContentHash(blob)
            v["content"] = blob_text
            v["source"] = "commit"
            v["sha"] = sha
            add(v)
        return


def WritePaths(raw: Optional[bytes]) -> Optional[List[str]]:
    if raw is None:
        return None
    p = _parse_file(File(Data=raw))
    if p.bad:
        return None
    paths = _write_paths(p)
    if not paths:
        return None
    return paths


# --- drain ---

ReasonIdle = "idle"
ReasonLockHeld = "lock held by another drain"
ReasonGaveUp = "backoff at cap and no new file"
ReasonStopped = "stopped"

_MAX_DRAIN_FILES = 500
_MAX_DRAIN_BYTES = 8 << 20


class _NetErr(Exception):
    pass


_ERR_NETWORK: BaseException = _NetErr()


class _DiscardIO:
    def write(self, s: str) -> int:
        return len(s)

    def flush(self) -> None:
        pass


_DISCARD_IO = _DiscardIO()


@dataclass
class DrainResponse:
    Status: int = 0
    RetryAfter: float = 0.0
    Results: List[dict[str, Any]] = field(default_factory=list)


class HTTPSink:
    def __init__(
        self,
        Endpoint: str = "",
        Key: str = "",
        Client: Any = None,
    ) -> None:
        self.Endpoint = Endpoint
        self.Key = Key
        self.Client = Client

    def Send(
        self, ctx: "DrainContext", facts: List[bytes]
    ) -> Tuple[DrainResponse, Optional[BaseException]]:
        parsed = [json.loads(f) for f in facts]
        body = json.dumps({"facts": parsed}).encode("utf-8")
        url = self.Endpoint.rstrip("/") + "/v1/ingest"
        req = urllib.request.Request(url, data=body, method="POST")
        req.add_header("Content-Type", "application/json")
        if self.Key:
            req.add_header("Authorization", "Bearer " + self.Key)
        timeout = 30.0
        if self.Client is not None and hasattr(self.Client, "timeout"):
            timeout = self.Client.timeout
        try:
            try:
                resp = urllib.request.urlopen(req, timeout=timeout)
                status = resp.status
                headers = resp.headers
                data = resp.read(64 << 20)
            except urllib.error.HTTPError as e:
                status = e.code
                headers = e.headers
                data = e.read(64 << 20)
        except (urllib.error.URLError, OSError):
            return DrainResponse(), _ERR_NETWORK
        out = DrainResponse(Status=status)
        ra = headers.get("Retry-After", "").strip()
        if ra.isdigit():
            out.RetryAfter = float(ra)
        if status == 200:
            try:
                r = json.loads(data)
                out.Results = r.get("results", [])
            except (json.JSONDecodeError, TypeError):
                out.Status = 502
        return out, None


def ConfigSink() -> Tuple[Optional[HTTPSink], Optional[BaseException]]:
    try:
        c = Load()
    except (ErrPartialEnv, OSError, ValueError) as err:
        return None, err
    return HTTPSink(Endpoint=c.Endpoint, Key=c.Key), None


@dataclass
class Options:
    Dir: str = ""
    Sink: Optional[Callable[[], Tuple[Any, Optional[BaseException]]]] = None
    Window: float = 0.0
    Linger: float = 0.0
    BackoffMax: float = 0.0
    BackoffMin: float = 0.0
    GiveUp: float = 0.0
    Poll: float = 0.0
    LockWait: float = 0.0
    Wake: Any = None
    Hosted: bool = False
    Log: Any = None
    afterRelease: Optional[Callable[[], None]] = None

    def defaults(self) -> None:
        if not self.Dir:
            self.Dir = QueueDir()
        if self.Window <= 0:
            self.Window = 1.5
        if self.Linger <= 0:
            self.Linger = 60.0
        if self.BackoffMax <= 0:
            self.BackoffMax = 300.0
        if self.BackoffMin <= 0:
            self.BackoffMin = 0.5
        if self.GiveUp <= 0:
            self.GiveUp = 900.0
        if self.Poll <= 0:
            self.Poll = 0.25
        if self.LockWait <= 0:
            self.LockWait = 1.0
        if self.BackoffMin > self.BackoffMax:
            self.BackoffMin = self.BackoffMax
        if self.Log is None:
            self.Log = _DISCARD_IO


class DrainContext:
    def __init__(
        self,
        deadline: Optional[float] = None,
        cancelled: bool = False,
    ) -> None:
        self._deadline = deadline
        self._cancelled = cancelled

    @classmethod
    def with_timeout(cls, seconds: float) -> "DrainContext":
        return cls(deadline=time.monotonic() + seconds)

    def cancel(self) -> None:
        self._cancelled = True

    def cancelled(self) -> bool:
        if self._cancelled:
            return True
        if self._deadline is not None and time.monotonic() > self._deadline:
            return True
        return False

    def err(self) -> Optional[BaseException]:
        if self.cancelled():
            return InterruptedError()
        return None


def QueueDir() -> str:
    d = os.environ.get("YAKKA_QUEUE", "")
    if d:
        return d
    home = os.environ.get("HOME", "") or os.path.expanduser("~")
    return os.path.join(home, ".local", "share", "yakka", "queue")


def EnsureDirs(dir_path: str) -> Optional[OSError]:
    for d in (
        dir_path,
        os.path.join(dir_path, "tmp"),
        os.path.join(dir_path, "rejected"),
    ):
        try:
            os.makedirs(d, mode=0o700, exist_ok=True)
        except OSError as err:
            return err
    return None


def _lock_path(dir_path: str) -> str:
    return os.path.join(dir_path, ".drain.lock")


def _try_lock(dir_path: str) -> Tuple[Optional[Any], Optional[BaseException]]:
    path = _lock_path(dir_path)
    try:
        f = open(path, "a+b")
    except OSError as err:
        return None, err
    try:
        fcntl.flock(f.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError as err:
        f.close()
        return None, err
    return f, None


def _release_lock(f: Any) -> None:
    if f is not None:
        try:
            fcntl.flock(f.fileno(), fcntl.LOCK_UN)
        except OSError:
            pass
        try:
            f.close()
        except OSError:
            pass


def _acquire(
    ctx: DrainContext,
    dir_path: str,
    wait: float,
    poll: float,
    forever: bool,
) -> Tuple[Optional[Any], Optional[BaseException]]:
    deadline = time.monotonic() + wait
    step = poll if forever else 0.02
    while True:
        f, err = _try_lock(dir_path)
        if f is not None:
            return f, None
        if err is not None and not isinstance(err, BlockingIOError):
            return None, err
        if not forever and time.monotonic() > deadline:
            return None, BlockingIOError()
        if not _drain_sleep(ctx, step):
            return None, InterruptedError()
        if ctx.cancelled():
            return None, InterruptedError()


def Running(dir_path: str) -> bool:
    path = _lock_path(dir_path)
    try:
        f = open(path, "r+b")
    except OSError:
        return False
    try:
        fcntl.flock(f.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        return True
    try:
        fcntl.flock(f.fileno(), fcntl.LOCK_UN)
    except OSError:
        pass
    f.close()
    return False


def _drain_sleep(ctx: DrainContext, duration: float) -> bool:
    if duration <= 0:
        return not ctx.cancelled()
    end = time.monotonic() + duration
    while time.monotonic() < end:
        if ctx.cancelled():
            return False
        time.sleep(min(0.02, end - time.monotonic()))
    return True


@dataclass
class _QueueEntry:
    name: str
    mod: float


def _list_queue(dir_path: str) -> List[_QueueEntry]:
    try:
        names = os.listdir(dir_path)
    except OSError:
        return []
    out: List[_QueueEntry] = []
    for n in names:
        if n.startswith(".") or not n.endswith(".evt"):
            continue
        p = os.path.join(dir_path, n)
        if not os.path.isfile(p):
            continue
        out.append(_QueueEntry(n, os.path.getmtime(p)))
    out.sort(key=lambda e: (e.mod, e.name))
    return out


@dataclass
class QueueStatusData:
    Dir: str
    Queued: int
    OldestAge: float
    Rejected: int
    Running: bool


def QueueStatus(dir_path: str) -> QueueStatusData:
    st = QueueStatusData(
        Dir=dir_path,
        Queued=0,
        OldestAge=-1.0,
        Rejected=0,
        Running=Running(dir_path),
    )
    es = _list_queue(dir_path)
    st.Queued = len(es)
    if es:
        st.OldestAge = time.time() - es[0].mod
    rej = os.path.join(dir_path, "rejected")
    try:
        for n in os.listdir(rej):
            if n.endswith(".evt"):
                st.Rejected += 1
    except OSError:
        pass
    return st


class _Runner:
    def __init__(self, o: Options) -> None:
        self.o = o
        self.seen: dict[str, bool] = {}
        self.last_new = time.monotonic()

    def logf(self, fmt: str, *args: Any) -> None:
        self.o.Log.write("drain: " + (fmt % args) + "\n")
        self.o.Log.flush()

    def scan(self) -> List[_QueueEntry]:
        es = _list_queue(self.o.Dir)
        cur = {e.name: True for e in es}
        now = time.monotonic()
        for e in es:
            if not self.seen.get(e.name):
                self.last_new = now
        self.seen = cur
        return es

    def wait_for_work(self, ctx: DrainContext) -> bool:
        linger_end = None
        if not self.o.Hosted:
            linger_end = time.monotonic() + self.o.Linger
        while True:
            if ctx.cancelled():
                return False
            if linger_end is not None and time.monotonic() >= linger_end:
                return False
            if self.o.Wake is not None:
                try:
                    self.o.Wake.acquire(block=False)
                except Exception:
                    pass
            if len(self.scan()) > 0:
                return True
            if not _drain_sleep(ctx, self.o.Poll):
                return False


def Run(ctx: DrainContext, o: Options) -> Tuple[str, Optional[BaseException]]:
    o.defaults()
    if o.Sink is None:
        return "", OSError("drain: no sink")
    err = EnsureDirs(o.Dir)
    if err is not None:
        return "", err
    r = _Runner(o)
    lock, err = _acquire(ctx, o.Dir, o.LockWait, o.Poll, o.Hosted)
    if err is not None:
        if ctx.cancelled():
            return ReasonStopped, None
        if isinstance(err, BlockingIOError):
            return ReasonLockHeld, None
        return "", err
    r.logf("acquired lock pid=%d", os.getpid())
    fresh = True
    backoff = 0.0
    try:
        while True:
            if ctx.cancelled():
                return ReasonStopped, None
            files = r.scan()
            if not files:
                fresh = True
                backoff = 0.0
                if not r.wait_for_work(ctx):
                    if ctx.cancelled():
                        return ReasonStopped, None
                    _release_lock(lock)
                    lock = None
                    if o.afterRelease is not None:
                        o.afterRelease()
                    if len(r.scan()) == 0:
                        return ReasonIdle, None
                    lock, err = _acquire(ctx, o.Dir, o.LockWait, o.Poll, False)
                    if err is not None:
                        if ctx.cancelled():
                            return ReasonStopped, None
                        return ReasonLockHeld, None
                    r.logf("acquired lock pid=%d", os.getpid())
                continue
            if fresh:
                fresh = False
                if not _drain_sleep(ctx, o.Window):
                    return ReasonStopped, None
                files = r.scan()
            sink, err = o.Sink()
            if err is not None:
                r.logf("config unavailable; retrying")
                if not o.Hosted and (time.monotonic() - r.last_new) >= o.GiveUp:
                    return ReasonGaveUp, None
                if not _drain_sleep(ctx, max(o.Poll, 1.0)):
                    return ReasonStopped, None
                continue
            if len(files) > _MAX_DRAIN_FILES:
                files = files[:_MAX_DRAIN_FILES]
            res = r.batch(ctx, sink, files)
            if not res[0]:
                backoff = 0.0
                continue
            wait = res[1]
            if wait <= 0:
                if backoff == 0:
                    backoff = o.BackoffMin
                else:
                    backoff = min(backoff * 2, o.BackoffMax)
                wait = backoff / 2 + random.random() * (backoff / 2)
            r.scan()
            if (
                not o.Hosted
                and backoff >= o.BackoffMax
                and (time.monotonic() - r.last_new) >= o.GiveUp
            ):
                return ReasonGaveUp, None
            if not _drain_sleep(ctx, wait):
                return ReasonStopped, None
    finally:
        _release_lock(lock)


@dataclass
class _BatchItem:
    name: str
    facts: List[bytes]
    reasons: List[str]


def _prefix(name: str, reasons: List[str]) -> List[str]:
    return [name + ": " + s for s in reasons]


class _RunnerBatch(_Runner):
    def batch(
        self, ctx: DrainContext, sink: HTTPSink, files: List[_QueueEntry]
    ) -> Tuple[bool, float]:
        in_files: List[File] = []
        for e in files:
            path = os.path.join(self.o.Dir, e.name)
            try:
                with open(path, "rb") as f:
                    data = f.read()
            except OSError:
                continue
            in_files.append(File(Name=e.name, Data=data))
        items: List[_BatchItem] = []
        for out in Build(None, in_files):
            if not out.Facts:
                if out.Reasons:
                    self.reject(out.Name, _prefix(out.Name, out.Reasons))
                else:
                    self.remove(out.Name)
                continue
            items.append(_BatchItem(out.Name, list(out.Facts), list(out.Reasons)))
        while items:
            n, size = 0, 0
            while n < len(items):
                s = sum(len(f) for f in items[n].facts)
                if n > 0 and size + s > _MAX_DRAIN_BYTES:
                    break
                size += s
                n += 1
            retry, wait = self.send(ctx, sink, items[:n])
            if retry:
                return True, wait
            items = items[n:]
        return False, 0.0

    def send(
        self, ctx: DrainContext, sink: HTTPSink, items: List[_BatchItem]
    ) -> Tuple[bool, float]:
        all_facts: List[bytes] = []
        for it in items:
            all_facts.extend(it.facts)
        resp, err = sink.Send(ctx, all_facts)
        if err is not None:
            if not ctx.cancelled():
                self.logf(
                    "attempt failed: network error (%d files kept)", len(items)
                )
            return True, 0.0
        if resp.Status == 200:
            return self.apply(items, all_facts, resp)
        if resp.Status == 429:
            wait = max(resp.RetryAfter, 0.001)
            self.logf(
                "attempt failed: status=429 retry-after=%s (%d files kept)",
                wait,
                len(items),
            )
            return True, wait
        if resp.Status in (400, 413):
            if len(items) == 1:
                self.logf("file rejected: status=%d", resp.Status)
                it = items[0]
                self.reject(
                    it.name,
                    _prefix(
                        it.name,
                        [str(resp.Status)] + list(it.reasons),
                    ),
                )
                return False, 0.0
            self.logf("status=%d: splitting %d files", resp.Status, len(items))
            h = len(items) // 2
            retry, wait = self.send(ctx, sink, items[:h])
            if retry:
                return True, wait
            return self.send(ctx, sink, items[h:])
        self.logf(
            "attempt failed: status=%d (%d files kept)", resp.Status, len(items)
        )
        return True, 0.0

    def apply(
        self,
        items: List[_BatchItem],
        all_facts: List[bytes],
        resp: DrainResponse,
    ) -> Tuple[bool, float]:
        if len(resp.Results) != len(all_facts):
            self.logf(
                "attempt failed: %d results for %d facts (%d files kept)",
                len(resp.Results),
                len(all_facts),
                len(items),
            )
            return True, 0.0
        for res in resp.Results:
            st = res.get("status", "")
            if st not in ("accepted", "duplicate", "rejected"):
                self.logf(
                    "attempt failed: unknown result status (%d files kept)",
                    len(items),
                )
                return True, 0.0
        i = 0
        for it in items:
            rej: List[str] = []
            for _ in it.facts:
                res = resp.Results[i]
                i += 1
                if res.get("status") == "rejected":
                    reason = res.get("reason") or "rejected"
                    rej.append(res.get("id", "") + ": " + reason)
            rej.extend(_prefix(it.name, it.reasons))
            if rej:
                self.reject(it.name, rej)
            else:
                self.remove(it.name)
        return False, 0.0

    def remove(self, name: str) -> None:
        path = os.path.join(self.o.Dir, name)
        try:
            os.remove(path)
        except FileNotFoundError:
            pass
        except OSError as err:
            self.logf("delete failed: %s", err)

    def reject(self, name: str, reasons: List[str]) -> None:
        dst = os.path.join(self.o.Dir, "rejected", name)
        lines = []
        for s in reasons:
            lines.append(s.replace("\r", " ").replace("\n", " ") + "\n")
        reason_path = dst + ".reason"
        try:
            with open(reason_path, "w", encoding="utf-8") as f:
                f.writelines(lines)
        except OSError as err:
            self.logf("reason write failed: %s", err)
        src = os.path.join(self.o.Dir, name)
        try:
            os.rename(src, dst)
        except FileNotFoundError:
            pass
        except OSError as err:
            self.logf("reject move failed: %s", err)


_Runner.batch = _RunnerBatch.batch  # type: ignore[method-assign]
_Runner.send = _RunnerBatch.send  # type: ignore[method-assign]
_Runner.apply = _RunnerBatch.apply  # type: ignore[method-assign]
_Runner.remove = _RunnerBatch.remove  # type: ignore[method-assign]
_Runner.reject = _RunnerBatch.reject  # type: ignore[method-assign]


def _parse_go_duration(s: str) -> float:
    import re

    units = {
        "ns": 1e-9,
        "us": 1e-6,
        "µs": 1e-6,
        "ms": 1e-3,
        "s": 1.0,
        "m": 60.0,
        "h": 3600.0,
    }
    pos = 0
    total = 0.0
    while pos < len(s):
        m = re.match(r"([0-9]+(?:\.[0-9]*)?)(ns|us|µs|ms|s|m|h)", s[pos:])
        if not m:
            raise ValueError(f"invalid duration {s!r}")
        total += float(m.group(1)) * units[m.group(2)]
        pos += m.end()
    if pos != len(s):
        raise ValueError(f"invalid duration {s!r}")
    return total


def RunStandalone(ctx: DrainContext, stderr: Any) -> int:
    try:
        Load()
    except ErrPartialEnv as err:
        print("yakka drain:", err, file=stderr)
        return 1
    o = Options(Sink=ConfigSink, Log=stderr, Poll=0.25)
    for env, attr in (
        ("YAKKA_DRAIN_WINDOW", "Window"),
        ("YAKKA_DRAIN_LINGER", "Linger"),
        ("YAKKA_DRAIN_BACKOFF_MAX", "BackoffMax"),
        ("YAKKA_DRAIN_GIVEUP", "GiveUp"),
    ):
        v = os.environ.get(env, "")
        if v:
            try:
                setattr(o, attr, _parse_go_duration(v))
            except ValueError as err:
                print(f"yakka drain: {env}: {err}", file=stderr)
                return 2
    o.defaults()
    if o.BackoffMax > 0 and o.BackoffMax < 0.5:
        o.BackoffMin = o.BackoffMax
    reason, err = Run(ctx, o)
    if err is not None:
        print("yakka drain:", err, file=stderr)
        return 1
    print(f"drain: exit: {reason}", file=stderr)
    return 0


# --- command dispatch ---


def cmd_drain(argv: List[str]) -> int:
    ctx = DrainContext()
    return RunStandalone(ctx, sys.stderr)


def main(argv: List[str]) -> int:
    if len(argv) < 2:
        print("yakka: unknown command", file=sys.stderr)
        return 2
    cmd = argv[1]
    if cmd == "drain":
        return cmd_drain(argv)
    print("yakka: unknown command", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
