// Package screen is the screen step of design 3: screen one piece of stored content through a
// scorer, then promote it with its scores or delete it with a rejection.
package screen

import (
	"context"
	"fmt"
	"os"
	"time"

	"github.com/codyhamilton/workflow-plugin/tools/workflow/internal/keys"
	"github.com/codyhamilton/workflow-plugin/tools/workflow/internal/scorer"
	"github.com/codyhamilton/workflow-plugin/tools/workflow/internal/store"
)

// young is how long a pending file with no fact row may wait for its fact to commit.
const young = time.Minute

// Step returns the screen step for sc. It matches serve.ScreenFunc.
func Step(sc scorer.Scorer) func(ctx context.Context, t *store.Tenant, hash string) error {
	return func(ctx context.Context, t *store.Tenant, hash string) error {
		pending := true
		content, err := t.ReadPending(hash)
		if os.IsNotExist(err) {
			pending = false
			content, err = t.ReadBlob(hash) // promoted but never screened
		}
		if err != nil {
			return fmt.Errorf("read content: %w", err)
		}
		ci, err := t.ContentFacts(ctx, hash)
		if err != nil {
			return fmt.Errorf("read facts: %w", err)
		}
		if pending && len(ci.Paths) == 0 {
			// Ingest writes pending before the fact commits; give it a minute.
			if mt, err := t.PendingModTime(hash); err == nil && time.Since(mt) < young {
				return nil
			}
		}
		var kinds []string
		for _, p := range ci.Paths {
			if k := keys.Kind(p); k != "" && !has(kinds, k) {
				kinds = append(kinds, k)
			}
		}
		v, err := sc.Screen(ctx, content, kinds)
		if err != nil {
			return fmt.Errorf("screen: %w", err)
		}
		if v.Flag {
			r := store.Rejection{Stage: "screen", Pattern: "jev_screen", Reason: v.Reason, FactType: "artifact_version",
				ContentHash: hash, Path: ci.LatestPath, ConversationID: ci.ConversationID}
			if pending {
				return t.DropPending(ctx, hash, r)
			}
			return t.DropBlob(ctx, hash, r)
		}
		var scores []store.Score
		if len(kinds) > 0 {
			ss, err := sc.Score(ctx, content, kinds)
			if err != nil {
				return fmt.Errorf("score: %w", err)
			}
			for _, s := range ss {
				scores = append(scores, store.Score{Check: s.Check, Result: s.Result})
			}
		}
		return t.Promote(ctx, hash, store.Screen{Verdict: "pass", Scorer: sc.Name()}, scores...)
	}
}

func has(xs []string, x string) bool {
	for _, y := range xs {
		if y == x {
			return true
		}
	}
	return false
}
