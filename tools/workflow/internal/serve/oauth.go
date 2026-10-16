package serve

import (
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"net/url"
	"strings"
	"time"
)

type githubOAuth struct {
	authorizeURL string
	tokenURL     string
	apiBase      string
	clientID     string
	clientSecret string
	httpClient   *http.Client
}

func (s *Server) githubOAuth() *githubOAuth {
	base := strings.TrimSuffix(s.opts.GitHubHTTPBase, "/")
	g := &githubOAuth{
		clientID:     s.cfg.GitHubOAuthClientID,
		clientSecret: s.cfg.GitHubOAuthClientSecret,
		httpClient:   http.DefaultClient,
	}
	if base == "" {
		g.authorizeURL = "https://github.com/login/oauth/authorize"
		g.tokenURL = "https://github.com/login/oauth/access_token"
		g.apiBase = "https://api.github.com"
		return g
	}
	g.authorizeURL = base + "/login/oauth/authorize"
	g.tokenURL = base + "/login/oauth/access_token"
	g.apiBase = base + "/api"
	return g
}

func (s *Server) oauthLogin(w http.ResponseWriter, r *http.Request) {
	g := s.githubOAuth()
	state, err := newSessionID()
	if err != nil {
		writeJSON(w, 500, map[string]string{"error": "state failed"})
		return
	}
	http.SetCookie(w, &http.Cookie{
		Name:     oauthStateCookie,
		Value:    state,
		Path:     "/",
		HttpOnly: true,
		SameSite: http.SameSiteLaxMode,
		Secure:   s.sessionCookieSecure(),
		Expires:  time.Now().Add(oauthStateLifetime).UTC(),
	})
	redirectAfter := "/"
	if ret := r.URL.Query().Get("return"); ret != "" && strings.HasPrefix(ret, "/") && !strings.HasPrefix(ret, "//") {
		redirectAfter = ret
	}
	http.SetCookie(w, &http.Cookie{
		Name:     "workflow_oauth_return",
		Value:    redirectAfter,
		Path:     "/",
		HttpOnly: true,
		SameSite: http.SameSiteLaxMode,
		Secure:   s.sessionCookieSecure(),
		Expires:  time.Now().Add(oauthStateLifetime).UTC(),
	})
	q := url.Values{
		"client_id":    {g.clientID},
		"redirect_uri": {s.publicOrigin() + "/oauth/callback"},
		"scope":        {"read:user user:email"},
		"state":        {state},
	}
	http.Redirect(w, r, g.authorizeURL+"?"+q.Encode(), http.StatusFound)
}

func (s *Server) oauthCallback(w http.ResponseWriter, r *http.Request) {
	stateCookie, err := r.Cookie(oauthStateCookie)
	if err != nil || stateCookie.Value == "" || r.URL.Query().Get("state") != stateCookie.Value {
		http.Redirect(w, r, "/login", http.StatusFound)
		return
	}
	http.SetCookie(w, &http.Cookie{
		Name: oauthStateCookie, Value: "", Path: "/", HttpOnly: true, SameSite: http.SameSiteLaxMode,
		Secure: s.sessionCookieSecure(), MaxAge: -1,
	})
	code := r.URL.Query().Get("code")
	if code == "" {
		http.Redirect(w, r, "/login", http.StatusFound)
		return
	}
	g := s.githubOAuth()
	access, err := g.exchangeCode(r.Context(), code, s.publicOrigin()+"/oauth/callback")
	if err != nil {
		http.Redirect(w, r, "/login", http.StatusFound)
		return
	}
	user, emails, err := g.fetchIdentity(r.Context(), access)
	if err != nil {
		http.Redirect(w, r, "/login", http.StatusFound)
		return
	}
	verified := filterVerifiedEmails(emails)
	rec := SessionRecord{
		GitHubID:       user.ID,
		GitHubLogin:    user.Login,
		VerifiedEmails: verified,
		ExpiresAt:      time.Now().Add(sessionLifetime).UTC(),
	}
	if !admittedByPolicy(rec, s.registry.Policy()) {
		http.Redirect(w, r, "/login?error=denied", http.StatusFound)
		return
	}
	sid, err := newSessionID()
	if err != nil {
		http.Redirect(w, r, "/login", http.StatusFound)
		return
	}
	s.registry.PutSession(sid, rec)
	_ = s.registry.Persist()
	s.setSessionCookie(w, sid, rec.ExpiresAt)
	dest := "/"
	if ret, err := r.Cookie("workflow_oauth_return"); err == nil && ret.Value != "" {
		dest = ret.Value
	}
	http.SetCookie(w, &http.Cookie{
		Name: "workflow_oauth_return", Value: "", Path: "/", HttpOnly: true, SameSite: http.SameSiteLaxMode,
		Secure: s.sessionCookieSecure(), MaxAge: -1,
	})
	http.Redirect(w, r, dest, http.StatusFound)
}

