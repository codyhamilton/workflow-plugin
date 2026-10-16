package serve

import (
	"encoding/json"
	"net/http"
	"net/url"
	"time"
)

func validLoopbackRedirectURI(raw string) bool {
	if raw == "" {
		return false
	}
	u, err := url.Parse(raw)
	if err != nil || u.Scheme != "http" && u.Scheme != "https" {
		return false
	}
	return loopbackHost(u.Hostname())
}

func redirectWithDeviceCode(w http.ResponseWriter, r *http.Request, redirectURI, code, state string) {
	u, err := url.Parse(redirectURI)
	if err != nil {
		writeJSON(w, 500, map[string]string{"error": "internal error"})
		return
	}
	q := u.Query()
	q.Set("code", code)
	q.Set("state", state)
	u.RawQuery = q.Encode()
	http.Redirect(w, r, u.String(), http.StatusSeeOther)
}

func (s *Server) handleDeviceAuthorize(w http.ResponseWriter, r *http.Request, sess *Session) {
	var body struct {
		RedirectURI string `json:"redirect_uri"`
		State       string `json:"state"`
		Tenant      string `json:"tenant"`
		Scope       string `json:"scope"`
		ExpiresAt   string `json:"expires_at"`
	}
	if err := json.NewDecoder(r.Body).Decode(&body); err != nil {
		writeJSON(w, 400, map[string]string{"error": "invalid body"})
		return
	}
	if body.RedirectURI == "" || body.State == "" || body.Tenant == "" || body.Scope == "" || body.ExpiresAt == "" {
		writeJSON(w, 400, map[string]string{"error": "invalid body"})
		return
	}
	if !validLoopbackRedirectURI(body.RedirectURI) {
		writeJSON(w, 400, map[string]string{"error": "invalid redirect_uri"})
		return
	}
	exp, err := time.Parse(time.RFC3339, body.ExpiresAt)
	if err != nil {
		writeJSON(w, 400, map[string]string{"error": "invalid expires_at"})
		return
	}
	now := time.Now()
	code, _, err := s.registry.CreateDeviceAuthorization(body.Tenant, body.Scope, exp, sess.GitHubID, body.RedirectURI, body.State, now)
	if err != nil {
		if err.Error() == "forbidden tenant" {
			writeJSON(w, 403, map[string]string{"error": "forbidden"})
			return
		}
		writeJSON(w, 400, map[string]string{"error": err.Error()})
		return
	}
	if err := s.registry.Persist(); err != nil {
		writeJSON(w, 500, map[string]string{"error": "persist failed"})
		return
	}
	redirectWithDeviceCode(w, r, body.RedirectURI, code, body.State)
}

func (s *Server) handleDeviceExchange(w http.ResponseWriter, r *http.Request) {
	var body struct {
		Code        string `json:"code"`
		State       string `json:"state"`
		RedirectURI string `json:"redirect_uri"`
	}
	if err := json.NewDecoder(r.Body).Decode(&body); err != nil || body.Code == "" || body.State == "" || body.RedirectURI == "" {
		writeJSON(w, 400, map[string]string{"error": "invalid body"})
		return
	}
	if !validLoopbackRedirectURI(body.RedirectURI) {
		writeJSON(w, 401, map[string]string{"error": "unauthorized"})
		return
	}
	plain, ok := s.registry.ExchangeDeviceCode(body.Code, body.State, body.RedirectURI, time.Now())
	if !ok {
		writeJSON(w, 401, map[string]string{"error": "unauthorized"})
		return
	}
	if err := s.registry.Persist(); err != nil {
		writeJSON(w, 500, map[string]string{"error": "persist failed"})
		return
	}
	writeJSON(w, 200, map[string]string{
		"endpoint": s.publicOrigin(),
		"token":    plain,
	})
}

func (s *Server) handleDeviceAuthorizeRoute(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		w.Header().Set("Allow", http.MethodPost)
		writeJSON(w, 405, map[string]string{"error": "method not allowed"})
		return
	}
	if rejectBearer(w, r) {
		return
	}
	s.originGuard(s.sessionOnly(s.handleDeviceAuthorize))(w, r)
}

func (s *Server) handleDeviceExchangeRoute(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		w.Header().Set("Allow", http.MethodPost)
		writeJSON(w, 405, map[string]string{"error": "method not allowed"})
		return
	}
	s.handleDeviceExchange(w, r)
}
