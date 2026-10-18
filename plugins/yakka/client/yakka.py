#!/usr/bin/env python3
"""Yakka plugin client: config, keys, secrets, and command dispatch (stdlib only)."""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from typing import Any, Callable, List, Optional, Tuple

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


# --- command dispatch ---


def cmd_drain(argv: List[str]) -> int:
    print("yakka drain: not implemented", file=sys.stderr)
    return 2


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
