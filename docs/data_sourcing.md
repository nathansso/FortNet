# Data sourcing

Status: active, last updated 2026-10-01. This is the procedure for acquiring, ingesting and checking data. Any session should be able to follow it end to end and get the same tables.

Related docs:
- [data_schema.md](data_schema.md): every table and column. Generated from `src/fnf/schema.py`, which is authoritative.
- [architecture.md](architecture.md): how the data is used, including splits and leakage rules.

## 1. What data we need

### 1.1 Replays

| Use | Replay kind | Mode | Lobby tier | Notes |
|---|---|---|---|---|
| Pipeline development (Stage 1a) | client OK | any | any | What we have now |
| Fight model, Stage 1 | server preferred, client OK | Build | any (tier is an input) | Client replays only fully cover fights involving the recorder |
| Event transformer pretraining (Stage 2) | **server** | Build | any, ideally high ranked tiers and up | Client relevancy gaps look like behavior, so server replays only |
| Competitive fine-tuning and evaluation | server, or pros' own client replays | Build | cash cup, FNCS, LAN | Must carry a reliable date and lobby tier |
| Per-pro features (FWAE, latency) | server, or that pro's own client replays | Build | competitive | ≥ ~50 fights per pro per 90-day window |

The major FNCS events are played in **Build** mode. Zero Build replays are kept, tagged by playlist, and modeled separately or excluded. They also contain item-deployed structures that aren't player building.

A replay is **usable** when all of these hold:
- it's finalized ("encrypted but not completed" means the recording was cut off; these fail to parse and are skipped);
- its game build is supported (see 4.3);
- its date is known (`utc_start`, or the file-name timestamp);
- its provenance is in the manifest.

### 1.2 Results backbone and career data (non-replay)

Needed for the forecaster. Schemas are planned in [data_schema.md](data_schema.md): `events`, `event_results`, `player_xref` and `player_meta`.
- **Per-event placements** for every pro in the forecast population, at least from 2019 onward. Majors, LANs and the qualifiers feeding them; cash cups as extra signal.
- **Identity mapping**: every external name or id is mapped to an Epic `player_id` through `player_xref`. Display names change often, so mappings carry validity dates and a confidence level.
- **Birth dates** only where publicly published (Liquipedia infobox, Wikipedia), each with its source URL in `birth_date_source`. Never infer or guess an age.

### 1.3 Volume targets

Starting estimates. Replace them with Stage 1 learning-curve results once available (architecture 1.8).

| Purpose | Fights | Server replays | Client replays |
|---|---|---|---|
| Stage 2 pretraining (2–10M-parameter model, ~10–50M tokens) | 100k–300k | ~700–2,000 | ~5k–15k |
| Competitive fine-tuning | 10k–30k | ~100–200 | pros' own replays |
| Held-out evaluation | ≥ 5k competitive | ~40 | n/a |
| Per-pro features | ≥ ~50 per pro per 90 days | most active pros get there | needs that pro's replays |

Measured yield on current data: a median client replay has ~75 visible player-vs-player damage exchanges (~19 involving the recorder). Exchanges are ~1 s bursts, and several merge into one fight. A server replay should yield several times more.

## 2. Sources

Each source has a `source` tag that is written to the manifest. Statuses: **verified** (used successfully), **untested**, **not contacted**, **excluded**.

### 2.1 `local_demos`: replays recorded on this machine (verified)

Fortnite saves replays to `%LOCALAPPDATA%\FortniteGame\Saved\Demos` when replay recording is enabled in the game's settings. These are client replays. Use them for pipeline development and pretraining; Build Ranked matches are the most useful. Command: `uv run fnf-import` (defaults to this folder, `--source local_demos --kind client`).

### 2.2 `tournament_ingame`: Epic's in-game tournament replays (untested, highest priority)

The game client can play tournament matches with whole-lobby coverage. Unknown: whether viewing one leaves a `.replay` file on disk. Test procedure:
1. List `%LOCALAPPDATA%\FortniteGame\Saved\Demos` and note the newest file.
2. In Fortnite, open a tournament match replay and let it load fully.
3. List the folder again. If a new `.replay` appeared, copy it to a staging folder.
4. Import it: `uv run fnf-import <staging> --source tournament_ingame --kind server`, then export and build (section 3).
5. Confirm it's a server replay: `players` should cover the whole lobby, and `positions` should resolve players far from any one recorder. Record the result in the Changelog below and update this section's status.

If it works, this is the primary competitive source. Collecting by hand is slow, so measure minutes per replay before planning volume.

### 2.3 `donated`: replays from competitive players (not started)

Client replays donated by cash-cup / Unreal-rank players and pros. They fully cover the donor's own fights, so they're good for that player's features and for pretraining.
- **Consent is required**, recorded before import. The consent record covers: what is collected (replays, which include other players' account IDs and names), the research purpose, storage and access, the right to withdraw (all files for a contributor are deleted), and a pseudonymous contributor id. **Minors need guardian consent.**
- Import: `uv run fnf-import <folder> --source donated --kind client --contributor c017 --consent CONSENT-2026-014`. The command refuses `donated` without `--consent`.
- Never put real names in `contributor`; keep the contributor-to-person key outside this repo.

### 2.4 `partner_osirion` / `partner_other`: data partnerships (not contacted)

Osirion holds tournament replay data at scale (2D tournament replay viewer, acquired fortnite-replay.info). Ask for research access to server replays, or to parsed telemetry delivered in our schema ([data_schema.md](data_schema.md)), for non-commercial academic use. Epic is the other candidate (a research data request). Record contacts and terms in the Changelog. Data received under partner terms is tagged with its source and handled as those terms require.

### 2.5 Results backbone sources (not started)

| Source | Gives | Terms / limits |
|---|---|---|
| Cito API (citoapi.com) | Tournament results, placements, kill feeds and storm circles parsed from server replays (no positions) | Free tier 500 requests/month, paid from $25/month. Results and labels only |
| Liquipedia (LPDB / MediaWiki API) | Events, placements, rosters, birth dates in infoboxes | Free only for non-commercial use with open-source code. Content CC-BY-SA, so attribute. MediaWiki API 60 req/h |
| Esports Earnings API | Prize results per player | API key, 1 req/s. No birth dates |
| Epic Power Rankings (official, since June 2026) | Weekly Elo-style rating over each player's top-20 results | Lags declines (bad results can't lower it). Baseline only, never a target |