func (s *Server) logout(w http.ResponseWriter, r *http.Request) {
	if c, err := r.Cookie(sessionCookieName); err == nil && c.Value != "" {
		s.registry.DeleteSession(c.Value)
		_ = s.registry.Persist()
	}
	s.clearSessionCookie(w)
	w.WriteHeader(http.StatusNoContent)
}

type ghUser struct {
	ID    int64  `json:"id"`
	Login string `json:"login"`
}

type ghEmail struct {
	Email    string `json:"email"`
	Verified bool   `json:"verified"`
}

func filterVerifiedEmails(in []ghEmail) []string {
	var out []string
	for _, e := range in {
		if e.Verified && e.Email != "" {
			out = append(out, e.Email)
		}
	}
	return out
}

func (g *githubOAuth) exchangeCode(ctx context.Context, code, redirectURI string) (string, error) {
	body := url.Values{
		"client_id":     {g.clientID},
		"client_secret": {g.clientSecret},
		"code":          {code},
		"redirect_uri":  {redirectURI},
	}
	req, err := http.NewRequestWithContext(ctx, http.MethodPost, g.tokenURL, strings.NewReader(body.Encode()))
	if err != nil {
		return "", err
	}
	req.Header.Set("Content-Type", "application/x-www-form-urlencoded")
	req.Header.Set("Accept", "application/json")
	resp, err := g.httpClient.Do(req)
	if err != nil {
		return "", err
	}
	defer resp.Body.Close()
	if resp.StatusCode != http.StatusOK {
		return "", fmt.Errorf("token exchange: %s", resp.Status)
	}
	var tok struct {
		AccessToken string `json:"access_token"`
	}
	if err := json.NewDecoder(resp.Body).Decode(&tok); err != nil {
		return "", err
	}
	if tok.AccessToken == "" {
		return "", fmt.Errorf("empty access token")
	}
	return tok.AccessToken, nil
}

func (g *githubOAuth) fetchIdentity(ctx context.Context, access string) (ghUser, []ghEmail, error) {
	var user ghUser
	if err := g.getJSON(ctx, g.apiBase+"/user", access, &user); err != nil {
		return ghUser{}, nil, err
	}
	var emails []ghEmail
	if err := g.getJSON(ctx, g.apiBase+"/user/emails", access, &emails); err != nil {
		return ghUser{}, nil, err
	}
	return user, emails, nil
}

func (g *githubOAuth) getJSON(ctx context.Context, url string, access string, dest any) error {
	req, err := http.NewRequestWithContext(ctx, http.MethodGet, url, nil)
	if err != nil {
		return err
	}
	req.Header.Set("Authorization", "Bearer "+access)
	req.Header.Set("Accept", "application/vnd.github+json")
	resp, err := g.httpClient.Do(req)
	if err != nil {
		return err
	}
	defer resp.Body.Close()
	if resp.StatusCode != http.StatusOK {
		b, _ := io.ReadAll(io.LimitReader(resp.Body, 256))
		return fmt.Errorf("github api %s: %s", resp.Status, strings.TrimSpace(string(b)))
	}
	return json.NewDecoder(resp.Body).Decode(dest)
}
