package scorer

import (
	"os"
	"path/filepath"
	"strings"
	"testing"
)

const realQuality = "../../../quality"
const design1 = "../../../../docs/design/01-event-model-and-ingest.md"

func TestReportChecksVerbatim(t *testing.T) {
	cs, err := LoadChecks(realQuality)
	if err != nil {
		t.Fatal(err)
	}
	doc, err := os.ReadFile(design1)
	if err != nil {
		t.Fatal(err)
	}
	rep := cs.For("report")
	if len(rep) != 5 {
		t.Fatalf("report checks = %d, want 5", len(rep))
	}
	for _, c := range rep {
		if !strings.Contains(string(doc), c.Q) {
			t.Errorf("%s: q not verbatim in design 1: %q", c.Name, c.Q)
		}
	}
}

func write(t *testing.T, path, s string) {
	t.Helper()
	if err := os.MkdirAll(filepath.Dir(path), 0o755); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(path, []byte(s), 0o644); err != nil {
		t.Fatal(err)
	}
}

const crit = `{"version":"1","brief":{"det":{"x":{}},"jev":{"b.one":{"q":"Q1","levels":["a","b"],"invert":true},"b.two":{"q":"Q2","levels":["a","b"],"invert":null}}},"design":{"det":{},"jev":{"d.one":{"q":"D","levels":["a","b"]}}}}`

func TestLoadChecks(t *testing.T) {
	t.Run("real", func(t *testing.T) {
		cs, err := LoadChecks(realQuality)
		if err != nil {
			t.Fatal(err)
		}
		for kind, want := range map[string]int{"design": 11, "brief": 11, "report": 5} {
			if got := cs.Count(kind); got != want {
				t.Errorf("%s = %d, want %d", kind, got, want)
			}
			if len(cs.For(kind)) != want {
				t.Errorf("For(%s) len mismatch", kind)
			}
		}
	})
	t.Run("override remove and order", func(t *testing.T) {
		d := t.TempDir()
		write(t, filepath.Join(d, "criteria.json"), crit)
		write(t, filepath.Join(d, "checks", "a.json"), `{"checks":[{"kind":"brief","name":"b.two","q":"Q2new","levels":["x","y","z"]},{"kind":"brief","name":"b.zero","q":"Z","levels":["a","b"],"invert":true}]}`)
		write(t, filepath.Join(d, "checks", "b.json"), `{"checks":[{"kind":"brief","name":"b.one","active":false,"q":"","levels":null}]}`)
		cs, err := LoadChecks(d)
		if err != nil {
			t.Fatal(err)
		}
		b := cs.For("brief")
		if len(b) != 2 || b[0].Name != "b.two" || b[1].Name != "b.zero" {
			t.Fatalf("brief = %+v", b)
		}
		if b[0].Q != "Q2new" || len(b[0].Levels) != 3 || b[0].Invert || !b[1].Invert {
			t.Errorf("override wrong: %+v", b)
		}
		if cs.Count("design") != 1 || cs.Count("report") != 0 {
			t.Errorf("counts wrong")
		}
	})
	bad := map[string]string{
		"unknown kind": `{"checks":[{"kind":"plan","name":"p.x","q":"Q","levels":["a","b"]}]}`,
		"one level":    `{"checks":[{"kind":"brief","name":"b.x","q":"Q","levels":["a"]}]}`,
		"empty q":      `{"checks":[{"kind":"brief","name":"b.x","q":"","levels":["a","b"]}]}`,
		"bad json":     `{"checks":`,
	}
	for name, body := range bad {
		t.Run(name, func(t *testing.T) {
			d := t.TempDir()
			write(t, filepath.Join(d, "criteria.json"), crit)
			write(t, filepath.Join(d, "checks", "bad.json"), body)
			_, err := LoadChecks(d)
			if err == nil || !strings.Contains(err.Error(), "bad.json") {
				t.Fatalf("err = %v, want one naming bad.json", err)
			}
		})
	}
	t.Run("missing criteria", func(t *testing.T) {
		if _, err := LoadChecks(t.TempDir()); err == nil {
			t.Fatal("want error")
		}
	})
	t.Run("bad criteria level", func(t *testing.T) {
		d := t.TempDir()
		write(t, filepath.Join(d, "criteria.json"), `{"brief":{"jev":{"b.x":{"q":"Q","levels":["a"]}}}}`)
		_, err := LoadChecks(d)
		if err == nil || !strings.Contains(err.Error(), "b.x") {
			t.Fatalf("err = %v", err)
		}
	})
}
