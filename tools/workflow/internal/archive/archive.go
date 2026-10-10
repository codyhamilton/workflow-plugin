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
		enc := json.NewEncoder(buf)
		enc.SetEscapeHTML(false)
		if err := enc.Encode(e.Line); err != nil {
			return fmt.Errorf("archive: encode line: %w", err)
		}
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

// Repaired reports what Repair changed.
type Repaired struct {
	Files int // files rewritten because they ended in a torn tail
	Lines int // complete lines dropped with those torn frames
}

// readFile decodes one archive file, delivering the lines of every frame
// before the first torn frame. A torn tail (a partial final zstd frame or a
// partial trailing line, left by a crash during Append) is not an error;
// damage beyond that (a frame that fails its checksum, a complete line that is
// not valid JSON) is returned as an error.
func readFile(path string, fn func(Line)) error {
	raw, err := os.ReadFile(path)
	if err != nil {
		if errors.Is(err, os.ErrNotExist) {
			return nil
		}
		return err
	}
	if len(raw) == 0 {
		return nil
	}
	if lines, err := linesOf(raw); err == nil {
		for _, l := range lines {
			fn(l)
		}
		return nil
	}
	for _, fr := range splitFrames(raw) {
		lines, err := linesOf(fr)
		if err != nil {
			if errors.Is(err, io.ErrUnexpectedEOF) {
				return nil
			}
			return err
		}
		for _, l := range lines {
			fn(l)
		}
	}
	return nil
}

// linesOf decodes raw as concatenated zstd frames of JSON lines. A truncated
// stream (a torn frame or a torn trailing line) returns io.ErrUnexpectedEOF
// with the lines decoded before the damage; any other decoder error, or a
// complete line that is not valid JSON, is returned as-is.
func linesOf(raw []byte) ([]Line, error) {
	zr, err := zstd.NewReader(bytes.NewReader(raw))
	if err != nil {
		return nil, err
	}
	defer zr.Close()
	var out []Line
	br := bufio.NewReader(zr)
	for {
		b, err := br.ReadBytes('\n')
		complete := len(b) > 0 && b[len(b)-1] == '\n'
		if complete {
			var l Line
			if jerr := json.Unmarshal(b, &l); jerr != nil {
				return out, jerr
			}
			out = append(out, l)
		}
		if err == io.EOF {
			if !complete && len(b) > 0 {
				return out, io.ErrUnexpectedEOF
			}
			return out, nil
		}
		if err != nil {
			return out, err
		}
	}
}

// splitFrames cuts raw into one slice per zstd frame, the later frames located
// by their magic. raw must begin with a frame. It is only used on files whose
// whole-stream decode failed, to tell a torn frame apart from checksum damage.
func splitFrames(raw []byte) [][]byte {
	cuts := make([]int, 0, 4)
	for i := 0; i+5 <= len(raw); i++ {
		if raw[i] == 0x28 && raw[i+1] == 0xb5 && raw[i+2] == 0x2f && raw[i+3] == 0xfd && raw[i+4]&0x08 == 0 {
			cuts = append(cuts, i)
		}
	}
	if len(cuts) == 0 || cuts[0] != 0 {
		return [][]byte{raw}
	}
	frames := make([][]byte, len(cuts))
	for i, c := range cuts {
		end := len(raw)
		if i+1 < len(cuts) {
			end = cuts[i+1]
		}
		frames[i] = raw[c:end]
	}
	return frames
}

// Repair restores archive files left unreadable by a crash during Append. For
// every file under <tenantDir>/archive/*/ it decodes the frames in order and
// drops any that are torn, keeping the frames that decode cleanly; if it
// dropped a torn frame it rewrites the file atomically as one fresh zstd frame
// holding exactly the surviving lines in order, duplicates kept. A healthy file
// is left untouched. Damage other than a torn frame is returned as an error.
func Repair(tenantDir string) (Repaired, error) {
	mu.Lock()
	defer mu.Unlock()
	var rep Repaired
	files, err := filepath.Glob(filepath.Join(tenantDir, "archive", "*", "*"+ext))
	if err != nil {
		return rep, err
	}
	sort.Strings(files)
	for _, p := range files {
		raw, err := os.ReadFile(p)
		if err != nil {
			return rep, err
		}
		if len(raw) == 0 {
			continue
		}
		if _, err := linesOf(raw); err == nil {
			continue // healthy: leave byte- and mtime-identical
		}
		lines, dropped, torn, err := repairFrames(raw)
		if err != nil {
			return rep, err
		}
		if !torn {
			continue
		}
		if err := rewriteFile(p, lines); err != nil {
			return rep, err
		}
		rep.Files++
		rep.Lines += dropped
	}
	return rep, nil
}

func repairFrames(raw []byte) (lines []Line, dropped int, torn bool, err error) {
	for _, fr := range splitFrames(raw) {
		ls, ferr := linesOf(fr)
		if ferr == nil {
			lines = append(lines, ls...)
			continue
		}
		if errors.Is(ferr, io.ErrUnexpectedEOF) {
			torn = true
			dropped += len(ls)
			continue
		}
		return nil, 0, false, ferr
	}
	return lines, dropped, torn, nil
}

func rewriteFile(path string, lines []Line) error {
	var plain bytes.Buffer
	enc := json.NewEncoder(&plain)
	enc.SetEscapeHTML(false)
	for _, l := range lines {
		if err := enc.Encode(l); err != nil {
			return fmt.Errorf("archive: encode line: %w", err)
		}
	}
	var frame bytes.Buffer
	zw, err := zstd.NewWriter(&frame)
	if err != nil {
		return err
	}
	if _, err := zw.Write(plain.Bytes()); err != nil {
		return err
	}
	if err := zw.Close(); err != nil {
		return err
	}
	tmp, err := os.CreateTemp(filepath.Dir(path), ".repair-*")
	if err != nil {
		return err
	}
	name := tmp.Name()
	if _, err := tmp.Write(frame.Bytes()); err != nil {
		tmp.Close()
		os.Remove(name)
		return err
	}
	if err := tmp.Sync(); err != nil {
		tmp.Close()
		os.Remove(name)
		return err
	}
	if err := tmp.Close(); err != nil {
		os.Remove(name)
		return err
	}
	return os.Rename(name, path)
}
