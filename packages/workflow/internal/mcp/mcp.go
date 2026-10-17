// Package mcp is the advisory MCP shim of design 4: a hand-written JSON-RPC 2.0
// server over stdio (one JSON object per line) exposing artifact_feedback,
// list_checks and search_artifacts. It forwards to the quality service named by
// the client config and adds local queue state. It never turns an unreachable
// or unconfigured service into a protocol error.
package mcp

import (
	"bufio"
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"os"
	"os/exec"
	"strings"
	"syscall"
	"time"

	"github.com/codyhamilton/workflow-plugin/tools/workflow/internal/drain"
)

// Options configures Serve. Zero values take defaults.
type Options struct {
	Version    string
	QueueDir   string                 // default drain.QueueDir()
	Wait       time.Duration          // how long to wait for the drain; 0 = 1.5 s, negative = no wait
	StartDrain func() error           // default: start `<this binary> drain` detached
	Getwd      func() (string, error) // default os.Getwd
	HTTP       *http.Client           // default: 3 s timeout client
}

func (o *Options) defaults() {
	if o.QueueDir == "" {
		o.QueueDir = drain.QueueDir()
	}
	if o.Wait == 0 {
		o.Wait = 1500 * time.Millisecond
	}
	if o.StartDrain == nil {
		o.StartDrain = startDrain
	}
	if o.Getwd == nil {
		o.Getwd = os.Getwd
	}
	if o.HTTP == nil {
		o.HTTP = &http.Client{Timeout: 3 * time.Second}
	}
}

func startDrain() error {
	exe, err := os.Executable()
	if err != nil {
		return err
	}
	cmd := exec.Command(exe, "drain")
	cmd.SysProcAttr = &syscall.SysProcAttr{Setsid: true}
	if err := cmd.Start(); err != nil {
		return err
	}
	go cmd.Wait()
	return nil
}

var versions = map[string]bool{"2025-11-25": true, "2025-06-18": true, "2025-03-26": true, "2024-11-05": true}

const instructions = "Read-only advice on design, brief and report files: delivery state and scores for a file, the checks a kind is scored against, and similar past artifacts."

type rpcError struct {
	Code    int    `json:"code"`
	Message string `json:"message"`
}

type response struct {
	JSONRPC string          `json:"jsonrpc"`
	ID      json.RawMessage `json:"id"`
	Result  any             `json:"result,omitempty"`
	Error   *rpcError       `json:"error,omitempty"`
}

type server struct{ o Options }

// Serve runs the protocol loop until r reaches EOF (nil) or ctx ends.
func Serve(ctx context.Context, r io.Reader, w io.Writer, opts Options) error {
	opts.defaults()
	s := &server{o: opts}
	lines := make(chan []byte)
	go func() {
		defer close(lines)
		br := bufio.NewReader(r)
		for {
			l, err := br.ReadBytes('\n')
			if len(bytes.TrimSpace(l)) > 0 {
				select {
				case lines <- l:
				case <-ctx.Done():
					return
				}
			}
			if err != nil {
				return
			}
		}
	}()
	for {
		select {
		case <-ctx.Done():
			return ctx.Err()
		case l, ok := <-lines:
			if !ok {
				return nil
			}
			if resp := s.handle(ctx, l); resp != nil {
				b, _ := json.Marshal(resp)
				if _, err := w.Write(append(b, '\n')); err != nil {
					return err
				}
			}
		}
	}
}

func fail(id json.RawMessage, code int, msg string) *response {
	if id == nil {
		id = json.RawMessage("null")
	}
	return &response{JSONRPC: "2.0", ID: id, Error: &rpcError{code, msg}}
}

func (s *server) handle(ctx context.Context, line []byte) *response {
	var v any
	if err := json.Unmarshal(line, &v); err != nil {
		return fail(nil, -32700, "parse error")
	}
	if _, ok := v.(map[string]any); !ok {
		return fail(nil, -32600, "invalid request: expected a single JSON object")
	}
	var rq struct {
		ID     json.RawMessage `json:"id"`
		Method string          `json:"method"`
		Params json.RawMessage `json:"params"`
	}
	if err := json.Unmarshal(line, &rq); err != nil || rq.Method == "" {
		return fail(rq.ID, -32600, "invalid request")
	}
	if rq.ID == nil { // notification
		return nil
	}
	ok := func(res any) *response { return &response{JSONRPC: "2.0", ID: rq.ID, Result: res} }
	switch rq.Method {
	case "initialize":
		var p struct {
			ProtocolVersion string `json:"protocolVersion"`
		}
		json.Unmarshal(rq.Params, &p)
		pv := "2025-11-25"
		if versions[p.ProtocolVersion] {
			pv = p.ProtocolVersion
		}
		return ok(map[string]any{"protocolVersion": pv, "capabilities": map[string]any{"tools": map[string]any{"listChanged": false}},
			"serverInfo": map[string]any{"name": "workflow", "version": s.o.Version}, "instructions": instructions})
	case "ping":
		return ok(map[string]any{})
	case "tools/list":
		return ok(map[string]any{"tools": toolList})
	case "tools/call":
		var p struct {
			Name string          `json:"name"`
			Args json.RawMessage `json:"arguments"`
		}
		json.Unmarshal(rq.Params, &p)
		var text string
		var bad bool
		args := map[string]any{}
		argErr := ""
		if len(p.Args) > 0 && string(p.Args) != "null" {
			if err := json.Unmarshal(p.Args, &args); err != nil {
				argErr = "arguments must be an object"
			}
		}
		switch p.Name {
		case "artifact_feedback", "list_checks", "search_artifacts":
		default:
			return fail(rq.ID, -32602, "unknown tool")
		}
		if argErr != "" {
			text, bad = argErr, true
		} else {
			switch p.Name {
			case "artifact_feedback":
				text, bad = s.feedback(ctx, args)
			case "list_checks":
				text, bad = s.listChecks(ctx, args)
			default:
				text, bad = s.search(ctx, args)
			}
		}
		return ok(map[string]any{"content": []map[string]any{{"type": "text", "text": text}}, "isError": bad})
	}
	return fail(rq.ID, -32601, "method not found: "+rq.Method)
}

