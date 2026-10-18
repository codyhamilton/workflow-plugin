// Package scorer screens artifact content for credentials and scores it
// against the kind's checks. The model behind the Jev implementation is not
// part of any contract (design 3, Screening and scoring).
package scorer

import (
	"context"
	"errors"
	"sync"
)

// Verdict is a screen result. Reason names the screen and level, never text.
type Verdict struct {
	Flag   bool
	Reason string
}

// Score is one check's result, 0..1, higher is better.
type Score struct {
	Check  string
	Result float64
}

// Scorer screens and scores content. kinds is every artifact kind the content
// was seen under ("design", "brief", "report"), or empty.
type Scorer interface {
	// Name is written to screens.scorer and scores.scorer.
	Name() string
	Screen(ctx context.Context, content []byte, kinds []string) (Verdict, error)
	Score(ctx context.Context, content []byte, kinds []string) ([]Score, error)
}

// ErrUnreachable means the scorer could not answer now; the content stays
// pending and the caller backs off.
var ErrUnreachable = errors.New("scorer unreachable")

// Fake is a Scorer for tests in other packages. It returns its fields and
// records calls.
type Fake struct {
	Verdict Verdict
	Scores  []Score
	Err     error // returned by both Screen and Score when set

	mu          sync.Mutex
	ScreenCalls []Call
	ScoreCalls  []Call
}

// Call is one recorded Fake call.
type Call struct {
	Content []byte
	Kinds   []string
}

func (f *Fake) Name() string { return "fake" }

func (f *Fake) Screen(_ context.Context, content []byte, kinds []string) (Verdict, error) {
	f.mu.Lock()
	defer f.mu.Unlock()
	f.ScreenCalls = append(f.ScreenCalls, Call{content, kinds})
	if f.Err != nil {
		return Verdict{}, f.Err
	}
	return f.Verdict, nil
}

func (f *Fake) Score(_ context.Context, content []byte, kinds []string) ([]Score, error) {
	f.mu.Lock()
	defer f.mu.Unlock()
	f.ScoreCalls = append(f.ScoreCalls, Call{content, kinds})
	if f.Err != nil {
		return nil, f.Err
	}
	return f.Scores, nil
}
