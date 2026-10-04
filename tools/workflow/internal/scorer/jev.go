package scorer

import (
	"bytes"
	"context"
	"crypto/sha256"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"math"
	"net/http"
	"sync"
	"time"
)

// DefaultURL and DefaultModel match tools/transcript/lib/jev_client.py.
const (
	DefaultURL   = "https://api.typesafe.ai/v1/systemone"
	DefaultModel = "jev-1.13.0"

	screenName     = "screen_credential"
	screenFlagAt   = 2
	maxText        = 60000
	maxKept        = 4
	screenQuestion = "Does this text contain a credential: an API key, token, password, private key or connection string with a live secret?"
)

var screenLevels = []string{
	"No credential or secret value appears",
	"Only placeholders, redacted values, variable names or documented example values",
	"A value that may be a live credential, token, password or private key",
	"A live credential, token, password or private key is plainly present",
}

// Jev is the TypeSafe System One scorer. Create with NewJev (non-empty key).
type Jev struct {
	URL    string
	Model  string
	Client *http.Client

	key    string
	checks Checks

	mu    sync.Mutex
	kept  map[[32]byte][]Score
	order [][32]byte
}

// NewJev returns a Jev using the key and checks. The key is only ever sent as
// the bearer header.
func NewJev(key string, checks Checks) *Jev {
	return &Jev{
		URL: DefaultURL, Model: DefaultModel,
		Client: &http.Client{Timeout: 120 * time.Second},
		key:    key, checks: checks,
		kept: map[[32]byte][]Score{},
	}
}

func (j *Jev) Name() string { return j.Model }

func prefix(kinds []string) string {
	if len(kinds) > 0 {
		switch kinds[0] {
		case "design":
			return "DESIGN DOCUMENT:\n"
		case "brief":
			return "BRIEF:\n"
		case "report":
			return "EXECUTION REPORT:\n"
		}
	}
	return "DOCUMENT:\n"
}

// checksFor returns the checks of every kind in kinds, de-duplicated by name.
func (j *Jev) checksFor(kinds []string) []Check {
	seen := map[string]bool{}
	var out []Check
	for _, k := range kinds {
		for _, c := range j.checks.For(k) {
			if !seen[c.Name] {
				seen[c.Name] = true
				out = append(out, c)
			}
		}
	}
	return out
}

// Screen sends one request holding the screen question and the kinds' checks,
// and keeps the check answers for the following Score of the same content.
func (j *Jev) Screen(ctx context.Context, content []byte, kinds []string) (Verdict, error) {
	cks := j.checksFor(kinds)
	answers, err := j.ask(ctx, content, kinds, cks, true)
	if err != nil {
		return Verdict{}, err
	}
	raw, ok := answers[screenName]
	if !ok {
		return Verdict{}, errors.New("scorer: response has no screen_credential answer")
	}
	j.keep(content, scoresOf(cks, answers))
	level := int(raw)
	if level >= screenFlagAt {
		return Verdict{Flag: true, Reason: fmt.Sprintf("screen: jev %s level %d", screenName, level)}, nil
	}
	return Verdict{}, nil
}

// Score returns the check scores kept by Screen for the same content, or makes
// its own request.
func (j *Jev) Score(ctx context.Context, content []byte, kinds []string) ([]Score, error) {
	if s, ok := j.take(content); ok {
		return s, nil
	}
	cks := j.checksFor(kinds)
	answers, err := j.ask(ctx, content, kinds, cks, false)
	if err != nil {
		return nil, err
	}
	return scoresOf(cks, answers), nil
}

func scoresOf(cks []Check, answers map[string]float64) []Score {
	var out []Score
	for _, c := range cks {
		raw, ok := answers[c.Name]
		if !ok {
			continue
		}
		x := raw / 3
		if c.Invert {
			x = 1 - x
		}
		out = append(out, Score{Check: c.Name, Result: math.Round(x*1000) / 1000})
	}
	return out
}

func (j *Jev) keep(content []byte, s []Score) {
	h := sha256.Sum256(content)
	j.mu.Lock()
	defer j.mu.Unlock()
	if _, ok := j.kept[h]; !ok {
		j.order = append(j.order, h)
	}
	j.kept[h] = s
	for len(j.order) > maxKept {
		delete(j.kept, j.order[0])
		j.order = j.order[1:]
	}
}

func (j *Jev) take(content []byte) ([]Score, bool) {
	h := sha256.Sum256(content)
	j.mu.Lock()
	defer j.mu.Unlock()
	s, ok := j.kept[h]
	if ok {
		delete(j.kept, h)
		for i, o := range j.order {
			if o == h {
				j.order = append(j.order[:i], j.order[i+1:]...)
				break
			}
		}
	}
	return s, ok
}

// ask makes one System One request and returns raw numeric scores by question.
// Errors carry a status or short cause only, never the key, request or body.
func (j *Jev) ask(ctx context.Context, content []byte, kinds []string, cks []Check, screen bool) (map[string]float64, error) {
	text := string(content)
	if r := []rune(text); len(r) > maxText {
		text = string(r[:maxText])
	}
	qs := map[string]any{}
	if screen {
		qs[screenName] = map[string]any{"type": "score", "instructions": screenQuestion, "criteria": screenLevels}
	}
	for _, c := range cks {
		qs[c.Name] = map[string]any{"type": "score", "instructions": c.Q, "criteria": c.Levels}
	}
	body, err := json.Marshal(map[string]any{
		"model":     j.Model,
		"state":     map[string]any{"snapshot": prefix(kinds) + text},
		"questions": qs,
	})
	if err != nil {
		return nil, errors.New("scorer: encode request")
	}
	req, err := http.NewRequestWithContext(ctx, http.MethodPost, j.URL, bytes.NewReader(body))
	if err != nil {
		return nil, errors.New("scorer: build request")
	}
	req.Header.Set("Authorization", "Bearer "+j.key)
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Accept", "application/json")
	resp, err := j.Client.Do(req)
	if err != nil {
		// Do's error holds the URL, not the key or body; still keep to a short cause.
		return nil, fmt.Errorf("%w: request failed (%s)", ErrUnreachable, causeOf(err))
	}
	defer resp.Body.Close()
	data, err := io.ReadAll(io.LimitReader(resp.Body, 8<<20))
	if err != nil {
		return nil, fmt.Errorf("%w: reading response (%s)", ErrUnreachable, causeOf(err))
	}
	switch s := resp.StatusCode; {
	case s >= 500 || s == 429 || s == 401 || s == 403:
		return nil, fmt.Errorf("%w: HTTP %d", ErrUnreachable, s)
	case s < 200 || s > 299:
		return nil, fmt.Errorf("scorer: HTTP %d", s)
	}
	var out struct {
		Answers map[string]struct {
			Score json.RawMessage `json:"score"`
		} `json:"answers"`
	}
	if err := json.Unmarshal(data, &out); err != nil {
		return nil, errors.New("scorer: malformed response body")
	}
	res := map[string]float64{}
	for name, a := range out.Answers {
		var f float64
		if json.Unmarshal(a.Score, &f) != nil {
			if name == screenName {
				return nil, errors.New("scorer: non-numeric screen_credential answer")
			}
			continue
		}
		res[name] = f
	}
	return res, nil
}

func causeOf(err error) string {
	switch {
	case errors.Is(err, context.DeadlineExceeded):
		return "timeout"
	case errors.Is(err, context.Canceled):
		return "canceled"
	}
	var ne interface{ Timeout() bool }
	if errors.As(err, &ne) && ne.Timeout() {
		return "timeout"
	}
	return "connection error"
}
