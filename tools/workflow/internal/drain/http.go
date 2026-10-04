package drain

import (
	"bytes"
	"context"
	"encoding/json"
	"io"
	"net/http"
	"strconv"
	"strings"
	"time"

	"github.com/codyhamilton/workflow-plugin/tools/workflow/internal/clientconfig"
	"github.com/codyhamilton/workflow-plugin/tools/workflow/internal/ingest"
)

// HTTPSink POSTs to <Endpoint>/v1/ingest with the bearer key (none in local mode), 30 s timeout.
type HTTPSink struct {
	Endpoint string
	Key      string
	Client   *http.Client // default: 30 s timeout
}

func (s *HTTPSink) Send(ctx context.Context, facts []json.RawMessage) (Response, error) {
	body, err := json.Marshal(map[string]any{"facts": facts})
	if err != nil {
		return Response{}, err
	}
	req, err := http.NewRequestWithContext(ctx, http.MethodPost, strings.TrimRight(s.Endpoint, "/")+"/v1/ingest", bytes.NewReader(body))
	if err != nil {
		return Response{}, err
	}
	req.Header.Set("Content-Type", "application/json")
	if s.Key != "" {
		req.Header.Set("Authorization", "Bearer "+s.Key)
	}
	c := s.Client
	if c == nil {
		c = &http.Client{Timeout: 30 * time.Second}
	}
	resp, err := c.Do(req)
	if err != nil {
		return Response{}, errNetwork // never carry the URL or key in a message
	}
	defer resp.Body.Close()
	out := Response{Status: resp.StatusCode}
	if n, err := strconv.Atoi(strings.TrimSpace(resp.Header.Get("Retry-After"))); err == nil && n >= 0 {
		out.RetryAfter = time.Duration(n) * time.Second
	}
	data, err := io.ReadAll(io.LimitReader(resp.Body, 64<<20))
	if err != nil {
		return Response{}, errNetwork
	}
	if resp.StatusCode == 200 {
		var r struct {
			Results []ingest.Result `json:"results"`
		}
		if json.Unmarshal(data, &r) != nil {
			out.Status = 502 // a 200 we cannot read is retried
			return out, nil
		}
		out.Results = r.Results
	}
	return out, nil
}

type netErr struct{}

func (netErr) Error() string { return "network error" }

var errNetwork error = netErr{}

// ConfigSink builds an HTTPSink from a fresh clientconfig.Load.
func ConfigSink() (Sink, error) {
	c, err := clientconfig.Load()
	if err != nil {
		return nil, err
	}
	return &HTTPSink{Endpoint: c.Endpoint, Key: c.Key}, nil
}
