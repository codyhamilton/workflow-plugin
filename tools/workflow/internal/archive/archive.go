// Package archive is the on-disk record of received hook bodies:
// <tenant dir>/archive/<YYYY-MM>/<conversation_id>.jsonl.zst. Each Append
// writes one complete zstd frame per file; concatenated frames decode as one
// stream. Delivery is at-least-once, so Read deduplicates by row hash.
package archive

import (
	"bufio"
	"bytes"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"os"
	"path/filepath"
	"sort"
	"strings"
	"sync"
	"time"

	"github.com/klauspost/compress/zstd"
)

// Line is one archived hook event.
type Line struct {
	RowHash    string          `json:"row_hash"`
	ReceivedAt int64           `json:"received_at"` // UnixNano, same unit as facts.received_at
	Fact       json.RawMessage `json:"fact"`
}

// Entry is a Line destined for a conversation; TS is the fact ts (unix
// seconds) and picks the UTC month.
type Entry struct {
	ConversationID string
	TS             float64
	Line           Line
}

var mu sync.Mutex

const ext = ".jsonl.zst"

// fileName maps a conversation ID to a safe, injective file name.
func fileName(id string) string {
	if id == "" {
		return "%" + ext // a bare "%" cannot otherwise occur: "%" is escaped
	}
	var b strings.Builder
	for i := 0; i < len(id); i++ {
		c := id[i]
		ok := c >= 'A' && c <= 'Z' || c >= 'a' && c <= 'z' || c >= '0' && c <= '9' || c == '.' || c == '_' || c == '-'
		if ok && !(i == 0 && c == '.') {
			b.WriteByte(c)
		} else {
			fmt.Fprintf(&b, "%%%02X", c)
		}
	}
	return b.String() + ext
}

func month(ts float64) string {
	sec := int64(ts)
	if float64(sec) > ts {
		sec--
	}
	return time.Unix(sec, 0).UTC().Format("2006-01")
}

// Append writes entries grouped by (month, conversation), one zstd frame per
// file, and fsyncs before returning.
func Append(tenantDir string, entries []Entry) error {
	type key struct{ month, name string }
	groups := map[key]*bytes.Buffer{}
	var order []key
	for _, e := range entries {
		k := key{month(e.TS), fileName(e.ConversationID)}
		buf := groups[k]
		if buf == nil {
			buf = &bytes.Buffer{}
			groups[k] = buf
			order = append(order, k)
		}
		b, err := json.Marshal(e.Line)
		if err != nil {
			return fmt.Errorf("archive: encode line: %w", err)
		}
		buf.Write(b)
		buf.WriteByte('\n')
	}
	mu.Lock()
	defer mu.Unlock()
	for _, k := range order {
		var frame bytes.Buffer
		zw, err := zstd.NewWriter(&frame)
		if err != nil {
			return err
		}
		if _, err := zw.Write(groups[k].Bytes()); err != nil {
			return err
		}
		if err := zw.Close(); err != nil {
			return err
		}
		dir := filepath.Join(tenantDir, "archive", k.month)
		if err := os.MkdirAll(dir, 0o700); err != nil {
			return err
		}
		f, err := os.OpenFile(filepath.Join(dir, k.name), os.O_WRONLY|os.O_APPEND|os.O_CREATE, 0o600)
		if err != nil {
			return err
		}
		_, werr := f.Write(frame.Bytes())
		if werr == nil {
			werr = f.Sync()
		}
		if cerr := f.Close(); werr == nil {
			werr = cerr
		}
		if werr != nil {
			return werr
		}
	}
	return nil
}

// Read returns all archived lines of a conversation across months,
// deduplicated by RowHash (first wins), ordered by fact ts then arrival.
func Read(tenantDir, conversationID string) ([]Line, error) {
	files, err := filepath.Glob(filepath.Join(tenantDir, "archive", "[0-9][0-9][0-9][0-9]-[0-9][0-9]", fileName(conversationID)))
	if err != nil {
		return nil, err
	}
	sort.Strings(files)
	type item struct {
		line Line
		ts   float64
	}
	var items []item
	seen := map[string]bool{}
	for _, p := range files {
		if err := readFile(p, func(l Line) {
			if seen[l.RowHash] {
				return
			}
			seen[l.RowHash] = true
			var h struct {
				TS float64 `json:"ts"`
			}
			_ = json.Unmarshal(l.Fact, &h)
			items = append(items, item{l, h.TS})
		}); err != nil {
			return nil, fmt.Errorf("archive: %s: %w", p, err)
		}
	}
	sort.SliceStable(items, func(i, j int) bool { return items[i].ts < items[j].ts })
	out := make([]Line, len(items))
	for i, it := range items {
		out[i] = it.line
	}
	return out, nil
}

func readFile(path string, fn func(Line)) error {
	f, err := os.Open(path)
	if err != nil {
		if errors.Is(err, os.ErrNotExist) {
			return nil
		}
		return err
	}
	defer f.Close()
	zr, err := zstd.NewReader(f)
	if err != nil {
		return err
	}
	defer zr.Close()
	br := bufio.NewReader(zr)
	for {
		b, err := br.ReadBytes('\n')
		if len(bytes.TrimSpace(b)) > 0 {
			var l Line
			if jerr := json.Unmarshal(b, &l); jerr != nil {
				return jerr
			}
			fn(l)
		}
		if err == io.EOF {
			return nil
		}
		if err != nil {
			return err
		}
	}
}
