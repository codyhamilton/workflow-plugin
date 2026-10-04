package screen

import (
	"context"
	"errors"
	"os"
	"testing"
	"time"

	"github.com/codyhamilton/workflow-plugin/tools/workflow/internal/keys"
	"github.com/codyhamilton/workflow-plugin/tools/workflow/internal/scorer"
	"github.com/codyhamilton/workflow-plugin/tools/workflow/internal/store"
)

func TestStepNoFactYet(t *testing.T) {
	tn, err := store.Open(t.TempDir(), store.Options{})
	if err != nil {
		t.Fatal(err)
	}
	defer tn.Close()
	c := []byte("orphan\n")
	h := keys.ContentHash(c)
	if err := tn.WritePending(h, c); err != nil {
		t.Fatal(err)
	}
	f := &scorer.Fake{}
	step := Step(f)
	if err := step(context.Background(), tn, h); err != nil || len(f.ScreenCalls) != 0 || !tn.HasPending(h) {
		t.Fatalf("young orphan not skipped: %v %d", err, len(f.ScreenCalls))
	}
	old := time.Now().Add(-2 * time.Minute)
	if err := os.Chtimes(tn.PendingPath(h), old, old); err != nil {
		t.Fatal(err)
	}
	if err := step(context.Background(), tn, h); err != nil || len(f.ScreenCalls) != 1 || len(f.ScreenCalls[0].Kinds) != 0 || !tn.HasBlob(h) {
		t.Fatalf("old orphan not screened without kinds: %v", err)
	}
	if len(f.ScoreCalls) != 0 {
		t.Fatal("scored with no kinds")
	}
}

func TestStepUnreachableWrapped(t *testing.T) {
	tn, _ := store.Open(t.TempDir(), store.Options{})
	defer tn.Close()
	c := []byte("x\n")
	h := keys.ContentHash(c)
	tn.WritePending(h, c)
	old := time.Now().Add(-2 * time.Minute)
	os.Chtimes(tn.PendingPath(h), old, old)
	err := Step(&scorer.Fake{Err: scorer.ErrUnreachable})(context.Background(), tn, h)
	if !errors.Is(err, scorer.ErrUnreachable) || !tn.HasPending(h) {
		t.Fatalf("err %v", err)
	}
}
