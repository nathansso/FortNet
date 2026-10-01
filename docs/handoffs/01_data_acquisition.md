# Handoff 01: data acquisition and results backbone

Branch: `data/results-backbone` (from `main`). Written 2026-10-01.

## Prompt to start the session

> You're picking up the data-acquisition workstream for the Fortnite placement forecasting project in this repo. Read `CLAUDE.md`, then `docs/handoffs/01_data_acquisition.md` (your plan), `docs/data_sourcing.md`, `docs/data_schema.md` and the "Data splits" and "Decisions" sections of `docs/architecture.md`. Work on branch `data/results-backbone`. If you're in a git worktree, set `FNF_DATA_DIR` as described in CLAUDE.md so you use the shared data. Follow the plan phase by phase. Start with Phase 1: send me all the "needs the user" questions in one message before fetching anything. Don't use unofficial Epic endpoints or anything listed as excluded in data_sourcing.md 2.6. Report at the end of each phase with what changed and what's next.

## Context

The replay pipeline works on local client replays (98 exported, quality gates pass). The forecaster needs two things that don't exist yet:
1. A **results backbone**: which competitive events happened, who placed where, and a stable identity for each player across sources.
2. **Career data**: birth dates and debut dates.

The schemas for these are already specified as *planned* tables in `src/fnf/schema.py`: `events`, `event_results`, `player_xref`, `player_meta`. Replay acquisition beyond local files also needs groundwork: the in-game tournament replay test, donated-replay intake, and partner outreach.

## Goal

Build `events`, `event_results`, `player_xref` and `player_meta` from sanctioned sources, with cached raw responses, rate limiting and a fetch log, so any session can rebuild them reproducibly. Prepare the replay-acquisition paths that need the user to act.

## Out of scope

- Modeling, fight segmentation (handoff 02), or changes to the replay exporter.
- **Unofficial Epic endpoints** (events service, replay datastorage) or any library that embeds a game-client credential. This is excluded in `docs/data_sourcing.md` 2.6; only the project owner can reverse it, as a recorded decision.
- Creating accounts, entering credentials, sending emails or messages on the user's behalf. Draft them for the user instead.
- Scraping HTML against a site's terms. Use documented APIs only.

## Constraints

