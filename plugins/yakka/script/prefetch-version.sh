#!/usr/bin/env bash
plugin=$(cd "$(dirname "$0")/.." && pwd -P) || exit 0
nohup bash "$plugin/bin/yakka" --version </dev/null >/dev/null 2>&1 & exit 0
