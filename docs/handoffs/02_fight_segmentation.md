# Handoff 02: damage-based fight segmentation (Stage 1.1)

Branch: `stage1/fight-segmentation` (from `main`). Written 2026-10-01.

> **Status (2026-10-01):** done and extended. The kill-feed v0 tables (`fights`, `player_fights`, `elims.fight_id`) were retired in a separate commit; v0 appears below only as the starting point. Beyond this plan the user added the three-way engagement type (fight / pick / poke), the `pokes` outcome table and `seg_version`: see docs/architecture.md 1.1 and 1.1a. The v0-vs-v1 comparison in Phase 4.3 (41.9% of 2,766 v0 fights with a knock matched a v1 fight; 1,584 of the misses had no recorded damage) can no longer be rerun from code.

## Prompt to start the session

> You're picking up Stage 1.1, fight segmentation, for the Fortnite placement forecasting project in this repo. Read `CLAUDE.md`, then `docs/handoffs/02_fight_segmentation.md` (your plan), section "Stage 1" and "Data splits" of `docs/architecture.md`, and the `damage`, `teams`, `elims`, `positions`, `players` and `matches` tables in `docs/data_schema.md`. Work on branch `stage1/fight-segmentation`. If you're in a git worktree, set `FNF_DATA_DIR` as described in CLAUDE.md so you use the shared data. Follow the plan phase by phase: explore before implementing, and stop at the visual-check step in Phase 4 so I can review example fights. Report at the end of each phase with numbers, what changed, and what's next.

## Context

Stage 1 predicts who wins a fight from the situation at its start, and turns actual-minus-expected into a skill feature (architecture 1.1–1.4). Everything downstream depends on a clean definition of a fight, its participants, its start time `t0` and its outcome. The original `fights` / `player_fights` tables were a kill-feed v0 that only saw fights with a knock and had no teams (since retired). This handoff replaces it with damage-based segmentation and produces the planned `fight_sides` table.

## Goal

Implement `fights.py` v1: segment fights from player-to-player damage between teams, label each side's outcome, and flag coverage problems. Build `fight_sides` into the pipeline with tests, diagnostics and documented parameter choices. Snapshot features (1.2) are the next handoff, not this one.

## Facts about the current data (measured 2026-10-01, 98 client replays)

- **`damage`:** 159,724 rows.
  - 74.6% have `target` null (non-player hits, mostly structures).
  - 42.5% have `magnitude` 0.
  - Self-hits are ~0%.
  - Filtering to player-to-player with `magnitude > 0` leaves **36,076 rows**.
  - Teams at hit time (from `teams`, using the last assignment at or before `t`) resolve for 100% of those. Friendly fire is 0.03%.
- **Gaps between consecutive damage events for the same team pair:** median 0.2 s, 75th percentile 0.9 s, 90th 4.5 s, 95th 14.6 s, 99th 103 s. Team-pair segments by gap threshold, across 2,150 distinct (match, team pair) groups: 5 s → 5,361, 10 s → 4,291, 15 s → 3,818, 20 s → 3,534. (Corrected 2026-10-01 from Phase 1; the original figures counted splits, not segments.)
- **Knocks vs. damage** (corrected 2026-10-01 from Phase 1):
  - **Recorder-involved knocks (468):** only 0.6% have no recorded damage on the victim; time from last damage to the knock is a median of 0.14 s, 90th percentile 2.2 s. 96.8% fall inside a team-pair segment at gap 10 s plus 3 s grace.
  - **All lobby knocks (5,072):** 47.3% have no damage ever recorded on the victim, and the 90th percentile is ~211 s, because most are outside the recorder's view range. Labels for non-recorder fights must account for this (Phase 2 step 5).
- **`matches.team_size` is mis-decoded** (values like 24 and 25). Derive team size from `teams`.
- **Mode:** most matches are Zero Build duos/squads, and 3 are Creative build matches. 6% of `teams` rows are bots (`BOT_*` or bot unique ids).
- **Clocks:** `damage.t`, `positions.t` and `elims.t_ms/1000` share one clock, aligned to ~15 ms.
- **Client-replay coverage:** fights involving the recorder (`matches.replay_owner`) are complete except opponents' health. Other fights can be partial.

## Out of scope

- Snapshot features, models, FWAE (later handoffs).
- Changing the C# exporter. If you find exporter bugs, write them up for the user instead.
- Results-backbone tables (handoff 01). In `src/fnf/schema.py`, edit only fight tables.

## Plan

### Phase 0: orient

Read the docs in the prompt. Run the pipeline end to end (CLAUDE.md commands), then `uv run fnf-quality`. Read `src/fnf/fights.py` (v0 at the time of writing; now replaced by v1), `src/fnf/builds.py` (it has `merge_asof`-by-player patterns you can reuse) and `src/fnf/splits.py`.

### Phase 1: explore (a script, not library code)

Write `scripts/explore_fights.py` (committed, deterministic, prints numbers, no plots required) and reproduce the facts above. Then answer:
1. How often do two team-pair segments overlap in time while sharing a team (third parties)? Within what time window?
2. For opposing-team knocks involving the recorder: what share fall inside a damage segment at gap 10 s plus a 3 s grace window?
3. How are solos different? There, an elimination can happen without a knock.
4. How many segments involve a bot team, and should bot fights be excluded from training labels? Proposed: keep them, flagged `has_bots`.

Report the answers before Phase 2.

### Phase 2: implement `src/fnf/fights.py` v1

Keep v0 in place for now (it was later retired); add v1 functions. Make every parameter a module constant with a docstring explaining it, and a keyword argument.

