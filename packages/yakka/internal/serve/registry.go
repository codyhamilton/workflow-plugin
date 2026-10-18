package serve

import (
	"crypto/rand"
	"crypto/sha256"
	"crypto/subtle"
	"encoding/base64"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"sync"
	"time"
)

// Registry persistence lives directly under YAKKA_SERVE_DATA (not inside a tenant directory):
//
//	<data>/registry.json — versioned JSON document with domain policy, sessions, and reserved
//	slots for tenant owners and issued token hashes (phase 2).
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
	GitHubID       int64     `json:"github_id"`
	GitHubLogin    string    `json:"github_login"`
	VerifiedEmails []string  `json:"verified_emails"`
	ExpiresAt      time.Time `json:"expires_at"`
}

const (
	TokenScopeRead      = "read"
	TokenScopeReadWrite = "read_write"
)

// TokenHashRecord is one issued API token (SHA-256 of plaintext stored; plaintext never persisted).
type TokenHashRecord struct {
	ID        string    `json:"id"`
	Tenant    string    `json:"tenant"`
	Scope     string    `json:"scope"`
	Hash      string    `json:"hash"`
	GitHubID  int64     `json:"github_id"`
	ExpiresAt time.Time `json:"expires_at"`
	Revoked   bool      `json:"revoked"`
	CreatedAt time.Time `json:"created_at"`
}

// CreatedToken is returned once when a token is issued (includes plaintext).
type CreatedToken struct {
	Record    TokenHashRecord
	Plaintext string
}

// DeviceCodeRecord binds a one-time device code to an issued token until exchange.
type DeviceCodeRecord struct {
	CodeHash       string    `json:"code_hash"`
	TokenID        string    `json:"token_id"`
	TokenPlaintext string    `json:"token_plaintext"`
	RedirectURI    string    `json:"redirect_uri"`
	State          string    `json:"state"`
	ExpiresAt      time.Time `json:"expires_at"`
}

// registryDoc is the on-disk shape of registry.json.
type registryDoc struct {
	Version     int                      `json:"version"`
	Policy      DomainPolicy             `json:"policy"`
	Sessions    map[string]SessionRecord `json:"sessions"`
	Owners      map[string]string        `json:"owners"`
	TokenHashes []TokenHashRecord        `json:"token_hashes"`
	DeviceCodes []DeviceCodeRecord       `json:"device_codes,omitempty"`
}