- **Secrets:** API keys come from environment variables (`CITO_API_KEY`, `ESPORTS_EARNINGS_API_KEY`, `LIQUIPEDIA_API_KEY`), loaded from a git-ignored `.env`. Add `.env` to `.gitignore` before creating one. Keys never appear in logs, cache file names, the fetch log or commits.
- **Rate limits** (verify each against the source's current docs, and record the verified value in data_sourcing.md):
  - Liquipedia MediaWiki API: ≤ 60 requests/hour, ≤ 1 request per 2 s, `action=parse` ≤ 1 per 30 s. A custom User-Agent with contact info is required.
  - LPDB: per the key's tier.
  - Esports Earnings: ≤ 1 request/s.
  - Cito: per plan (free tier 500 requests/month).
- **Liquipedia licensing:** the free tier is for non-commercial or educational use *with the project's code open-sourced*. Content is CC-BY-SA, so attribution is required. Whether this repo will be public is the user's decision (Phase 1).
- **Privacy:** birth dates only where publicly published (Liquipedia infobox, Wikipedia), each with its source URL. Never infer an age. Many players are minors. All data stays under git-ignored `data/`.
- **Tests never touch the network.** Use recorded fixtures (trimmed, anonymized responses) under `tests/fixtures/`.
- **Schema first:** move tables from `status="planned"` to `"built"` in `src/fnf/schema.py` and add any new tables (e.g. `fetch_log`) there. Then run `uv run fnf-schema-doc` in the same change. Edit only your tables in schema.py, since handoff 02 edits `fight_sides`.

## Plan

### Phase 0: orient (no network)

1. Read the docs listed in the prompt, then run the full pipeline and `uv run fnf-quality` to confirm the environment (see CLAUDE.md for the `dotnet` PATH line).
2. Skim `docs/research/notes/data_and_prior_work.md` for what's known about each source.

### Phase 1: decisions that need the user (ask all at once, then wait)

1. **Liquipedia:** will the repo be open-sourced (required for the free tier)? If not, Liquipedia is limited to manual lookups with citations, and Cito becomes the backbone.
2. **Cito API:** will the user create an account and put `CITO_API_KEY` in `.env`? Which plan? The free tier is ~500 requests/month, which is likely too little for history.
3. **Esports Earnings:** key wanted? (Optional: earnings cross-check and identity hints.)
4. **Contact string for the User-Agent**, e.g. a project URL or email the user chooses.
5. **Forecast population and event scope.** Proposed default: FNCS Majors, FNCS Global Championships, LANs and the qualifiers feeding them, all regions, 2019 to now; cash cups only as optional extra signal.
6. **Event granularity.** Proposed: one `events` row per scored leaderboard (a session or round with one standings table), e.g. "FNCS Major 2 2026 Grand Finals NAC", with `tier`, `format`, `is_lan`, `region`, `date`. Tournament-level grouping goes in a new `tournament_key` column.

Record the answers in the `docs/architecture.md` Decisions table (event granularity, population) and in `docs/data_sourcing.md` (source status, verified limits).

### Phase 2: fetch infrastructure

- `src/fnf/sources/http.py`: one client used by every adapter:
  - per-source rate limiter (token bucket from constants);
  - retry with exponential backoff on 429/5xx, honoring `Retry-After`;
  - User-Agent `fnf-research/<version> (<contact>)`;
  - raw response cache at `data/raw/results/<source>/<sha256(endpoint+sorted params)>.json`, with cache-first reads;
  - optional `--refresh` to bypass the cache.
- New schema table `fetch_log` (`data/raw/results/fetch_log.csv`) with columns: `source`, `endpoint`, `params_hash`, `fetched_at`, `status`, `cache_path`, `bytes`. Never store the key or full query strings that contain one.
- Tests: rate limiter timing (with an injected clock), cache hit/miss, backoff, and that keys are absent from logs and cache paths.

### Phase 3: source adapters (one module each under `src/fnf/sources/`)

Order depends on the Phase 1 answers. Default: Cito first (results with Epic account IDs, which makes identity resolution easy), then Liquipedia (event catalog, LAN/tier metadata, birth dates), then Esports Earnings (optional).

Each adapter:
- `fetch_*` functions that go through the shared client and return raw JSON;
- `parse_*` functions from raw JSON to DataFrames in schema shape, pure and tested on fixtures;
- a CLI entry: `uv run fnf-fetch <source> [--since 2019-01-01] [--refresh]`.

Before writing an adapter, check what the source actually returns on a handful of live calls, and record field availability in `docs/data_sourcing.md`. Field names in this plan are expectations, not facts.

### Phase 4: build the backbone tables

`uv run fnf-build-results` (new CLI) combines adapter outputs into `data/processed/`:
- **`events`:** dedupe across sources by (name, date, region), keeping `source` and `source_key` from the primary source. Store other sources' keys in an `event_xref` table, or a column if simpler; decide and record.
- **`event_results`:** one row per (event, player). Team events give each member the team's placement; `team_key` groups teammates, and `field_size` is the number of teams.
- Validate with `schema.validate`; build fails loudly on problems, the same pattern as `fnf-build-tables`.

### Phase 5: identity resolution (`player_xref`)

- **Canonical id:** Epic account ID (`player_id`, 32 uppercase hex), the same id the replays use.
- **Match order:**
  1. exact account ID from the source → `confidence=exact`;
  2. a link the source documents, e.g. Liquipedia page ↔ account ID via a source that provides both → `exact`;
  3. otherwise write candidates to `data/interim/review/xref_candidates.csv` for the user to review → accepted rows become `manual`.
- **Never auto-accept fuzzy name matches.** Display names change, so use `valid_from` / `valid_to` when a source gives name history.

### Phase 6: career data (`player_meta`)

- `birth_date` only from an explicit published field, with its URL in `birth_date_source`. If a source gives only a year, store `YYYY` and note the precision. If the schema needs a precision column, add one and record the change.
- `debut_date` = date of the player's first row in `event_results`.
- `display_name` = the latest known name.

### Phase 7: replay acquisition groundwork (prepares work for the user; sends nothing)

1. **In-game tournament replay test (data_sourcing 2.2):** add a helper `uv run fnf-demos-snapshot` that lists the Demos folder (name, size, mtime) to a timestamped file and diffs it against the previous snapshot. Give the user the exact steps: snapshot, open a tournament replay in game, snapshot again, report. If a file appears, import it with `--source tournament_ingame --kind server` and run the manual server-vs-client check from data_sourcing 4.2.
2. **Consent template** for donated replays: `docs/consent_template.md`. It covers what's collected (including other players' IDs and names), purpose, storage, withdrawal, the pseudonymous contributor id, and guardian consent for minors. Mark it as a draft for the user to review.
3. **Outreach drafts** for Osirion and Epic research data access: `docs/outreach/*.md`. Each states the research purpose, the data requested (server replays, or parsed telemetry in our schema), non-commercial use, and data handling. The user sends them.

### Phase 8: quality gates for results (extend `fnf-quality`)

- Each event's placements cover 1..`field_size` without gaps or duplicates per team, or the event is flagged.
- ≥ 95% of `event_results` rows in the forecast population have an `exact` or `manual` `player_id`. Report the rest.
- Share of forecast-population players with a `birth_date` (reported, no threshold).
- Share of replay `players` (non-bot) that appear in `player_xref` (reported).

### Phase 9: docs and handoff

- `docs/data_sourcing.md`: source statuses, verified limits, field availability, Changelog.
- `src/fnf/schema.py`: built tables, then `uv run fnf-schema-doc`.
- README: new commands.
- Commit on `data/results-backbone`. Summarize for the user: coverage numbers, open review items, and what needs their action.

## Acceptance criteria

- `events`, `event_results`, `player_xref` and `player_meta` are built, schema-validated, and rebuildable from the raw cache with no network (`fnf-build-results`).
- Every network call goes through the shared client, and `fetch_log` shows rate limits honored.
- No secrets in git, logs, cache paths or fetch log (there's a test for this).
- New quality gates pass, or every failure is explained in the data_sourcing Changelog.
- Phase 1 decisions are recorded, and the docs are updated.
- `uv run pytest` passes offline.

## Stop and ask the user when

- Any Phase 1 question is unanswered.
- A source's terms are unclear or forbid the intended use.
- An identity match isn't `exact`.
- A step would need an account, a credential or an outgoing message.
- Coverage looks too thin for the forecast population, e.g. events before 2021 missing.
