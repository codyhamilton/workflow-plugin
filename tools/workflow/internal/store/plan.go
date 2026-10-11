package store

// PlanOf returns the <plan> segment of a kind path (docs/plans/<plan>/...), or "" when p has no
// kind. It is the exported form of planOf for the offline compaction engine.
func PlanOf(p string) string { return planOf(p) }
