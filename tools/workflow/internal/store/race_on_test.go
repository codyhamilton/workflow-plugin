//go:build race

package store

// raceEnabled is true under the race detector; timing assertions are relaxed there.
const raceEnabled = true
