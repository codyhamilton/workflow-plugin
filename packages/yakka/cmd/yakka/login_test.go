package main

import (
	"io"
	"os"
	"strings"
	"testing"
)

func TestLoginMovedToPluginWrapper(t *testing.T) {
	for _, args := range [][]string{{"login"}, {"login", "start"}, {"login", "--endpoint", "http://x"}} {
		r, w, err := os.Pipe()
		if err != nil {
			t.Fatal(err)
		}
		old := os.Stderr
		os.Stderr = w
		code := run(args)
		os.Stderr = old
		w.Close()
		out, _ := io.ReadAll(r)
		if code != 1 {
			t.Fatalf("%v: exit %d", args, code)
		}
		if !strings.Contains(string(out), "plugins/yakka/bin/yakka") {
			t.Fatalf("%v: message %q does not name the plugin wrapper", args, out)
		}
	}
}
