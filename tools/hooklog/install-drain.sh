#!/bin/sh
# Install the hooklog drain as a systemd user timer (runs drain.py --once every 15 s; the spool just grows while the service is down).
set -e
repo=$(cd "$(dirname "$0")/../.." && pwd)
mkdir -p ~/.config/systemd/user
sed "s#%REPO%#$repo#" "$repo/tools/hooklog/workflow-hooklog-drain.service" > ~/.config/systemd/user/workflow-hooklog-drain.service
cp "$repo/tools/hooklog/workflow-hooklog-drain.timer" ~/.config/systemd/user/
systemctl --user daemon-reload
systemctl --user enable --now workflow-hooklog-drain.timer
echo "workflow-hooklog-drain.timer enabled"
