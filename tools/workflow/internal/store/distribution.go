package store

import (
	"context"
	"math"
	"sort"
)

// DistributionParams selects measure, grain, optional model dimension, and top-N keys.
type DistributionParams struct {
	Measure string
	Grain   string // "call" or "conversation"
	Dim     string // "" or "model"
	Top     int
}

// DistributionBin is one histogram bucket; Hi is omitted on the overflow bucket.
type DistributionBin struct {
	Lo float64  `json:"lo"`
	Hi *float64 `json:"hi,omitempty"`
	N  int      `json:"n"`
}

// DistributionRow is one dimension key's summary.
type DistributionRow struct {
	K        string            `json:"k"`
	N        int               `json:"n"`
	Unpriced int               `json:"unpriced"`
	Min      float64           `json:"min"`
	P25      float64           `json:"p25"`
	Median   float64           `json:"median"`
	P75      float64           `json:"p75"`
	P95      float64           `json:"p95"`
	Max      float64           `json:"max"`
	Bins     []DistributionBin `json:"bins"`
}

// DistributionResult is the store output for GET /v1/analytics/distribution.
type DistributionResult struct {
	Measure        string
	Grain          string
	Dim            string
	Rows           []DistributionRow
	Truncated      bool
	IgnoredFilters []string
}

type distSample struct {
	key           string
	value         float64
	priced        bool
	unpricedCalls int
}

func distributionApplyFilters(f AnalyticsFilter) (AnalyticsFilter, []string) {
	def, _ := measureByName("cost_usd")
	return def.applyFilters(f)
}

func (t *Tenant) Distribution(ctx context.Context, f AnalyticsFilter, p DistributionParams) (DistributionResult, error) {
	f2, ignored := distributionApplyFilters(f)
	rows, err := t.usageKeptRows(ctx, f2)
	if err != nil {
		return DistributionResult{}, err
	}
	samples := distSamplesFromCalls(rows, p)
	res := DistributionResult{
		Measure: p.Measure, Grain: p.Grain, Dim: p.Dim,
		IgnoredFilters: ignored,
	}
	groups := map[string]*distGroup{}
	for _, s := range samples {
		g := groups[s.key]
		if g == nil {
			g = &distGroup{key: s.key}
			groups[s.key] = g
		}
		g.add(p.Measure, s.value, s.priced, s.unpricedCalls)
	}
	keys := make([]string, 0, len(groups))
	for k := range groups {
		keys = append(keys, k)
	}
	sort.Slice(keys, func(i, j int) bool {
		ni, nj := groups[keys[i]].n, groups[keys[j]].n
		if ni != nj {
			return ni > nj
		}
		return keys[i] < keys[j]
	})
	top := p.Top
	if top <= 0 {
		top = 20
	}
	if top > 100 {
		top = 100
	}
	if len(keys) > top {
		res.Truncated = true
		keys = keys[:top]
	}
	for _, k := range keys {
		res.Rows = append(res.Rows, groups[k].row(p.Measure))
	}
	return res, nil
}

type distGroup struct {
	key         string
	n, unpriced int
	values      []float64
	bins        []DistributionBin
}

func (g *distGroup) add(measure string, value float64, priced bool, unpricedCalls int) {
	g.unpriced += unpricedCalls
	if measure == "cost_usd" {
		if priced {
			g.n++
			g.values = append(g.values, value)
			assignBin(&g.bins, measure, value)
		} else if unpricedCalls == 0 {
			g.unpriced++
		}
		return
	}
	if priced {
		g.n++
		g.values = append(g.values, value)
		assignBin(&g.bins, measure, value)
	}
}

func (g *distGroup) row(measure string) DistributionRow {
	sort.Float64s(g.values)
	round := func(v float64) float64 { return roundMeasure(measure, v) }
	r := DistributionRow{
		K: g.key, N: g.n, Unpriced: g.unpriced,
		Min: round(Percentile(g.values, 0)), P25: round(Percentile(g.values, 0.25)),
		Median: round(Percentile(g.values, 0.5)), P75: round(Percentile(g.values, 0.75)),
		P95: round(Percentile(g.values, 0.95)), Max: round(Percentile(g.values, 1)),
		Bins: binCounts(measure, g.bins),
	}
	return r
}