### 2.6 Excluded

- **Unofficial Epic replay/event endpoints** called with a game-client credential embedded in third-party libraries, e.g. `fortnite-replay-downloader`. Terms-of-service risk. Agents must not use them. Only the project owner can decide otherwise, recorded in the architecture doc's Decisions table.
- Scraping any site against its terms.

## 3. Ingest procedure (reproducible)

Prerequisites: .NET 10 SDK and [uv](https://docs.astral.sh/uv/). On this Windows machine `dotnet` lives in `C:\Program Files\dotnet`; add it to PATH in Git Bash with `export PATH="/c/Program Files/dotnet:$PATH"`.

```bash
uv sync
dotnet build ingest/ReplayExport -c Release

# 1. Import (copies + manifest; dedupes by sha256)
uv run fnf-import [folder] [--source ... --kind ... --contributor ... --consent ...]

# 2. Export per-replay telemetry CSVs (skips already-exported; --force to redo)
dotnet run --project ingest/ReplayExport -c Release --no-build

# 3. Build processed tables (casts and validates against the schema; fails loudly)
uv run fnf-build-tables

# 4. Validate and run quality gates
uv run fnf-validate
uv run fnf-quality
```

Layout:

```
data/raw/replays/*.replay                 immutable copies, named by original file name
data/raw/manifest.csv                     provenance (schema: manifest)
data/interim/telemetry/<match_id>/*.csv   one folder per replay (schema: interim tables)
data/processed/*.parquet                  combined, typed tables (schema: processed tables)
```

`data/` is git-ignored. To rebuild from scratch, delete `data/interim` and `data/processed` and rerun steps 2–4; `data/raw` is the only thing that can't be regenerated.

## 4. Quality gates

### 4.1 Automatic (`uv run fnf-quality`)

| Gate | Threshold | Current (2026-10-01, 98 replays) |
|---|---|---|
| Recorder damage to players vs. game end-of-match stat | r ≥ 0.90, median ratio 0.90–1.10 | r = 0.938, ratio 1.01 |
| Position rows with a resolved `player_id` | ≥ 99% | 99.98% |
| Knock event time vs. downed flag in positions | \|median\| ≤ 50 ms | −14 ms |
| Build shapes covered by `ingest/gen_build_pieces.py` | none unknown | all known |
| Manifest replays without telemetry | reported | 2 (unfinalized recordings) |

A failing gate blocks using new data for modeling until it's explained in the Changelog.

### 4.2 Manual checks for a new source or a new game build

- **Server vs. client:** a server replay resolves players across the whole map. A client replay's `health` table covers ~1–3 players.
- **Builder attribution:** for build-mode data, rerun the team-blind attribution check described in the README (`pieces.builder_source`) and record its accuracy.
- **Lobby tier:** confirm the tier can be read from `matches.playlist` / `tournament_round`, or record it in the manifest `notes` until a `lobby_tier` column exists.

### 4.3 Supported game builds

Verified end to end: 41.30, 42.00, 42.10, 42.20 (FortniteReplayReader 3.1.0).

When a new build ships:
1. Update the `FortniteReplayReader` package version if needed.
2. Export a sample of new replays and run `fnf-quality`.
3. If new `PBWA_*` shapes appear, add them to `ingest/gen_build_pieces.py`, run `uv run python ingest/gen_build_pieces.py`, rebuild and re-export.
4. Add the build to this list.

## 5. Adding a new source (checklist)

1. Add its `source` tag to `SOURCES` in `src/fnf/import_replays.py` and to the `manifest.source` description in `src/fnf/schema.py`, then run `uv run fnf-schema-doc`.
2. Add a subsection under section 2: what it gives, status, procedure, terms.
3. Import a small batch, run the full procedure and quality gates, and do the manual checks in 4.2.
4. Record the result in the Changelog.

## 6. Privacy

- Replays contain Epic account IDs and display names of everyone in the lobby. Many pros are minors.
- Nothing under `data/` is committed or shared. Published outputs are aggregates only.
- Donated data can be withdrawn: delete the contributor's files from `data/raw/replays`, their manifest rows, and rebuild.

## Changelog

| Date | Change |
|---|---|
| 2026-10-01 | Manifest introduced and backfilled with 100 `local_demos` client replays. Quality gates added; all pass on 98 exported replays. NPC bots without unique ids get `BOT_<state_player_id>`. |
| 2026-09-30 | Builder attribution with build-tool signal (95% team-blind accuracy on 1,142 Creative pieces). |
| 2026-09-27 | C# exporter on FortniteReplayReader 3.1.0. Damage, health, positions and builds validated on local replays. |