// Registry holds collector-wide state outside tenant directories.
type Registry struct {
	mu   sync.RWMutex
	path string

	policy      DomainPolicy
	sessions    map[string]SessionRecord
	owners      map[string]string
	tokenHashes []TokenHashRecord
	deviceCodes []DeviceCodeRecord
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
	r.deviceCodes = doc.DeviceCodes
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
		DeviceCodes: r.deviceCodes,
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

func hashTokenPlaintext(plaintext string) string {
	h := sha256.Sum256([]byte(plaintext))
	return hex.EncodeToString(h[:])
}

func generateTokenPlaintext() (string, error) {
	var b [32]byte
	if _, err := rand.Read(b[:]); err != nil {
		return "", err
	}
	return "wk_" + base64.RawURLEncoding.EncodeToString(b[:]), nil
}

func newTokenID() (string, error) {
	var b [16]byte
	if _, err := rand.Read(b[:]); err != nil {
		return "", err
	}
	return hex.EncodeToString(b[:]), nil
}

// CreateTenant registers name for githubID. Returns false when the name is taken.
func (r *Registry) CreateTenant(name string, githubID int64) bool {
	owner := fmt.Sprintf("%d", githubID)
	r.mu.Lock()
	defer r.mu.Unlock()
	if r.owners[name] != "" {
		return false
	}
	r.owners[name] = owner
	r.dirty = true
	return true
}

// CreateToken issues a token for tenant owned by githubID. Returns nil on validation or ownership failure.
func (r *Registry) CreateToken(tenant, scope string, expiresAt time.Time, githubID int64, now time.Time) (*CreatedToken, error) {
	if scope != TokenScopeRead && scope != TokenScopeReadWrite {
		return nil, fmt.Errorf("invalid scope")
	}
	if !expiresAt.After(now) {
		return nil, fmt.Errorf("expires_at must be in the future")
	}
	owner := fmt.Sprintf("%d", githubID)
	r.mu.Lock()
	defer r.mu.Unlock()
	if r.owners[tenant] != owner {
		return nil, fmt.Errorf("forbidden tenant")
	}
	id, err := newTokenID()
	if err != nil {
		return nil, err
	}
	plain, err := generateTokenPlaintext()
	if err != nil {
		return nil, err
	}
	rec := TokenHashRecord{
		ID:        id,
		Tenant:    tenant,
		Scope:     scope,
		Hash:      hashTokenPlaintext(plain),
		GitHubID:  githubID,
		ExpiresAt: expiresAt.UTC(),
		CreatedAt: now.UTC(),
	}
	r.tokenHashes = append(r.tokenHashes, rec)
	r.dirty = true
	return &CreatedToken{Record: rec, Plaintext: plain}, nil
}

func generateDeviceCode() (string, error) {
	var b [32]byte
	if _, err := rand.Read(b[:]); err != nil {
		return "", err
	}
	return base64.RawURLEncoding.EncodeToString(b[:]), nil
}

func hashDeviceCode(code string) string {
	return hashTokenPlaintext(code)
}

// CreateDeviceAuthorization issues a token and stores a one-time device code for loopback exchange.
func (r *Registry) CreateDeviceAuthorization(tenant, scope string, expiresAt time.Time, githubID int64, redirectURI, state string, now time.Time) (code string, created *CreatedToken, err error) {
	created, err = r.CreateToken(tenant, scope, expiresAt, githubID, now)
	if err != nil {
		return "", nil, err
	}
	code, err = generateDeviceCode()
	if err != nil {
		return "", nil, err
	}
	rec := DeviceCodeRecord{
		CodeHash:       hashDeviceCode(code),
		TokenID:        created.Record.ID,
		TokenPlaintext: created.Plaintext,
		RedirectURI:    redirectURI,
		State:          state,
		ExpiresAt:      created.Record.ExpiresAt,
	}
	r.mu.Lock()
	r.deviceCodes = append(r.deviceCodes, rec)
	r.dirty = true
	r.mu.Unlock()
	return code, created, nil
}

// ExchangeDeviceCode consumes a device code once and returns the issued token plaintext.
func (r *Registry) ExchangeDeviceCode(code, state, redirectURI string, now time.Time) (plaintext string, ok bool) {
	kh := sha256.Sum256([]byte(code))
	r.mu.Lock()
	defer r.mu.Unlock()
	var idx = -1
	var found *DeviceCodeRecord
	match := 0
	for i := range r.deviceCodes {
		rec := &r.deviceCodes[i]
		ph, err := hex.DecodeString(rec.CodeHash)
		if err != nil || len(ph) != sha256.Size {
			continue
		}
		eq := subtle.ConstantTimeCompare(kh[:], ph)
		if eq == 1 {
			found = rec
			idx = i
		}
		match |= eq
	}
	if match != 1 || found == nil {
		return "", false
	}
	if found.State != state || found.RedirectURI != redirectURI {
		return "", false
	}
	if !now.Before(found.ExpiresAt) {
		r.deviceCodes = append(r.deviceCodes[:idx], r.deviceCodes[idx+1:]...)
		r.dirty = true
		return "", false
	}
	plaintext = found.TokenPlaintext
	r.deviceCodes = append(r.deviceCodes[:idx], r.deviceCodes[idx+1:]...)
	r.dirty = true
	return plaintext, true
}

// ListTokensForOwner returns tokens whose tenant is owned by githubID.
func (r *Registry) ListTokensForOwner(githubID int64) []TokenHashRecord {
	r.mu.RLock()
	defer r.mu.RUnlock()
	owner := fmt.Sprintf("%d", githubID)
	var out []TokenHashRecord
	for _, rec := range r.tokenHashes {
		if r.owners[rec.Tenant] == owner {
			out = append(out, rec)
		}
	}
	return out
}

// ListAllTokens returns every token record.
func (r *Registry) ListAllTokens() []TokenHashRecord {
	r.mu.RLock()
	defer r.mu.RUnlock()
	out := make([]TokenHashRecord, len(r.tokenHashes))
	copy(out, r.tokenHashes)
	return out
}

// RevokeToken marks a token revoked. Returns (found, alreadyRevoked).
func (r *Registry) RevokeToken(id string) (bool, bool) {
	r.mu.Lock()
	defer r.mu.Unlock()
	for i := range r.tokenHashes {
		if r.tokenHashes[i].ID != id {
			continue
		}
		if r.tokenHashes[i].Revoked {
			return true, true
		}
		r.tokenHashes[i].Revoked = true
		r.dirty = true
		return true, false
	}
	return false, false
}

// TokenByID returns one token by id.
func (r *Registry) TokenByID(id string) (TokenHashRecord, bool) {
	r.mu.RLock()
	defer r.mu.RUnlock()
	for _, rec := range r.tokenHashes {
		if rec.ID == id {
			return rec, true
		}
	}
	return TokenHashRecord{}, false
}

// resolveBearer maps a plaintext bearer to tenant and scope. Expired and revoked tokens do not match.
func (r *Registry) resolveBearer(plaintext string, now time.Time) (tenant, scope string, ok bool) {
	kh := sha256.Sum256([]byte(plaintext))
	r.mu.RLock()
	defer r.mu.RUnlock()
	var found *TokenHashRecord
	match := 0
	for i := range r.tokenHashes {
		rec := &r.tokenHashes[i]
		ph, err := hex.DecodeString(rec.Hash)
		if err != nil || len(ph) != sha256.Size {
			continue
		}
		eq := subtle.ConstantTimeCompare(kh[:], ph)
		if eq == 1 {
			found = rec
		}
		match |= eq
	}
	if match != 1 || found == nil {
		return "", "", false
	}
	if found.Revoked || !now.Before(found.ExpiresAt) {
		return "", "", false
	}
	return found.Tenant, found.Scope, true
}