func distSamplesFromCalls(rows []usageRow, p DistributionParams) []distSample {
	if p.Grain == "conversation" {
		return distConversationSamples(rows, p)
	}
	out := make([]distSample, 0, len(rows))
	for _, r := range rows {
		val, priced := distCallValue(p.Measure, r)
		key := "all"
		if p.Dim == "model" {
			key = r.model
		}
		out = append(out, distSample{key: key, value: val, priced: priced})
	}
	return out
}

func distCallValue(measure string, r usageRow) (float64, bool) {
	if measure == "cost_usd" {
		usd, ok := Cost(r.harness, r.model, r.tokens(), r.costReported)
		return usd, ok
	}
	return usageValue(measure, r), true
}

func distConversationSamples(rows []usageRow, p DistributionParams) []distSample {
	type acc struct {
		sum         float64
		priced, unp int
		models      map[string]int
	}
	m := map[string]*acc{}
	for _, r := range rows {
		a := m[r.convID]
		if a == nil {
			a = &acc{models: map[string]int{}}
			m[r.convID] = a
		}
		val, priced := distCallValue(p.Measure, r)
		if priced {
			a.sum += val
			a.priced++
		} else {
			a.unp++
		}
		if r.model != "" {
			a.models[r.model]++
		}
	}
	out := make([]distSample, 0, len(m))
	for _, a := range m {
		key := "all"
		if p.Dim == "model" {
			key = dominantModel(a.models)
		}
		if a.priced > 0 {
			out = append(out, distSample{key: key, value: a.sum, priced: true, unpricedCalls: a.unp})
		} else if a.unp > 0 {
			out = append(out, distSample{key: key, unpricedCalls: a.unp})
		}
	}
	return out
}

func dominantModel(counts map[string]int) string {
	best, n := "", 0
	for name, c := range counts {
		if c > n || (c == n && (best == "" || name < best)) {
			best, n = name, c
		}
	}
	return best
}

func distributionBinDefs(measure string) []DistributionBin {
	if measure == "cost_usd" {
		defs := []DistributionBin{{Lo: 0}, {Lo: 0, Hi: f64(1e-4)}}
		for i := -4; i <= 1; i++ {
			lo := math.Pow(10, float64(i))
			hi := math.Pow(10, float64(i+1))
			defs = append(defs, DistributionBin{Lo: lo, Hi: &hi})
		}
		defs = append(defs, DistributionBin{Lo: 100})
		return defs
	}
	defs := []DistributionBin{{Lo: 0}}
	for i := 0; i < 20; i++ {
		lo := math.Pow(2, float64(i))
		hi := math.Pow(2, float64(i+1))
		defs = append(defs, DistributionBin{Lo: lo, Hi: &hi})
	}
	defs = append(defs, DistributionBin{Lo: math.Pow(2, 20)})
	return defs
}

func f64(v float64) *float64 { return &v }

func binIndex(measure string, v float64) int {
	if measure == "cost_usd" {
		if v == 0 {
			return 0
		}
		if v > 0 && v < 1e-4 {
			return 1
		}
		if v >= 100 {
			return 8
		}
		for i := -4; i <= 1; i++ {
			lo := math.Pow(10, float64(i))
			if v >= lo && v < math.Pow(10, float64(i+1)) {
				return i + 6 // zero, (0,1e-4), then i=-4 at index 2
			}
		}
		return 8
	}
	if v == 0 {
		return 0
	}
	if v >= math.Pow(2, 20) {
		return 21
	}
	if v > 0 && v < 1 {
		return 0
	}
	for i := 0; i < 20; i++ {
		lo := math.Pow(2, float64(i))
		if v >= lo && v < math.Pow(2, float64(i+1)) {
			return i + 1
		}
	}
	return 21
}

func assignBin(bins *[]DistributionBin, measure string, v float64) {
	if *bins == nil {
		*bins = distributionBinDefs(measure)
	}
	idx := binIndex(measure, v)
	(*bins)[idx].N++
}

func binCounts(measure string, partial []DistributionBin) []DistributionBin {
	defs := distributionBinDefs(measure)
	if len(partial) == 0 {
		return defs
	}
	for i := range defs {
		if i < len(partial) {
			defs[i].N = partial[i].N
		}
	}
	return defs
}
