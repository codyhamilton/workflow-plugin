#!/usr/bin/env python3
"""Load Jev check definitions into the running service (PUT /v1/checks). Usage: load_checks.py checks/acceptance-provenance.json [base-url]"""
import json, os, sys, urllib.request

base = sys.argv[2] if len(sys.argv) > 2 else os.environ.get("WORKFLOW_QUALITY_URL", "http://127.0.0.1:8765")
req = urllib.request.Request(base + "/v1/checks", open(sys.argv[1], "rb").read(), method="PUT", headers={"Content-Type": "application/json"})
if os.environ.get("WORKFLOW_QUALITY_TOKEN"):
    req.add_header("Authorization", "Bearer " + os.environ["WORKFLOW_QUALITY_TOKEN"])
print(json.dumps(json.load(urllib.request.urlopen(req)), indent=1))
