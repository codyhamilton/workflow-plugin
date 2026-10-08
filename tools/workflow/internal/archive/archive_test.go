package archive

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"sync"
	"testing"
	"time"

	"github.com/klauspost/compress/zstd"
)

func ent(conv string, ts float64, hash string) Entry {
	cj, _ := json.Marshal(conv)
	return Entry{ConversationID: conv, TS: ts, Line: Line{
		RowHash: hash, ReceivedAt: int64(ts * 1e9),
		Fact: json.RawMessage(fmt.Sprintf(`{"conversation_id":%s,"ts":%v}`, cj, ts)),
	}}
}

func TestAppendTwiceZstdDecodes(t *testing.T) {
	dir := t.TempDir()
	if err := Append(dir, []Entry{ent("c1", 1700000000, "h1")}); err != nil {
		t.Fatal(err)
	}
	if err := Append(dir, []Entry{ent("c1", 1700000001, "h2")}); err != nil {
		t.Fatal(err)
	}
	files, _ := filepath.Glob(filepath.Join(dir, "archive", "*", "*.jsonl.zst"))
	if len(files) != 1 {
		t.Fatalf("files = %v", files)
	}
	if _, err := exec.LookPath("zstd"); err == nil {
		out, err := exec.Command("zstd", "-dc", files[0]).Output()
		if err != nil {
			t.Fatal(err)
		}
		lines := strings.Split(strings.TrimSuffix(string(out), "\n"), "\n")
		if len(lines) != 2 || !strings.Contains(lines[0], `"h1"`) || !strings.Contains(lines[1], `"h2"`) {
			t.Fatalf("lines = %q", lines)
		}
	} else {
		t.Log("zstd binary not installed; skipping CLI check")
	}
	got, err := Read(dir, "c1")
	if err != nil || len(got) != 2 || got[0].RowHash != "h1" || got[1].RowHash != "h2" {
		t.Fatalf("got %v err %v", got, err)
	}
	fi, _ := os.Stat(files[0])
	if fi.Mode().Perm() != 0o600 {
		t.Fatalf("mode %v", fi.Mode())
	}
}

func TestMonthBoundary(t *testing.T) {
	dir := t.TempDir()
	last := float64(time.Date(2026, 1, 31, 23, 59, 59, 0, time.UTC).Unix())
	first := last + 1
	if err := Append(dir, []Entry{ent("c", last, "a"), ent("c", first, "b")}); err != nil {
		t.Fatal(err)
	}
	for _, m := range []string{"2026-01", "2026-02"} {
		if _, err := os.Stat(filepath.Join(dir, "archive", m, "c.jsonl.zst")); err != nil {
			t.Fatal(err)
		}
	}
	got, _ := Read(dir, "c")
	if len(got) != 2 || got[0].RowHash != "a" {
		t.Fatalf("got %v", got)
	}
}

func TestReadDedupAndOrder(t *testing.T) {
	dir := t.TempDir()
	Append(dir, []Entry{ent("c", 30, "z"), ent("c", 10, "x")})
	Append(dir, []Entry{ent("c", 20, "y"), ent("c", 10, "x")})
	got, err := Read(dir, "c")
	if err != nil {
		t.Fatal(err)
	}
	var hs []string
	for _, l := range got {
		hs = append(hs, l.RowHash)
	}
	if strings.Join(hs, ",") != "x,y,z" {
		t.Fatalf("hs = %v", hs)
	}
}

func TestReadMissing(t *testing.T) {
	got, err := Read(t.TempDir(), "nope")
	if err != nil || got == nil || len(got) != 0 {
		t.Fatalf("got %#v err %v", got, err)
	}
}

func TestHostileIDs(t *testing.T) {
	dir := t.TempDir()
	ids := []string{"../x", "a/b", ".hidden", "", "..", "%", "a%2Fb", "a/b2", `a\b`, "x\x00y"}
	for i, id := range ids {
		if err := Append(dir, []Entry{ent(id, 1700000000, fmt.Sprint("h", i))}); err != nil {
			t.Fatalf("%q: %v", id, err)
		}
	}
	for i, id := range ids {
		got, err := Read(dir, id)
		if err != nil || len(got) != 1 || got[0].RowHash != fmt.Sprint("h", i) {
			t.Fatalf("%q: got %v err %v", id, got, err)
		}
	}
	var n int
	filepath.Walk(dir, func(p string, fi os.FileInfo, err error) error {
		if p == dir {
			return nil
		}
		if rel, e := filepath.Rel(filepath.Join(dir, "archive"), p); e != nil || strings.HasPrefix(rel, "..") {
			t.Errorf("escaped: %s", p)
		}
		if !fi.IsDir() {
			n++
			if strings.HasPrefix(fi.Name(), ".") {
				t.Errorf("hidden file %s", p)
			}
		}
		return nil
	})
	if n != len(ids) {
		t.Fatalf("files %d want %d (collision?)", n, len(ids))
	}
	if _, err := os.Stat(filepath.Join(dir, "x")); err == nil {
		t.Fatal("escaped to tenant dir")
	}
}

func TestConcurrentAppend(t *testing.T) {
	dir := t.TempDir()
	var wg sync.WaitGroup
	for g := 0; g < 8; g++ {
		wg.Add(1)
		go func(g int) {
			defer wg.Done()
			for i := 0; i < 20; i++ {
				if err := Append(dir, []Entry{ent("c", float64(1700000000+g*100+i), fmt.Sprint(g, "-", i))}); err != nil {
					t.Error(err)
				}
			}
		}(g)
	}
	wg.Wait()
	got, err := Read(dir, "c")
	if err != nil || len(got) != 160 {
		t.Fatalf("len %d err %v", len(got), err)
	}
	if bytes.Contains(got[0].Fact, []byte("\n")) {
		t.Fatal("newline in fact")
	}
}

func TestAppendVerbatimHTMLChars(t *testing.T) {
	dir := t.TempDir()
	fact := json.RawMessage(`{"conversation_id":"c","ts":1,"body":"a <b> & c > d"}`)
	if err := Append(dir, []Entry{{ConversationID: "c", TS: 1, Line: Line{RowHash: "h", ReceivedAt: 1, Fact: fact}}}); err != nil {
		t.Fatal(err)
	}
	got, err := Read(dir, "c")
	if err != nil || len(got) != 1 {
		t.Fatalf("got %v err %v", got, err)
	}
	if !bytes.Equal(got[0].Fact, fact) {
		t.Fatalf("round-trip fact = %s, want %s", got[0].Fact, fact)
	}
	files, _ := filepath.Glob(filepath.Join(dir, "archive", "*", "*.jsonl.zst"))
	if len(files) != 1 {
		t.Fatalf("files = %v", files)
	}
	raw, err := os.ReadFile(files[0])
	if err != nil {
		t.Fatal(err)
	}
	zr, err := zstd.NewReader(bytes.NewReader(raw))
	if err != nil {
		t.Fatal(err)
	}
	dec, err := io.ReadAll(zr)
	zr.Close()
	if err != nil {
		t.Fatal(err)
	}
	for _, esc := range []string{`\u003c`, `\u003e`, `\u0026`} {
		if bytes.Contains(dec, []byte(esc)) {
			t.Fatalf("archive escaped %s: %s", esc, dec)
		}
	}
	if !bytes.Contains(dec, []byte("<b> & c > d")) {
		t.Fatalf("archive body not verbatim: %s", dec)
	}
}
