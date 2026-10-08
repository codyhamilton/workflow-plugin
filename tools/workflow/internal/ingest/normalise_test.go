package ingest

import (
	"bytes"
	"encoding/json"
	"os"
	"path/filepath"
	"testing"

	"github.com/codyhamilton/workflow-plugin/tools/workflow/internal/secrets"
)

type policyFixture struct {
	Facts []struct {
		ID, Harness, Event string
		Payload            map[string]any
	} `json:"facts"`
	Expect []struct {
		ID           string   `json:"id"`
		Policy       string   `json:"policy"`
		NormEvent    string   `json:"norm_event"`
		Tool         string   `json:"tool"`
		Model        string   `json:"model"`
		TokIn        int64    `json:"tok_in"`
		TokOut       int64    `json:"tok_out"`
		TokCacheRead int64    `json:"tok_cache_read"`
		TokCacheWr   int64    `json:"tok_cache_write"`
		TokReasoning int64    `json:"tok_reasoning"`
		CostReported *float64 `json:"cost_reported"`
	} `json:"expect"`
	ExpectTotals map[string]struct {
		TokIn        int64 `json:"tok_in"`
		TokOut       int64 `json:"tok_out"`
		TokCacheRead int64 `json:"tok_cache_read"`
		TokCacheWr   int64 `json:"tok_cache_write"`
		TokReasoning int64 `json:"tok_reasoning"`
	} `json:"expect_totals"`
}

func loadPolicyFixture(t *testing.T) policyFixture {
	t.Helper()
	raw, err := os.ReadFile(filepath.Join("..", "..", "..", "hooklog", "tests", "fixtures", "ingest_policy.json"))
	if err != nil {
		t.Fatal(err)
	}
	dec := json.NewDecoder(bytes.NewReader(raw))
	dec.UseNumber()
	var fx policyFixture
	if err := dec.Decode(&fx); err != nil {
		t.Fatal(err)
	}
	if len(fx.Facts) != len(fx.Expect) {
		t.Fatalf("facts %d != expect %d", len(fx.Facts), len(fx.Expect))
	}
	return fx
}

func TestNormaliseFixtureDerive(t *testing.T) {
	fx := loadPolicyFixture(t)
	for i, f := range fx.Facts {
		e := fx.Expect[i]
		if e.ID != f.ID {
			t.Fatalf("expect[%d] id %s != fact %s", i, e.ID, f.ID)
		}
		d := Derive(f.Harness, f.Event, f.Payload)
		if d.NormEvent != e.NormEvent || d.Tool != e.Tool || d.Model != e.Model ||
			d.TokIn != e.TokIn || d.TokOut != e.TokOut || d.TokCacheRead != e.TokCacheRead ||
			d.TokCacheWrite != e.TokCacheWr || d.TokReasoning != e.TokReasoning {
			t.Errorf("%s (%s %s): got %+v want %+v", f.ID, f.Harness, f.Event, d, e)
		}
		if (d.CostReported == nil) != (e.CostReported == nil) || (e.CostReported != nil && *d.CostReported != *e.CostReported) {
			t.Errorf("%s: cost got %v want %v", f.ID, d.CostReported, e.CostReported)
		}
	}
}

func TestNormaliseFixtureNoSecrets(t *testing.T) {
	fx := loadPolicyFixture(t)
	for _, f := range fx.Facts {
		if r := Precheck(map[string]any{"payload": f.Payload}); r != "" {
			t.Errorf("%s flagged: %s", f.ID, r)
		}
		b, _ := json.Marshal(f.Payload)
		if h := secrets.Scan(string(b)); len(h) > 0 {
			t.Errorf("%s: secrets.Scan hit %s", f.ID, h[0].Pattern)
		}
	}
}

