package serve

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"sync"
	"time"
)

// Registry persistence lives directly under WORKFLOW_SERVE_DATA (not inside a tenant directory):
//
//   <data>/registry.json — versioned JSON document with domain policy, sessions, and reserved
//   slots for tenant owners and issued token hashes (phase 2).
//
// Restart loads this file; a missing file means domain policy defaults to everyone and no sessions.
const registryFileName = "registry.json"

// DomainPolicyMode is the collector-wide admission mode.
const (
	PolicyEveryone  = "everyone"
	PolicyAllowList = "allow_list"
)

// DomainPolicy is the collector-wide domain admission record.
type DomainPolicy struct {
	Mode    string   `json:"mode"`
	Domains []string `json:"domains,omitempty"`
}

// SessionRecord is one logged-in session keyed by opaque session id.
type SessionRecord struct {
	GitHubID        int64     `json:"github_id"`
	GitHubLogin     string    `json:"github_login"`
	VerifiedEmails  []string  `json:"verified_emails"`
	ExpiresAt       time.Time `json:"expires_at"`
}

// TokenHashRecord is reserved for phase-2 issued API tokens (stored hashed, never plaintext).
type TokenHashRecord struct{}

// registryDoc is the on-disk shape of registry.json.
type registryDoc struct {
	Version     int               `json:"version"`
	Policy      DomainPolicy      `json:"policy"`
	Sessions    map[string]SessionRecord `json:"sessions"`
	Owners      map[string]string `json:"owners"`
	TokenHashes []TokenHashRecord `json:"token_hashes"`
}

// Registry holds collector-wide state outside tenant directories.
type Registry struct {
	mu   sync.RWMutex
	path string

	policy      DomainPolicy
	sessions    map[string]SessionRecord
	owners      map[string]string
	tokenHashes []TokenHashRecord
	dirty       bool
}

// OpenRegistry loads or creates registry state for dataDir.
func OpenRegistry(dataDir string) (*Registry, error) {
	r := &Registry{
		path:     filepath.Join(dataDir, registryFileName),
		policy:   DomainPolicy{Mode: PolicyEveryone},
		sessions: map[string]SessionRecord{},
		owners:   map[string]string{},
	}
	if err := r.load(); err != nil {
		return nil, err
	}
	return r, nil
}

func (r *Registry) load() error {
	b, err := os.ReadFile(r.path)
	if err != nil {
		if os.IsNotExist(err) {
			return nil
		}
		return err
	}
	var doc registryDoc
	if err := json.Unmarshal(b, &doc); err != nil {
		return fmt.Errorf("registry: invalid %s: %w", registryFileName, err)
	}
	if doc.Version != 1 {
		return fmt.Errorf("registry: unsupported version %d in %s", doc.Version, registryFileName)
	}
	if doc.Policy.Mode == "" {
		doc.Policy.Mode = PolicyEveryone
	}
	r.policy = doc.Policy
	if doc.Sessions != nil {
		r.sessions = doc.Sessions
	}
	if doc.Owners != nil {
		r.owners = doc.Owners
	}
	r.tokenHashes = doc.TokenHashes
	return nil
}

// Persist writes the registry if the data directory should hold a file (remote collector mode).
func (r *Registry) Persist() error {
	r.mu.Lock()
	defer r.mu.Unlock()
	return r.saveLocked()
}

func (r *Registry) saveLocked() error {
	doc := registryDoc{
		Version:     1,
		Policy:      r.policy,
		Sessions:    r.sessions,
		Owners:      r.owners,
		TokenHashes: r.tokenHashes,
	}
	b, err := json.MarshalIndent(doc, "", "  ")
	if err != nil {
		return err
	}
	tmp := r.path + ".tmp"
	if err := os.WriteFile(tmp, b, 0o600); err != nil {
		return err
	}
	if err := os.Rename(tmp, r.path); err != nil {
		_ = os.Remove(tmp)
		return err
	}
	r.dirty = false
	return nil
}

// Close flushes pending changes.
func (r *Registry) Close() error {
	r.mu.Lock()
	defer r.mu.Unlock()
	if !r.dirty {
		return nil
	}
	return r.saveLocked()
}

// Policy returns the current domain policy (default everyone when never set).
func (r *Registry) Policy() DomainPolicy {
	r.mu.RLock()
	defer r.mu.RUnlock()
	return r.policy
}

// SetPolicy updates domain policy and marks the registry dirty.
func (r *Registry) SetPolicy(p DomainPolicy) error {
	if p.Mode != PolicyEveryone && p.Mode != PolicyAllowList {
		return fmt.Errorf("registry: invalid policy mode %q", p.Mode)
	}
	if p.Mode == PolicyEveryone {
		p.Domains = nil
	}
	r.mu.Lock()
	r.policy = p
	r.dirty = true
	r.mu.Unlock()
	return nil
}

// GetSession returns one session by id, or false when missing or expired at now.
func (r *Registry) GetSession(id string, now time.Time) (SessionRecord, bool) {
	r.mu.RLock()
	rec, ok := r.sessions[id]
	r.mu.RUnlock()
	if !ok || !now.Before(rec.ExpiresAt) {
		return SessionRecord{}, false
	}
	return rec, true
}

// PutSession stores or replaces a session record.
func (r *Registry) PutSession(id string, rec SessionRecord) {
	r.mu.Lock()
	r.sessions[id] = rec
	r.dirty = true
	r.mu.Unlock()
}

// DeleteSession removes a session by id.
func (r *Registry) DeleteSession(id string) {
	r.mu.Lock()
	if _, ok := r.sessions[id]; ok {
		delete(r.sessions, id)
		r.dirty = true
	}
	r.mu.Unlock()
}

// RegistryPath reports the on-disk file path (tests).
func (r *Registry) RegistryPath() string { return r.path }
