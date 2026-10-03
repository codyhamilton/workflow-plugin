#!/bin/sh
# Install and start the quality service as a systemd user unit (survives logout/reboot when lingering is on).
set -e
repo=$(cd "$(dirname "$0")/../.." && pwd)
mkdir -p ~/.config/systemd/user
sed "s#%REPO%#$repo#" "$repo/tools/quality/workflow-quality.service" > ~/.config/systemd/user/workflow-quality.service
systemctl --user daemon-reload
systemctl --user enable --now workflow-quality.service
sleep 1
curl -s -m 3 http://127.0.0.1:8765/v1/checks >/dev/null && echo "workflow-quality up on 127.0.0.1:8765" || { echo "service not answering"; exit 1; }
