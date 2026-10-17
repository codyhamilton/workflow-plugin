package store

import "math"

// Percentile is linear interpolation between closest ranks (position (n-1)*q) of sorted values,
// matching GET /v1/analytics/scores and baselines in serve.
func Percentile(sorted []float64, q float64) float64 {
	if len(sorted) == 0 {
		return 0
	}
	pos := float64(len(sorted)-1) * q
	lo := int(math.Floor(pos))
	hi := int(math.Ceil(pos))
	return sorted[lo] + (sorted[hi]-sorted[lo])*(pos-float64(lo))
}

func roundCost(v float64) float64 { return math.Round(v*1e6) / 1e6 }

func roundToken(v float64) float64 { return math.Round(v*10) / 10 }

func roundMeasure(measure string, v float64) float64 {
	if measure == "cost_usd" {
		return roundCost(v)
	}
	return roundToken(v)
}
