package main

import (
	"encoding/json"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"regexp"
	"syscall"
	"time"
)

var convSanitize = regexp.MustCompile(`[^A-Za-z0-9._-]`)

func conversationID(payload map[string]any) string {
	for _, k := range []string{"session_id", "conversation_id", "sessionID"} {
		if v, ok := payload[k]; ok {
			if s, ok := v.(string); ok && s != "" {
				return convSanitize.ReplaceAllString(s, "_")
			}
		}
	}
	return ""
}

// writeSpool enqueues one hook event like hooklog/spool.sh (without calling the shell script).
// When kick is true it starts a detached drain; kickBin empty uses the test wrapper.
func (e *env) writeSpool(harness, event string, payload map[string]any, kick bool, kickBin string, kickEnv []string) error {
	if harness == "" || harness == "auto" {
		return nil
	}
	id := conversationID(payload)
	if id == "" {
		return nil
	}
	if err := os.MkdirAll(filepath.Join(e.queue, "tmp"), 0o700); err != nil {
		return err
	}
	ts := float64(time.Now().UnixNano()) / 1e9
	body, err := json.Marshal(payload)
	if err != nil {
		return err
	}
	inner := fmt.Sprintf("{\"ts\":%g,\"harness\":\"%s\",\"event\":\"%s\"}\n%s\n", ts, harness, event, body)
	tmp := filepath.Join(e.queue, "tmp", fmt.Sprintf("%d-%d", time.Now().UnixNano(), os.Getpid()))
	if err := os.WriteFile(tmp, []byte(inner), 0o600); err != nil {
		return err
	}
	name := fmt.Sprintf("%s-%g-%d-%d.evt", id, ts, os.Getpid(), time.Now().UnixNano()%1e6)
	if err := os.Rename(tmp, filepath.Join(e.queue, name)); err != nil {
		return err
	}
	if kick {
		return e.kickDrain(kickBin, kickEnv)
	}
	return nil
}

func queueLockHeld(queue string) bool {
	f, err := os.OpenFile(filepath.Join(queue, ".drain.lock"), os.O_RDWR, 0)
	if err != nil {
		return false
	}
	defer f.Close()
	if err := syscall.Flock(int(f.Fd()), syscall.LOCK_EX|syscall.LOCK_NB); err != nil {
		return true
	}
	syscall.Flock(int(f.Fd()), syscall.LOCK_UN)
	return false
}

func (e *env) kickDrain(kickBin string, env []string) error {
	if queueLockHeld(e.queue) {
		return nil
	}
	bin := kickBin
	if bin == "" {
		bin = e.wrapper
	}
	if fi, err := os.Stat(bin); err != nil || fi.Mode()&0111 == 0 {
		return nil
	}
	if env == nil {
		env = e.base
	}
	cmd := exec.Command(bin, "drain")
	cmd.Env = env
	cmd.Stdin = nil
	if err := cmd.Start(); err != nil {
		return err
	}
	go cmd.Wait()
	return nil
}