var kindEnum = map[string]any{"type": "string", "enum": []string{"design", "brief", "report"}}

func schema(props map[string]any, required ...string) map[string]any {
	return map[string]any{"type": "object", "properties": props, "required": required, "additionalProperties": false}
}

var toolList = []map[string]any{
	{"name": "artifact_feedback", "description": "State of one design, brief or report file: queued, rejected (with the reason), delivered (screen verdict, scores against the tenant baseline), stale or not delivered.",
		"inputSchema": schema(map[string]any{"path": map[string]any{"type": "string", "description": "path of the file, absolute or relative to the working directory"}}, "path"),
		"annotations": map[string]any{"readOnlyHint": true}},
	{"name": "list_checks", "description": "The checks a design, brief or report is scored against.",
		"inputSchema": schema(map[string]any{"kind": kindEnum}, "kind"), "annotations": map[string]any{"readOnlyHint": true}},
	{"name": "search_artifacts", "description": "Similar past designs, briefs and reports in this tenant, with path, repo and a snippet.",
		"inputSchema": schema(map[string]any{"query": map[string]any{"type": "string"}, "kind": kindEnum}, "query"),
		"annotations": map[string]any{"readOnlyHint": true}},
}

func strArg(args map[string]any, name string) (string, bool) {
	s, ok := args[name].(string)
	return s, ok
}

func kindArg(args map[string]any, required bool) (string, string) {
	v, present := args["kind"]
	if !present && !required {
		return "", ""
	}
	k, _ := v.(string)
	if k != "design" && k != "brief" && k != "report" {
		return "", "kind must be one of design, brief, report"
	}
	return k, ""
}

func (s *server) listChecks(ctx context.Context, args map[string]any) (string, bool) {
	kind, bad := kindArg(args, true)
	if bad != "" {
		return bad, true
	}
	var out struct {
		Checks []struct {
			Name   string   `json:"name"`
			Q      string   `json:"q"`
			Levels []string `json:"levels"`
			Invert bool     `json:"invert"`
		} `json:"checks"`
		Loaded *bool `json:"loaded"`
	}
	if msg := s.fetch(ctx, "/v1/checks", map[string]string{"kind": kind}, &out); msg != "" {
		return msg, false
	}
	if (out.Loaded != nil && !*out.Loaded) || len(out.Checks) == 0 {
		return "no checks loaded on the service", false
	}
	var b strings.Builder
	for _, c := range out.Checks {
		fmt.Fprintf(&b, "%s [levels %s]", c.Name, strings.Join(c.Levels, "/"))
		if c.Invert {
			b.WriteString(" [inverted]")
		}
		fmt.Fprintf(&b, ": %s\n", c.Q)
	}
	return strings.TrimRight(b.String(), "\n"), false
}

func (s *server) search(ctx context.Context, args map[string]any) (string, bool) {
	q, _ := strArg(args, "query")
	if strings.TrimSpace(q) == "" {
		return "query must be a non-empty string", true
	}
	kind, bad := kindArg(args, false)
	if bad != "" {
		return bad, true
	}
	var out struct {
		Hits []struct {
			RepoID  string  `json:"repo_id"`
			Path    string  `json:"path"`
			Kind    string  `json:"kind"`
			Snippet string  `json:"snippet"`
			Rank    float64 `json:"rank"`
		} `json:"hits"`
	}
	if msg := s.fetch(ctx, "/v1/search", map[string]string{"q": q, "kind": kind, "limit": "10"}, &out); msg != "" {
		return msg, false
	}
	if len(out.Hits) == 0 {
		return "no matches", false
	}
	var b strings.Builder
	for _, h := range out.Hits {
		fmt.Fprintf(&b, "%s %s:%s (rank %g)\n%s\n\n", h.Kind, h.RepoID, h.Path, h.Rank, h.Snippet)
	}
	return strings.TrimRight(b.String(), "\n"), false
}