// Every (harness, event) pair seen in the local ledger (plus fixture pairs) maps as listed here.
func TestNormaliseTable(t *testing.T) {
	cases := map[string]string{
		"opencode|message.part.updated": "message_part", "opencode|message.updated": "other",
		"opencode|tool.execute.after": "tool_post", "opencode|session.status": "other",
		"codex|PostToolUse": "tool_post", "opencode|tool.execute.before": "tool_pre",
		"opencode|session.updated": "other", "claude|PostToolUse": "tool_post",
		"claude|transcript.assistant_message": "usage", "opencode|session.diff": "other",
		"opencode|chat.headers": "other", "opencode|chat.params": "other",
		"opencode|experimental.chat.system.transform": "other", "codex|transcript.token_count": "usage",
		"opencode|PostToolBatch": "batch_end", "opencode|transcript.assistant_message": "usage",
		"opencode|shell.env": "other", "codex|transcript.assistant_message": "assistant_message",
		"opencode|experimental.text.complete": "assistant_message", "opencode|chat.message": "prompt",
		"opencode|session.created": "session_start", "codex|PreToolUse": "tool_pre",
		"claude|PreToolUse": "tool_pre", "claude|PostToolBatch": "batch_end",
		"claude|UserPromptSubmit": "prompt", "opencode|Stop": "turn_end",
		"opencode|session.idle": "other", "codex|UserPromptSubmit": "prompt", "codex|Stop": "turn_end",
		"codex|SessionStart": "session_start", "claude|SessionStart": "session_start",
		"claude|MessageDisplay": "assistant_message", "claude|SubagentStart": "subagent_start",
		"claude|InstructionsLoaded": "other", "opencode|permission.asked": "other",
		"opencode|permission.replied": "other", "claude|SessionEnd": "session_end",
		"opencode|todo.updated": "other", "claude|SubagentStop": "subagent_end",
		"codex|SessionEnd": "session_end", "claude|Stop": "turn_end",
		"claude|PostToolUseFailure": "tool_fail", "codex|SubagentStart": "subagent_start",
		"codex|SubagentStop": "subagent_end", "codex|PermissionRequest": "other",
		"claude|PostCompact": "compact", "claude|PreCompact": "compact", "claude|Notification": "other",
		"claude|StopFailure": "turn_end", "claude|postToolUse": "tool_post",
		"cursor|afterFileEdit": "tool_post", "cursor|postToolUse": "tool_post",
		"claude|ConfigChange": "other", "claude|PermissionRequest": "other", "codex|Interrupt": "other",
		"codex|PostCompact": "compact", "codex|PreCompact": "compact",
		"claude|PostModelSwitch": "other", "claude|PreModelSwitch": "other",
		"claude|UserPromptExpansion": "other", "opencode|PostToolUse": "tool_post",
		"opencode|UserPromptSubmit": "prompt", "opencode|message.part.delta": "message_part",
		"cursor|beforeSubmitPrompt": "prompt", "cursor|afterShellExecution": "tool_post",
		"cursor|stop": "turn_end", "cursor|afterAgentResponse": "assistant_message",
		"nobody|Whatever": "other", "claude|": "other",
	}
	for k, want := range cases {
		var h, e string
		for i := range k {
			if k[i] == '|' {
				h, e = k[:i], k[i+1:]
				break
			}
		}
		// Usage mapping depends on the payload; give the usage-bearing events one.
		var p map[string]any
		switch k {
		case "claude|transcript.assistant_message":
			p = map[string]any{"usage": map[string]any{"input_tokens": json.Number("1")}}
		case "opencode|transcript.assistant_message":
			p = map[string]any{"tokens": map[string]any{"input": json.Number("1")}}
		}
		if got := Derive(h, e, p).NormEvent; got != want {
			t.Errorf("%s: got %s want %s", k, got, want)
		}
	}
}

func TestNormaliseCaseInsensitiveAndRobust(t *testing.T) {
	if Derive("claude", "POSTTOOLUSE", nil).NormEvent != "tool_post" {
		t.Error("event names match case-insensitively")
	}
	d := Derive("claude", "transcript.assistant_message", map[string]any{"usage": "bad", "model": 5})
	if d.NormEvent == "" || d.Model != "" || d.TokIn != 0 {
		t.Errorf("mistyped fields give zero values: %+v", d)
	}
	for _, h := range []string{"claude", "codex", "opencode", "cursor", ""} {
		for _, e := range []string{"transcript.token_count", "transcript.assistant_message", "PostToolUse", ""} {
			if Derive(h, e, nil).NormEvent == "" {
				t.Errorf("%s %s: NormEvent empty", h, e)
			}
		}
	}
	if Derive("claude", "PreToolUse", map[string]any{"tool_name": "Bash"}).Tool != "Bash" ||
		Derive("claude", "UserPromptSubmit", map[string]any{"tool_name": "Bash"}).Tool != "" {
		t.Error("tool only on tool events")
	}
}
