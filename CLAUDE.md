# FortNet: Fortnite placement forecasting

Forecast pro Fortnite placements at Majors/LANs from replay telemetry and results history, and test whether age adds signal beyond fight skill, reaction latency, tenure, cohort and era.

## Read first

- `docs/architecture.md`: the modeling plan (Stages 1–3), leakage rules, **data splits**, evaluation gates, Decisions table.
- `docs/data_sourcing.md`: where data comes from, the ingest procedure, quality gates, privacy.
- `docs/data_schema.md`: every table and column. Generated; edit `src/fnf/schema.py`, then run `uv run fnf-schema-doc`.
- `docs/handoffs/`: scoped plans for parallel workstreams (one branch each). If your prompt names one, it is your plan.

## Commands

```bash
uv sync
export PATH="/c/Program Files/dotnet:$PATH"        # Git Bash on this machine; .NET 10 SDK
dotnet build ingest/ReplayExport -c Release
uv run fnf-import [folder] [--source ... --kind ...]   # copy replays + provenance manifest
dotnet run --project ingest/ReplayExport -c Release --no-build   # per-replay CSVs (--force to redo)
uv run fnf-build-tables                             # typed parquet tables, schema-validated
uv run fnf-validate && uv run fnf-quality           # schema check + quality gates
uv run pytest
```

In a git worktree, `data/` doesn't exist (it's git-ignored). Point both the Python package and the exporter at the main checkout's data:
`export FNF_DATA_DIR="<absolute path to the main checkout>/data"` (`git worktree list` shows the main checkout). Treat `data/raw` as shared and append-only. If two sessions run `fnf-build-tables` at once, they overwrite each other's `data/processed`, so coordinate, or give a session its own copy of `data/processed` work.

## Rules

- **Schema first.** Any new or changed table/column goes in `src/fnf/schema.py` (and the doc is regenerated) in the same change. `fnf-build-tables` refuses to write tables that don't validate.
- **Splits come from `src/fnf/splits.py`**, never ad hoc. No random splits. Changing a split is a Decisions-table entry plus a salt version bump.
- **No leakage.** Features for an event use only data before it, and fight-model features use only data before `t0`. Fight models never see player identity. Residual features are out-of-fold.
- **Data never leaves `data/`** (git-ignored): account IDs, names, minors. Commit code and docs only.
- **Excluded data sources:** don't call unofficial Epic endpoints with embedded game-client credentials (e.g. `fortnite-replay-downloader`), and don't scrape against a site's terms. See data_sourcing.md 2.6.
- **New data or a new game build:** run `fnf-quality` and record results in the data_sourcing.md Changelog. New `PBWA_*` shapes go in `ingest/gen_build_pieces.py` (then regenerate, rebuild, re-export).

## Gotchas

- The exporter's assembly must be named `ReplayExport.ReplayReader`: FortniteReplayReader only loads export groups from assemblies whose name contains "ReplayReader".
- 2026 builds never replicate the game-state clock. All times use the demo frame clock (`t`, seconds since replay start).
- Client replays only cover what was near the recorder; `health` is recorder-only. Piece owner/editor fields are empty, so builders are inferred (`pieces.builder_source`).