1. **Engagement damage:** `target` and `source` not null, `source != target`, `magnitude > 0`. Attach `source_team` and `target_team` (team at `t`, by `merge_asof` per player per match). Drop rows with an unknown team or friendly fire.
2. **Team-pair segments:** for each match and unordered team pair, sort by `t` and start a new segment when the gap exceeds `GAP_S` (start with 10 s and tune in Phase 4).
3. **Fights:** merge segments that share a team and **truly overlap in time**, within a tolerance `OVERLAP_TOL_S` (start at 0–3 s), into one fight. Don't merge on `GAP_S` proximity: back-to-back fights (A–B ends, then A–C starts) stay separate, since the carry-over state is captured by snapshot features at the next `t0`. `multi_team = number of teams > 2`. A two-team fight has exactly one pair. (Decided 2026-10-01 after Phase 1: merging within `GAP_S` made 38% of fights multi-team and chained up to 13 teams over 192 s; true overlap gives ~16% multi-team.)
4. **Times:** `t0` = first engagement damage in the fight. `t_end` = last engagement damage.
5. **Outcome per side:**
   - Use opposing-team knocks/elims from `elims`: the eliminated player is on one fight team, and the eliminator is on another fight team.
   - The event must fall within `[t0, t_end + GRACE_S]` (start with `GRACE_S = 3`).
   - In solo playlists, an elimination without a knock counts as a knock.
   - The **first** such event decides: the victim's side `loss`, the eliminator's side `win`.
   - If both sides suffer a first knock within `TIE_S = 1` s of each other, it's `tie` for both.
   - With no qualifying knock, it's `disengage` for both.
   - Multi-team fights label each team by whether it lost a member first, won by downing another fight team's member first, or neither. Training excludes multi-team fights in v1, but label them anyway.
6. **Flags and counts per side:** `players` (`;`-joined ids engaged on that side), `n_damage_events`, `damage_dealt`, `damage_taken`, `recorder_involved` (any participant is `matches.replay_owner`), `has_bots`.
7. **Ids:** generate `fight_id` deterministically, e.g. `f"{match_id}:{index}"` in `t0` order, so reruns produce identical ids.

### Phase 3: schema and pipeline

- Update the planned `fight_sides` table in `src/fnf/schema.py` to match what you built: add the Phase 2 step 6 columns, set `status="built"` and document each column. Run `uv run fnf-schema-doc`.
- Wire it into `src/fnf/build_tables.py`. It must pass `schema.validate`.
- Keep producing v0 `fights` / `player_fights` until the user agrees to retire them, then remove them in a separate commit (done).
- Add a gate to `src/fnf/quality.py`: the share of recorder-involved opposing-team knocks that fall inside a v1 fight with a non-`disengage` outcome. Set its threshold from Phase 4 results; ≥ 90% is the target.

### Phase 4: tune and check

1. **Sensitivity:** for `GAP_S` in {5, 10, 15, 20}, `GRACE_S` in {1, 3, 5} and `OVERLAP_TOL_S` in {0, 1, 2, 3}, report number of fights, outcome shares (win/loss/tie/disengage), duration distribution, and recorder-knock coverage (the quality gate). Choose values and record them in the `docs/architecture.md` Decisions table with the numbers that justified them.
2. **Visual check (stop here for the user):** write `scripts/plot_fights.py`. It renders N random recorder-involved fights to PNGs under `data/reports/fights/`, which is git-ignored:
   - top-down tracks from `positions` for each participant, from `t0` − 5 s to `t_end` + 5 s, colored by team;
   - damage events as source → target segments;
   - knocks marked;
   - title with fight_id, outcome per team and duration.

   Use matplotlib (add as a dev dependency). Then ask the user to review ~10 fights and say whether segmentation and labels look right. Iterate on their feedback.
3. **v0 vs. v1:** report what fraction of kill-feed v0 fights with a knock are matched by a v1 fight, and characterize the misses (no damage recorded, out of the recorder's view range).

### Phase 5: tests (`tests/test_fights.py`, synthetic frames only)

Cover at least:
- a clean 1v1 win;
- a gap that splits two fights;
- friendly fire ignored;
- a knock in the grace window after the last damage counts, and one after the grace window doesn't;
- tie within `TIE_S`;
- disengage when nobody is knocked;
- third-party merge into a multi-team fight;
- a player's team changing mid-match uses the team at hit time;
- solo elim without a knock;
- deterministic `fight_id`s;
- **a leakage guard:** deleting all events after a fight's `t_end + GRACE_S` doesn't change that fight's `t0`, participants or outcome.

### Phase 6: docs and handoff

- `docs/architecture.md`: update 1.1 with the final algorithm and parameters. Resolve or update the open question on disengagement labels.
- `docs/data_sourcing.md` Changelog: one line on the new table and gate.
- README "Next steps": point to 1.2 snapshot features.
- Commit on `stage1/fight-segmentation`. Summarize for the user: counts, chosen parameters, gate result, known failure modes, and a proposed outline for handoff 03 (snapshot features at `t0`).

## Acceptance criteria

- `fight_sides` is built by `fnf-build-tables`, schema-validated, and deterministic across reruns.
- All Phase 5 tests pass, and the full suite passes.
- Recorder-knock coverage meets the agreed threshold (target ≥ 90%), or the shortfall is explained.
- Parameters are chosen from the sensitivity analysis and recorded in Decisions.
- The user has reviewed example fight plots, and their feedback is addressed.

## Stop and ask the user when

- Phase 1 findings suggest a different fight definition than this plan.
- You reach the visual check (Phase 4.2).
- You want to retire the v0 tables.
- You hit an exporter bug or a data problem the quality gates didn't catch.

## Coordination with handoff 01

Both branches edit `src/fnf/schema.py`. Touch only your own tables. After rebasing on `main`, run `uv run fnf-schema-doc`; the doc test fails if you forget. Neither branch commits anything under `data/`.
