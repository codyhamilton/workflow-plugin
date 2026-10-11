package compact

import (
	"os"
	"path/filepath"
	"testing"

	"github.com/codyhamilton/workflow-plugin/tools/workflow/internal/store"
)

func TestFinishNeedBytes(t *testing.T) {
	tn := openExclusive(t)
	hookA := []byte(`{"type":"hook_event","conversation_id":"c","harness":"claude","event":"PreToolUse","ts":1,"payload":{"cwd":"/x"}}`)
	hookB := []byte(`{"type":"hook_event","conversation_id":"c","harness":"claude","event":"PostToolUse","ts":2,"payload":{"cwd":"/x"}}`)
	art := []byte(`{"type":"artifact_version","conversation_id":"c","harness":"claude","event":"","ts":3,"path":"p"}`)
	insertRow(t, tn, "h1", "hook_event", "c", "claude", "PreToolUse", 1, hookA)
	insertRow(t, tn, "h2", "hook_event", "c", "claude", "PostToolUse", 2, hookB)
	insertRow(t, tn, "a1", "artifact_version", "c", "claude", "", 3, art)

	sum := int64(len(hookA) + len(hookB))
	fi, err := os.Stat(filepath.Join(tn.Dir(), "ledger.db"))
	if err != nil {
		t.Fatal(err)
	}
	final := int64(minFinalDB)
	if fi.Size()-sum > final {
		final = fi.Size() - sum
	}
	want := uint64(sum/3) + uint64(final) + uint64(walHeadroom)
	got, err := NeedBytes(tn)
	if err != nil {
		t.Fatalf("NeedBytes: %v", err)
	}
	if got != want {
		t.Fatalf("NeedBytes = %d, want %d", got, want)
	}
}

func TestFinishNeedBytesRequiresExclusive(t *testing.T) {
	dir := t.TempDir()
	tn, err := store.Open(dir, store.Options{})
	if err != nil {
		t.Fatal(err)
	}
	defer tn.Close()
	if _, err := NeedBytes(tn); err == nil {
		t.Fatal("NeedBytes must error without the exclusive lock")
	}
}

func TestFinishFreeBytes(t *testing.T) {
	got, err := FreeBytes(t.TempDir())
	if err != nil {
		t.Fatalf("FreeBytes: %v", err)
	}
	if got == 0 {
		t.Fatal("FreeBytes returned 0")
	}
}
