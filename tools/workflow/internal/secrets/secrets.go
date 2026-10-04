// Package secrets holds the one pattern set shared by the client scrub and
// the server precheck (designs 1, 2 and 3). Standard library only.
package secrets

import (
	"regexp"
	"sort"
	"strings"
	"unicode/utf8"
)

// Hit is one pattern match. It never carries the matched text.
type Hit struct {
	Pattern string
	Line    int // 1-based
}

type pattern struct {
	name  string
	re    *regexp.Regexp
	group int                 // submatch checked by ok; 0 = none
	ok    func(v string) bool // false means placeholder: not a hit
}

var patterns = []pattern{
	{name: "private_key_block", re: regexp.MustCompile(`-----BEGIN [A-Z ]*PRIVATE KEY-----(?:[\s\S]*?-----END [A-Z ]*PRIVATE KEY-----)?`)},
	{name: "sk_key", re: regexp.MustCompile(`\bsk-[A-Za-z0-9_\-]{16,}`)},
	{name: "github_token", re: regexp.MustCompile(`\bgh[pousr]_[A-Za-z0-9]{20,}`)},
	{name: "github_pat", re: regexp.MustCompile(`\bgithub_pat_[A-Za-z0-9_]{20,}`)},
	{name: "aws_access_key", re: regexp.MustCompile(`\bAKIA[0-9A-Z]{16}\b`)},
	{name: "slack_token", re: regexp.MustCompile(`\bxox[abprs]-[A-Za-z0-9\-]{10,}`)},
	{name: "google_api_key", re: regexp.MustCompile(`\bAIza[0-9A-Za-z_\-]{35}`)},
	{name: "stripe_key", re: regexp.MustCompile(`\b[sr]k_live_[0-9A-Za-z]{16,}`)},
	{name: "jwt", re: regexp.MustCompile(`\beyJ[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{10,}`)},
	{name: "bearer_token", re: regexp.MustCompile(`(?i)\bbearer[ \t]+[A-Za-z0-9._~+/\-]{20,}=*`)},
	{name: "connection_string", re: regexp.MustCompile(`\b[A-Za-z][A-Za-z0-9+.\-]*://[^\s:/@]+:([^\s@/]+)@[^\s/]+`), group: 1, ok: func(v string) bool { return !placeholder(v, false) }},
	{name: "env_assignment", re: regexp.MustCompile(`(?i)[A-Za-z0-9_]*(?:KEY|SECRET|TOKEN|PASSWORD)["']?[ \t]*[=:][ \t]*["']?([^\s"']+)`), group: 1, ok: func(v string) bool { return !placeholder(v, true) }},
}

var xRun = regexp.MustCompile(`^[xX*.\-_]{3,}$`)

// placeholder reports whether v looks like a documentation placeholder.
func placeholder(v string, lengthRule bool) bool {
	if lengthRule && utf8.RuneCountInString(v) < 8 {
		return true
	}
	for _, p := range []string{"$", "<", "{", "…", "...", "*"} {
		if strings.HasPrefix(v, p) {
			return true
		}
	}
	if xRun.MatchString(v) || strings.HasPrefix(strings.ToLower(v), "xxxx") {
		return true
	}
	switch strings.ToLower(v) {
	case "password", "pass", "pwd", "secret", "changeme":
		return true
	}
	return false
}

type match struct {
	name       string
	start, end int
}

// matches returns non-overlapping matches in text order. On overlap the
// earlier (then longer) match wins.
func matches(text string) []match {
	var all []match
	for _, p := range patterns {
		for _, m := range p.re.FindAllStringSubmatchIndex(text, -1) {
			if p.ok != nil && m[2*p.group] >= 0 && !p.ok(text[m[2*p.group]:m[2*p.group+1]]) {
				continue
			}
			all = append(all, match{p.name, m[0], m[1]})
		}
	}
	sort.SliceStable(all, func(i, j int) bool {
		if all[i].start != all[j].start {
			return all[i].start < all[j].start
		}
		return all[i].end > all[j].end
	})
	var out []match
	for _, m := range all {
		if len(out) > 0 && m.start < out[len(out)-1].end {
			continue
		}
		out = append(out, m)
	}
	return out
}

// Scan returns every hit in text order.
func Scan(text string) []Hit {
	var hits []Hit
	for _, m := range matches(text) {
		hits = append(hits, Hit{m.name, 1 + strings.Count(text[:m.start], "\n")})
	}
	return hits
}

// Redact replaces each match with [REDACTED:<pattern>].
func Redact(text string) string {
	var b strings.Builder
	last := 0
	for _, m := range matches(text) {
		b.WriteString(text[last:m.start])
		b.WriteString("[REDACTED:" + m.name + "]")
		last = m.end
	}
	b.WriteString(text[last:])
	return b.String()
}

// Patterns returns the stable pattern names.
func Patterns() []string {
	names := make([]string, len(patterns))
	for i, p := range patterns {
		names[i] = p.name
	}
	return names
}
