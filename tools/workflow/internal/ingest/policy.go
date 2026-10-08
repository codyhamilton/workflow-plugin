package ingest

import (
	"bytes"
	"encoding/json"

	"github.com/codyhamilton/workflow-plugin/tools/workflow/internal/keys"
)

// Action is what ingest does with a received hook_event fact (DESIGN "Capture and event policy").
type Action int

const (
	// Keep stores the slim envelope; the row hash is the full received envelope's.
	Keep Action = iota
	// Collapse stores one row per message part; the row hash is CollapseHash.
	Collapse
	// Remove stores nothing: no fact row and no archive line.
	Remove
)

func (a Action) String() string {
	switch a {
	case Collapse:
		return "collapse"
	case Remove:
		return "remove"
	}
	return "keep"
}

type policyKey struct{ harness, event string }

// policyTable maps (harness, event) to an action. Any pair not listed is Keep. The OpenCode Remove
// entries must equal the plugin's remove-list in packages/opencode-workflow-hooks/src/index.ts
// (asserted by TestRemoveListMatchesPlugin).
var policyTable = map[policyKey]Action{
	{"opencode", "experimental.chat.system.transform"}: Remove,
	{"opencode", "chat.params"}:                        Remove,
	{"opencode", "chat.headers"}:                       Remove,
	{"opencode", "shell.env"}:                          Remove,
	{"opencode", "message.part.delta"}:                 Collapse,
}

// Policy returns the action for a hook_event fact. A Collapse event lacking a non-empty string
// messageID, partID or field in payload.event.properties is Keep.
func Policy(harness, event string, payload map[string]any) Action {
	a := policyTable[policyKey{harness, event}]
	if a == Collapse {
		if _, ok := collapseKey(payload); !ok {
			return Keep
		}
	}
	return a
}

// collapseKey returns [messageID, partID, field] from payload.event.properties.
func collapseKey(payload map[string]any) ([3]string, bool) {
	var k [3]string
	ev, _ := payload["event"].(map[string]any)
	props, _ := ev["properties"].(map[string]any)
	for i, name := range []string{"messageID", "partID", "field"} {
		s, ok := props[name].(string)
		if !ok || s == "" {
			return k, false
		}
		k[i] = s
	}
	return k, true
}

// CollapseHash is the row hash of a collapsed fact: keys.ContentHash over the canonical JSON array
// [type, harness, event, conversation_id, messageID, partID, field]. ok is false when the payload
// lacks the collapse key.
func CollapseHash(typ, harness, event, conv string, payload map[string]any) (string, bool) {
	k, ok := collapseKey(payload)
	if !ok {
		return "", false
	}
	var buf bytes.Buffer
	enc := json.NewEncoder(&buf)
	enc.SetEscapeHTML(false)
	if err := enc.Encode([]string{typ, harness, event, conv, k[0], k[1], k[2]}); err != nil {
		return "", false
	}
	return keys.ContentHash(bytes.TrimRight(buf.Bytes(), "\n")), true
}
