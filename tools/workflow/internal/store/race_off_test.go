//go:build !race

package store

// raceEnabled is false in normal runs; timing assertions apply.
const raceEnabled = false
