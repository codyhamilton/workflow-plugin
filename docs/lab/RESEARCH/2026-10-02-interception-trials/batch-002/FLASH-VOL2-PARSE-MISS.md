# Flash vol2 parse-miss glance (Soft HOLD)

**Status:** bounded diagnosis from the landed runner and repository artifacts.  
**Reported symptom:** Flash vol2 `parse_miss=10` (WSM report).  
**Soft Standard HOLD:** no hooks, behavior ship, or FP/miss product claim.

## Finding

The repository does not contain the vol2 meter, result rows, batch summary, or
raw stdout/stderr needed to identify a concrete failing response. The
originating raw directory is intentionally ignored by
[`batch-002/.gitignore`](.gitignore). Therefore the ten misses have **no
demonstrable root cause in landed evidence**.

What can be established from the runner:

1. [`run_flash_luna_volume.py`](run_flash_luna_volume.py) sets
   `CELLS_PER_FLASH = 10`.
2. [`run_batch002_multidriver.py`](run_batch002_multidriver.py)
   `write_results()` increments `parse_miss_cells` once for every planned cell
   with no answer in the aggregate `by_id` map.
3. `extract_json_array()` silently returns an empty or partial list when array
   decoding fails; its fallback accepts only complete one-object-per-line JSON.
4. `run_flash_batch()` writes raw prompt/stdout/stderr locally, but the
   persisted meters retain only the aggregate miss count. They do not retain
   expected IDs, parsed IDs, parser path, stdout size, or decode error.

Ten misses are thus **consistent with** one wholly unparsed ten-cell batch.
They do not prove that shape: ten absent or mismatched IDs could be distributed
across multiple partially parsed batches.

## Root-cause sample status

| Evidence needed | Landed? | What it would distinguish |
|---|---|---|
| `flash-hframings-vol2/raw/batch-NNN-stdout.txt` | No | Empty/truncated output, prose/fence shape, malformed JSON |
| matching `batch-NNN-stderr.txt` + exit code | No | Driver/process failure versus parser-only failure |
| expected and parsed cell IDs by batch | No | Whole-batch decode failure versus missing/wrong IDs |
| vol2 `results.jsonl` null-answer rows | No | Which cells are missing; not the parser cause by itself |
| vol2 `meters.json` / batch summaries | No | Denominator and distribution across batches |

Do not label any hypothetical malformed output as “the sample.” There is no
sample in git to support that claim.

## Plausible buckets, not findings

The current parser admits several failure modes:

- the model emits malformed or truncated array JSON;
- a response contains a code fence that is not the answer array selected by
  the first-fence regex;
- valid objects omit or alter `cell_id`, so parsing succeeds but `by_id` cannot
  join them;
- output is empty while the process exits zero;
- a batch is partially valid and the other objects are discarded.

No landed evidence chooses among these buckets.

## Smallest follow-up

Before the next Flash volume wave, persist a compact, non-prompt diagnostic
row per batch:

```json
{
  "batch_idx": 0,
  "exit_code": 0,
  "expected_cell_ids": ["..."],
  "parsed_cell_ids": ["..."],
  "stdout_bytes": 0,
  "parser_path": "array|jsonl|none",
  "decode_error_class": "none|json_decode|no_array|id_mismatch"
}
```

This sidecar is sufficient to localize misses without landing bulky prompts,
states, rationales, or raw output. Keep parse-miss rows out of response-rate
denominators and report them separately by batch and driver. A retry, if later
authorized, should target the exact missing IDs and preserve the original row
provenance.

## Non-authorization

This glance does not score Flash, infer an outcome for missing cells, alter
`window_status`, or authorize a runner/product behavior change.
