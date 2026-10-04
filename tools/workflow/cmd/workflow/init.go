package main

import (
	"crypto/rand"
	"encoding/hex"
	"errors"
	"fmt"
	"io/fs"
	"os"
	"path/filepath"

	"github.com/codyhamilton/workflow-plugin/tools/workflow/internal/clientconfig"
)

// runInit sets up local mode once (design 5, Local bootstrap). It never runs systemctl or any other
// process, never writes TYPESAFE_API_KEY, and never prints the key.
func runInit(args []string) int {
	if len(args) > 0 {
		fmt.Fprint(os.Stderr, "usage: workflow init (no arguments)\n")
		return 2
	}
	root := os.Getenv("WORKFLOW_ROOT")
	if root == "" {
		fmt.Fprintln(os.Stderr, "workflow init: WORKFLOW_ROOT unset; run it through bin/workflow")
		return 2
	}
	home := os.Getenv("HOME")
	if home == "" {
		fmt.Fprintln(os.Stderr, "workflow init: HOME unset")
		return 2
	}
	if err := doInit(root, home); err != nil {
		fmt.Fprintln(os.Stderr, "workflow init:", err)
		return 1
	}
	return 0
}

func exists(p string) bool {
	_, err := os.Stat(p)
	return err == nil || !errors.Is(err, fs.ErrNotExist)
}

// writeNew writes content at path (dirs 0700, file 0600) unless it exists, and reports which.
func writeNew(path, content string) error {
	if exists(path) {
		fmt.Printf("kept   %s\n", path)
		return nil
	}
	dir := filepath.Dir(path)
	if err := os.MkdirAll(dir, 0o700); err != nil {
		return err
	}
	if err := os.WriteFile(path, []byte(content), 0o600); err != nil {
		return err
	}
	if err := os.Chmod(path, 0o600); err != nil {
		return err
	}
	fmt.Printf("wrote  %s\n", path)
	return nil
}

func doInit(root, home string) error {
	cfgPath := clientconfig.Path()
	envPath := filepath.Join(home, ".config", "workflow", "serve.env")
	secretsPath := filepath.Join(filepath.Dir(envPath), "serve.secrets.env")
	unitPath := filepath.Join(home, ".config", "systemd", "user", "workflow-serve.service")

	var key string
	if exists(cfgPath) {
		c, err := clientconfig.Load()
		if err != nil {
			return fmt.Errorf("read client config: %w", err)
		}
		key = c.Key
	} else {
		b := make([]byte, 32)
		if _, err := rand.Read(b); err != nil {
			return err
		}
		key = hex.EncodeToString(b)
	}
	if key == "" {
		return errors.New("client config has no key")
	}
	if err := writeNew(cfgPath, "endpoint = \"http://127.0.0.1:8770\"\nkey = \""+key+"\"\n"); err != nil {
		return err
	}
	if err := writeNew(envPath, "WORKFLOW_SERVE_KEYS=local="+key+"\nWORKFLOW_CHECKS_DIR="+root+"/tools/quality\n"); err != nil {
		return err
	}
	unit := "[Unit]\nDescription=workflow serve (local)\n\n[Service]\n" +
		"EnvironmentFile=" + envPath + "\nEnvironmentFile=-" + secretsPath + "\n" +
		"ExecStart=" + root + "/bin/workflow serve\nRestart=on-failure\n\n[Install]\nWantedBy=default.target\n"
	if err := writeNew(unitPath, unit); err != nil {
		return err
	}
	fmt.Printf("\nTo enable screening, create %s (mode 0600) holding TYPESAFE_API_KEY=...\n", secretsPath)
	fmt.Println("Nothing is enabled or started. To enable the local service, run:")
	fmt.Println("systemctl --user daemon-reload && systemctl --user enable --now workflow-serve.service")
	return nil
}
