// Package clientconfig loads the one client config file the drain and the MCP shim share
// (design 2, Config): ~/.config/workflow/client.toml with `endpoint` and `key`. The file means
// remote mode and is written by `workflow login`; with no file the client is in local mode and
// talks to the keyless local service at LocalEndpoint.
//
// The path is $WORKFLOW_CLIENT_CONFIG when set (tests only), else $HOME/.config/workflow/client.toml.
// Only the subset design 2 shows is parsed: `name = "string"` lines, `#` comments and blank lines;
// unknown names are ignored; any other line is an error that names the line number, never its text.
// The key is never logged or placed in an error.
package clientconfig

import (
	"errors"
	"fmt"
	"os"
	"path/filepath"
	"regexp"
	"strconv"
	"strings"
)

// LocalEndpoint is where local mode sends, matching serve's default address.
const LocalEndpoint = "http://127.0.0.1:8770"

// Config is the parsed file, or the local default when there is none.
type Config struct {
	Endpoint string
	Key      string // empty in local mode
	Local    bool   // no config file: local mode
}

// Mode names the mode for status lines.
func (c Config) Mode() string {
	if c.Local {
		return "local"
	}
	return "remote"
}

var lineRE = regexp.MustCompile(`^([A-Za-z_][A-Za-z0-9_-]*)\s*=\s*("(?:[^"\\]|\\.)*")\s*(?:#.*)?$`)

// Path returns the config file path.
func Path() string {
	if p := os.Getenv("WORKFLOW_CLIENT_CONFIG"); p != "" {
		return p
	}
	home := os.Getenv("HOME")
	if home == "" {
		home, _ = os.UserHomeDir()
	}
	return filepath.Join(home, ".config", "workflow", "client.toml")
}

// Load reads and parses the config on every call, so edits need no restart. A missing file is
// local mode, not an error.
func Load() (Config, error) {
	path := Path()
	data, err := os.ReadFile(path)
	if err != nil {
		if errors.Is(err, os.ErrNotExist) {
			return Config{Endpoint: LocalEndpoint, Local: true}, nil
		}
		return Config{}, fmt.Errorf("clientconfig: read %s: %w", path, err)
	}
	return parse(path, string(data))
}

func parse(path, text string) (Config, error) {
	vals := map[string]string{}
	for i, line := range strings.Split(text, "\n") {
		line = strings.TrimSpace(line)
		if line == "" || strings.HasPrefix(line, "#") {
			continue
		}
		m := lineRE.FindStringSubmatch(line)
		if m == nil {
			return Config{}, fmt.Errorf("clientconfig: %s: line %d is not a `name = \"string\"` line", path, i+1)
		}
		v, err := strconv.Unquote(m[2])
		if err != nil {
			return Config{}, fmt.Errorf("clientconfig: %s: line %d has an invalid string", path, i+1)
		}
		vals[m[1]] = v
	}
	cfg := Config{Endpoint: vals["endpoint"], Key: vals["key"]}
	if cfg.Endpoint == "" {
		return Config{}, fmt.Errorf("clientconfig: %s: missing endpoint", path)
	}
	if cfg.Key == "" {
		return Config{}, fmt.Errorf("clientconfig: %s: missing key", path)
	}
	return cfg, nil
}
