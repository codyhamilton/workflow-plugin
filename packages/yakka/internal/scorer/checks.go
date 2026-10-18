package scorer

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"sort"
)

// Check is one scored question. Levels run worst first; the raw score is the
// level index.
type Check struct {
	Kind   string
	Name   string
	Q      string
	Levels []string
	Invert bool
}

// Checks is the loaded check set per kind.
type Checks struct {
	byKind map[string]map[string]Check
}

var kinds = map[string]bool{"brief": true, "design": true, "report": true}

// For returns the kind's checks ordered by name.
func (c Checks) For(kind string) []Check {
	m := c.byKind[kind]
	out := make([]Check, 0, len(m))
	for _, ch := range m {
		out = append(out, ch)
	}
	sort.Slice(out, func(i, j int) bool { return out[i].Name < out[j].Name })
	return out
}

// Count is the number of checks for a kind.
func (c Checks) Count(kind string) int { return len(c.byKind[kind]) }

type rawCheck struct {
	Kind   string   `json:"kind"`
	Name   string   `json:"name"`
	Q      string   `json:"q"`
	Levels []string `json:"levels"`
	Invert *bool    `json:"invert"`
	Active *bool    `json:"active"`
}

func validate(file string, c Check) error {
	if c.Q == "" {
		return fmt.Errorf("%s: check %q: empty q", file, c.Name)
	}
	if len(c.Levels) < 2 {
		return fmt.Errorf("%s: check %q: needs at least two levels", file, c.Name)
	}
	return nil
}

// LoadChecks reads dir/criteria.json (each kind's jev map; det is ignored)
// then dir/checks/*.json in filename order. A later check overrides the same
// name; active:false removes it.
func LoadChecks(dir string) (Checks, error) {
	cs := Checks{byKind: map[string]map[string]Check{}}
	critPath := filepath.Join(dir, "criteria.json")
	b, err := os.ReadFile(critPath)
	if err != nil {
		return Checks{}, fmt.Errorf("criteria.json: %w", err)
	}
	var crit map[string]json.RawMessage
	if err := json.Unmarshal(b, &crit); err != nil {
		return Checks{}, fmt.Errorf("criteria.json: %w", err)
	}
	for kind, raw := range crit {
		if !kinds[kind] {
			continue // version, note, and the like
		}
		var k struct {
			Jev map[string]rawCheck `json:"jev"`
		}
		if err := json.Unmarshal(raw, &k); err != nil {
			return Checks{}, fmt.Errorf("criteria.json: kind %s: %w", kind, err)
		}
		for name, r := range k.Jev {
			c := Check{Kind: kind, Name: name, Q: r.Q, Levels: r.Levels, Invert: r.Invert != nil && *r.Invert}
			if err := validate("criteria.json", c); err != nil {
				return Checks{}, err
			}
			cs.put(c)
		}
	}
	files, err := filepath.Glob(filepath.Join(dir, "checks", "*.json"))
	if err != nil {
		return Checks{}, err
	}
	sort.Strings(files)
	for _, f := range files {
		base := filepath.Base(f)
		b, err := os.ReadFile(f)
		if err != nil {
			return Checks{}, fmt.Errorf("%s: %w", base, err)
		}
		var doc struct {
			Checks []rawCheck `json:"checks"`
		}
		if err := json.Unmarshal(b, &doc); err != nil {
			return Checks{}, fmt.Errorf("%s: %w", base, err)
		}
		for _, r := range doc.Checks {
			if !kinds[r.Kind] {
				return Checks{}, fmt.Errorf("%s: check %q: unknown kind %q", base, r.Name, r.Kind)
			}
			if r.Active != nil && !*r.Active {
				delete(cs.byKind[r.Kind], r.Name)
				continue
			}
			c := Check{Kind: r.Kind, Name: r.Name, Q: r.Q, Levels: r.Levels, Invert: r.Invert != nil && *r.Invert}
			if err := validate(base, c); err != nil {
				return Checks{}, err
			}
			cs.put(c)
		}
	}
	return cs, nil
}

func (c *Checks) put(ch Check) {
	if c.byKind[ch.Kind] == nil {
		c.byKind[ch.Kind] = map[string]Check{}
	}
	c.byKind[ch.Kind][ch.Name] = ch
}
