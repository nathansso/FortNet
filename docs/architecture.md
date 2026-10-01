# Architecture: from fights to placement forecasts

Status: plan, agreed 2026-09-30; data splits, fight v1 and pokes added 2026-10-01. Stage 1 is the active work. Stages 2 and 3 are designed but gated on data (see "Entry criteria" in each).

## Goal

Forecast each pro's placement percentile at the next Major or LAN, using only information from before that event. Then test whether age predicts decline once fight skill, reaction latency, tenure, debut cohort, format era and activity are controlled for. Background and literature: [research/literature_review.md](research/literature_review.md). Data acquisition and schema: [data_sourcing.md](data_sourcing.md), [data_schema.md](data_schema.md).

## System overview

Two models, trained separately:

1. **Fight model.** Learns how likely a side is to win a fight *given the situation*, from many fights, without knowing who the players are. It never sees placements. Its job is to turn raw fights into skill measurements that aren't confounded by circumstance (height, health, numbers, cover).
2. **Placement forecaster.** For each (player, upcoming event), it ranks the field using rating history, fight-skill features from the fight model, latency features, and career/context features.

```
replays ─► fights ─► fight model: P(win | situation) ─► residuals (actual − expected) ─┐
   │                                                                                   ├─► player features (pre-event, shrunk) ─► forecaster ─► placement percentile
   └──────► latency features (hit→return fire, hit→build) ────────────────────────────┘                                            ▲
results backbone (placements, ratings) + career data (age, tenure, cohort, era) ────────────────────────────────────────────────────┘
```

The fight model evolves over three stages. Each stage must beat the previous one on the gates in [Evaluation](#evaluation-protocol), and the previous stage stays as the baseline.

| Stage | Fight model | Feature it produces | Data needed |
|---|---|---|---|
| 1 | Snapshot at engagement start → P(win) | Fights won above expected (FWAE), hand-built latency | Works on current data (machinery); pros need server replays |
| 2 | Causal event transformer over the fight's event chain | Win probability added per action, latency vs. model-predicted response time | Tournament server replays at scale |
| 3 | Fight-history encoder → player embedding over time | Distance from own peak, drift speed, comparable-player trajectories | Stage 2 data plus multi-season histories |

## Cross-cutting rules

These apply to every stage. A change that breaks one needs an explicit decision recorded below.

### Time and leakage

- **Within a fight:** a prediction made at time *t* may only use information from ≤ *t*. Stage 1 predicts at engagement start. Stage 2 enforces this with a causal mask.
- **Across a career:** features for event *E* use only fights and results dated before *E*. Fight models used to produce features for *E* are trained only on data before *E*. They're retrained at each rolling-origin step, or trained on a population disjoint from the forecast set and frozen before the forecast window.
- **Across patches:** weapons and movement change by season, so the season/patch is an input to every fight model. Residuals are compared within era. The forecaster gets the format era as a feature.

### Identity exclusion

Fight models (Stages 1–2) never see player identity: no player ID, name, embedding or team history. If they did, they would learn "who wins" instead of "which situation wins", and the residual would no longer measure skill. Identity enters only through aggregation (FWAE) or the Stage 3 encoder, which is a separate model.

### Population

The fight model may train on any lobby (pubs, ranked, cash cups). "Who should win this spot" doesn't need pro data, and more fights make it better. Player-level features and the forecaster use pros only.

### Label calibration and relabeling

Every rule-based label (fight boundaries, outcomes, poke vs. fight, poke conversion windows) has thresholds that were first tuned on **local client replays: mostly Zero Build pubs, recorder-involved fights only**. Those are v1 values for building the pipeline, not final ones.
- Before any model is trained for pro features, **re-tune and relabel on competitive Build data** (tournament server replays or pros' own replays). Rerun the parameter sweep, the visual review of example plots (including build fights) and the quality gates, then record the new values in Decisions.
- Build mode changes the data itself. Builds absorb damage, fights last longer, more damage hits structures, and pokes often target walls and tarps (long protected rotation tunnels). Gap, grace and poke thresholds are expected to move.
- One definition is used across all data, tuned on competitive Build data, because that's what the final models serve. Pub data can still pretrain under it.
- Labeled tables carry a `seg_version` string (the parameter set that produced them), so models and features record which labels they used.

### Data handling

Replays contain account IDs and display names, and many pros are minors. `data/` is never committed. Only aggregated results are published.

## Stage 1: snapshot fight model and FWAE

### 1.1 Fight segmentation (replaces kill-feed v0)

Source: the `damage`, `positions`, `teams`, `elims` and `players` tables. Implementation: `src/fnf/fights.py` v1 (handoff 02). All thresholds are v1 values, subject to [relabeling](#label-calibration-and-relabeling).

- **Engagement damage:** player-to-player damage (`target` not null, `source != target`, `magnitude > 0`) between different teams, using `teams` as of the hit time.
- **Team-pair segments:** per match and team pair, a new segment starts when the gap between hits exceeds `GAP_S` (v1: 10 s; 5 s under review).
- **Fights:** segments that share a team merge into one fight only when they **truly overlap in time**, within `OVERLAP_TOL_S` (v1: 1 s, swept 0–3 s). Back-to-back fights (A–B ends, then A–C starts) stay separate; the carried-over state (health, position) is captured by the next fight's snapshot at `t0`. Merging on gap proximity instead made 38% of fights multi-team and chained up to 13 teams.
- **Engagement start** `t0`: the first damage event of the fight. Snapshot features are taken at `t0`, before any damage resolves.
- **Engagement type** (per fight): `fight` when both sides deal meaningful damage; `poke` when it's one-sided (not `mutual`, or the minority side dealt less than `POKE_MINORITY_SHARE` of total damage; v1 ≈ 10%). See [1.1a](#11a-pokes-and-zone-pressure).
- **Fight outcome (per side, `engagement_type = fight`):**
  - `win` = an opposing member is knocked or eliminated first, within `[t0, t_end + GRACE_S]` (v1: 3 s);
  - `loss` = the reverse;
  - `tie` = both sides' first knocks within 1 s;
  - `disengage` = no knock. Kept as its own class, not dropped.
- **Output table** `fight_sides`: one row per (fight, team), with participants, `t0`, end, outcome, `engagement_type`, `mutual`, hits/damage per side, distance, `multi_team`, `recorder_involved`, `has_bots` and `seg_version`.

v1 numbers (98 local client replays, `GAP_S` 10 / tolerance 1 / grace 3): 3,217 fights, 20.6% multi-team. 97.2% of recorder-involved opposing-team knocks fall in a fight with a decisive outcome.

### 1.1a Pokes and zone pressure

In competitive play, a poke is usually zone pressure: a team that rotated early and holds a good position inside the next zone chips a team rotating late across open ground under storm pressure. A poke rarely produces a knock directly. Its value is what it causes next. So pokes are kept as their own engagement type with their own outcome and skill measure, never counted as failed fights.

**Poke outcomes** (per poke, labeled in `fight_sides` or a sibling table):

| Outcome | Definition (v1, to re-tune on competitive Build data) | Source |
|---|---|---|
| Net damage | Damage dealt − damage taken in the poke | `damage` |
| Conversion | Target knocked or eliminated by **anyone** within `POKE_CONVERT_S` after the poke ends (start 20 s) | `elims` |
| Storm death | Target dies within `POKE_CONVERT_S` while flagged `in_storm` | `players`, `positions` |
| Forced heal | Target's health/shield rises without a pickup within N s | `health`; recorder-only in client replays, so server replays only |
| Structure pressure | Damage to structures within ~2 tiles of target players during the poke | `damage` (`target` null) + `positions`; matters in Build, where pokes hit walls and tarps |

**Zone context** (snapshot features at `t0`, part of 1.2, for fights and pokes):
- distance of each side to the current and next safe-zone edge (inside or outside, in uu);
- time until the next shrink;
- whether each side's players are moving toward the zone (velocity · direction to zone center);
- the **rotation timing** of each team in the current storm phase: when its players entered the next zone relative to that phase's shrink start (early, on time or late), computed from `positions` and `safezones`;
- height difference, as in 1.2.

**Skill measures** (same pattern as FWAE):
- **Poke value above expected (PVAE):** a small model predicts poke outcomes (conversion probability, expected net damage) from the poke's `t0` snapshot. PVAE = actual − expected, credited to the poking side by damage share, aggregated and shrunk per player like FWAE.
- **Rotation quality:** for the poked side, damage taken (and conversions suffered) per late rotation, compared with expected. Rotation timing itself (early/late share per player) also becomes a forecaster feature.

### 1.2 Snapshot features at `t0`

Per side (sum/mean/max over the team's players present), plus differences between sides:

| Group | Features | Source / caveat |
|---|---|---|
| Numbers | players alive per team, players engaged | `teams`, `players` death times |
| Health | health + shield | `health` is recorder-only in client replays: use a missing flag plus damage taken since last known value. Full coverage expected in server replays |
| Geometry | horizontal distance, height difference, closing speed, facing angle toward opponent | `positions` |
| Loadout | held item class at `t0` (shotgun / AR / SMG / sniper / build tool / other) | `weapons` |
| Cover | own and enemy pieces within 2 tiles, pieces between the sides, high-ground pieces | `pieces` |
| Context | storm phase, time into match, other teams within N m (third-party risk), season/patch | `safezones`, `matches` |
| Zone and rotation | per side: distance to current and next zone edge, inside/outside, moving toward zone, team rotation timing this phase (see 1.1a) | `safezones`, `positions` |

No identity fields (see [Identity exclusion](#identity-exclusion)).

### 1.3 Models

1. Logistic regression on the side-difference features (calibration floor).
2. Gradient boosting (LightGBM) on the same features.
3. **Neural net:** a set model over player tokens (Deep Sets or a small transformer without a time axis). It handles variable team sizes (solos to squads) and per-player features without hand-aggregation. Season/patch is a context token.

Train with log loss and check calibration (reliability curves, Brier). Split by match, ordered by date, never by fight.

### 1.4 Fights won above expected (FWAE)

- **Per fight:** each side's residual = outcome (1/0) − P(win). Players on the side share it in proportion to their damage dealt in the fight, with an equal split as a sensitivity check.
- **Per player, before event *E*:** sum the residuals over fights in a window before *E* (start with 90 days), then shrink toward 0: `FWAE = Σr / (n + k)`. Fit `k` by split-half reliability.
- **Variants:** FWAE when outnumbered or at a health disadvantage, FWAE in build fights vs. no-build fights, fight volume.
- **Companion measures:** PVAE (poke value above expected) and rotation quality from [1.1a](#11a-pokes-and-zone-pressure), aggregated and shrunk the same way and passed through the same reliability gate.
- **Reliability gate:** split-half (odd/even fights) correlation of FWAE across players ≥ 0.5 at the chosen window. If it fails, lengthen the window or drop the variant.

### 1.5 Latency features (hand-built)

From `damage`, `positions`, `weapons` and `pieces`, per player per window, as median and IQR plus trend:

- **Hit → return fire:** first damage from the victim to the attacker after being hit, after a quiet period of ≥ 2 s.
- **Hit → build:** first piece placed by the victim after being hit (builder attribution from `pieces`; build modes only).
- **Hit → turn:** time until the victim's yaw points within 30° of the attacker.
- **Trend:** slope of each median across rolling windows, i.e. months of career. This is the operational stand-in for perception-action cycle latency.

### 1.6 Forecaster (shared by all stages)

- **Unit:** (player, upcoming event). **Target:** placement percentile, trained with a ranking objective within each event.
- **Feature blocks:**
  - **Results history:** Weng-Lin/OpenSkill μ and σ from full lobby placements, recent placement trend, events played.
  - **Fight skill:** FWAE and its variants.
  - **Latency:** level and trend.
  - **Career:** age, tenure, debut cohort, format era, activity (events in the last 90 days).
  - **Event context:** LAN or online, team size, teammate ratings.
- **Models:** LightGBM ranker, plus a hierarchical (mixed-effects) model with explicit age, tenure, cohort and era terms for the age hypothesis test.
- **Baselines:** last-event rank, rating-only, and Epic's Power Rankings where available.

### 1.7 Stage 1 deliverables

- **1a (on current local data):** `fights.py` v1 segmentation, a `fight_sides` table, a snapshot feature builder, the three fight models with calibration report, FWAE and latency feature builders, and tests for leakage (no feature uses data after `t0` or after event *E*).
- **1b (on pro data):** the same pipeline on tournament server replays plus a results backbone, then the forecaster and the ablation (rating-only vs. + FWAE vs. + latency).

### 1.8 Stage 1 exit criteria

- The fight net beats logistic regression on held-out log loss and is calibrated within ±3 pp per decile.
- FWAE passes the reliability gate.
- On pro data, adding FWAE and/or latency improves forecaster NDCG@k over rating-only in rolling-origin evaluation (block bootstrap CI over events excludes 0).

## Stage 2: causal event transformer

**Entry criteria:** Stage 1 exited, and tournament server replays at scale. Aim for tens of thousands of complete fights; set the threshold from Stage 1 learning curves.

### Tokenization

A fight becomes a sequence: `[context] → event → event → …`

- **Context token:** season/patch, storm phase, players alive, team sizes.
- **Event tokens:** shot or damage, knock, elimination, piece placed, edit, edit reset, held-item switch, heal, plus periodic state ticks (every 250 ms) so inactivity is visible.
- **Each token carries:** event type, Δt since the previous token, actor and target as *roles* (self team / enemy team, player slot), not identities, and the state relevant to that event (relative positions, height, health/shield, held item, nearby pieces).

### Objectives (multi-task, causal mask)

1. **Next event:** predict the type, actor role and time until the next event (a temporal point process head). Every event is a label, so this is the self-supervised bulk of the signal.
2. **Win probability:** P(each side wins the fight) at every step.

### Features produced

- **Win probability added (WPA) per action:** the change in P(win) caused by each event, summed per player and split by action type (shooting, building, editing, positioning).
- **Latency vs. expected:** for stimulus events (taking a hit, enemy appearing), the player's actual response time minus the model-predicted response time. This is reaction latency with the situation controlled for, and it supersedes 1.5 when it passes the gates.

### Exit criteria

- Beats Stage 1 log loss at `t0` *and* is calibrated at later steps.
- WPA and latency-vs-expected pass the split-half reliability gate.
- Adding them improves forecaster NDCG over Stage 1 features.

### Risks

- Client-replay relevancy gaps look like behavior. Train on server replays only.
- Credit between teammates is ambiguous. Report WPA at team level alongside player level.

## Stage 3: fight-history encoder and player trajectories

**Entry criteria:** Stage 2 exited, plus multi-season fight histories for the pro population.

### Model

An encoder over a player's last *N* fights (Stage 2 token sequences or Stage 2 per-fight summaries) outputs a vector *z*. It is trained so *z* improves prediction of that player's *next* fights when added to the Stage 2 model. Optionally add a placement head (multi-task), so the vector is shaped toward what matters for results. Because the encoder is inductive, it works for new players without retraining. Computed month by month, it gives a trajectory *z(t)* per player.

### Features for the forecaster

- **Distance from own peak:** ‖*z(t)* − *z*(peak window)‖.
- **Drift speed:** recent change in *z* per month.
- **Comparables (PECOTA-style):** the k nearest historical players by trajectory up to the same career stage, and their subsequent placement changes.
- **Raw *z*, with a dimension sweep:** treated as an experiment, not a default (see Decisions).

### Exit criteria

- The encoder improves held-out next-fight log loss over Stage 2 alone.
- Trajectory or comparable features improve forecaster NDCG.
- Gains hold on **held-out players** (players never seen in encoder or forecaster training), not only held-out events.

## Data splits

Implemented in `src/fnf/splits.py` as pure functions of ids and dates, so every session reproduces the same assignment (tests: `tests/test_splits_schema.py`). Changing a fraction or salt is a versioned decision: bump the salt suffix (`-v1` → `-v2`) and add a row to [Decisions](#decisions).

| Split | Unit | Rule | Code |
|---|---|---|---|
| Held-out players | `player_id` | 20% of players by salted hash (`fnf-holdout-v1`). Bots never held out | `is_held_out_player` |
| Fight models | match | Chronological by match start: oldest 70% train, next 15% val, latest 15% test | `chronological_split` |
| Out-of-fold residuals | match | 5 folds by salted hash of `match_id` (`fnf-folds-v1`) | `cross_fit_fold` |
| Forecaster | event date | Rolling origin: train on events strictly before the origin date, test on that date's events | `rolling_origins` |

### Held-out players (all stages)

- Excluded from Stage 3 encoder training, forecaster training, and all hyperparameter and feature selection.
- Their fights *may* be used to train the identity-free fight models (Stages 1–2), because those never see who played. Their residual features must still be out-of-fold (below).
- Forecaster metrics are reported separately for held-out and seen players. A large gap means the model is memorizing players.

### Fight models (Stages 1–2)

- Whole matches go to one split. Match start is `utc_start`, falling back to the replay file-name timestamp (local time) when missing.
- Once tournament data exists, split by **session** (all matches of one tournament session together), since a session's matches share players and conditions. Then add a `session_id` grouping to `chronological_split`.
- The test split is touched only for numbers that get reported. Tuning uses val.
- Also report on the most recent season alone, to catch patch drift.
- **Pretrain / fine-tune (Stage 2):** pretrain on all lobby tiers in the train period. Fine-tune on competitive matches in the train period. Val and test metrics are reported on competitive matches; pub val is diagnostic only.

### Out-of-fold residuals (FWAE, WPA, latency vs. expected)

A fight's residual must come from a fight model that didn't train on that fight's match. Otherwise the model has partly memorized the outcome, and residuals shrink toward zero unevenly.
- Within a training window, assign matches to 5 folds (`cross_fit_fold`), train on four, and score the fifth.
- For forecasting event *E*, the fight model is trained only on fights before *E*. Retraining at every origin is expensive, so retrain at monthly checkpoints. Features for *E* use the latest checkpoint whose training data ends before *E*'s date.

### Forecaster

- Expanding-window rolling origin. The minimum history before the first origin is set when the results backbone lands (default 10 events).
- Events on the origin date are never in training, since same-day sessions share information.
- Origins are divided once into a **dev period** (model and feature selection) and a **final test period** (the latest 25% of origins, reported once). The boundary date is fixed and recorded in Decisions when the results backbone lands.
- The held-out-player rule applies on top.

### Required leakage tests

Each feature builder or model that takes a cutoff gets a test in `tests/` showing that:
- changing or deleting data after the cutoff (fight `t0`, or event date) leaves its output unchanged;
- encoder and forecaster training sets contain no held-out players;
- split functions are deterministic (already covered).

## Evaluation protocol

- Splits as defined in [Data splits](#data-splits). No random splits anywhere.
- **Held-out players** are reported separately. This catches "embedding as a disguised player ID".
- **Fight models:** log loss, Brier, reliability curves, by season.
- **Forecaster:** NDCG@10 and @25, Spearman, log loss on top-k finish, with block bootstrap confidence intervals over events.
- **Gate rule:** a stage or feature is adopted only if it beats the current baseline on these, with the CI excluding 0.

## Decisions

| Date | Decision | Why |
|---|---|---|
| 2026-09-30 | Fight models exclude player identity | Otherwise the residual stops measuring skill |
| 2026-09-30 | Stage 1 snapshot at engagement start (first damage) | Avoids absorbing early-fight skill and makes leakage easy to audit. Sequences come in Stage 2 |
| 2026-09-30 | Embeddings enter the forecaster through a dimension sweep (0/2/4/8/16/64), comparing PCA with supervised reduction | A raw 64-d vector over a few hundred players risks acting as a disguised player ID. PCA may drop low-variance but predictive directions (e.g. latency drift) |
| 2026-09-30 | Fight model may train on all lobbies; player features and forecaster use pros only | "Which situation wins" doesn't need pro data |
| 2026-09-30 | Builder attribution: team at spawn → holding build tool (new pieces) → nearest | 95% team-blind accuracy on 1,142 labeled pieces (see README) |
| 2026-10-01 | Splits v1: 20% player holdout (`fnf-holdout-v1`), chronological 70/15/15 by match for fight models, 5-fold out-of-fold residuals (`fnf-folds-v1`), rolling origin by event date for the forecaster | Deterministic and reproducible across sessions. Out-of-fold residuals keep fight-skill features from being shrunk by memorization |
| 2026-10-01 | Fight-model splits move from match to tournament session once tournament data exists | Matches in one session share players and conditions |
| 2026-10-01 | Fights merge only on true time overlap (tolerance swept 0–3 s), not gap proximity | Gap-proximity merging made 38% of fights multi-team and chained unrelated back-to-back fights |
| 2026-10-01 | Pokes are a separate engagement type with their own outcomes (conversion, storm death, net damage, structure pressure) and skill measure (PVAE), plus zone and rotation context | Zone-edge poking of late rotators is a core competitive skill; counting pokes as failed fights would lose it |
| 2026-10-01 | All segmentation and poke thresholds are v1 (tuned on local Zero Build pub replays) and must be re-tuned and relabeled on competitive Build data before training models for pro features; tables carry `seg_version` | Build mode and competitive tempo change damage, gap and poke distributions |

## Open questions

- Do tournament server replays fill in piece `OwnerPersistentID` / `EditingPlayer`? If so, they replace inferred builders.
- What's the sanctioned source for tournament server replays at scale? See [data_sourcing.md](data_sourcing.md), section 2.
- Disengage outcome: resolved as its own class for fights; one-sided engagements are pokes with their own outcomes (1.1a).
- Poke thresholds: `POKE_MINORITY_SHARE`, `POKE_CONVERT_S`, and the structure-pressure radius. Set from competitive Build data.
- Does poke conversion credit the poker when a third team takes the knock? Proposed yes for team-level zone pressure, reported separately from self-converted pokes.
- How should duo/trio credit be split: by damage share or by Stage 2 WPA?

## Planned code layout

Existing: `schema.py` (all table schemas), `splits.py`, `quality.py`, `import_replays.py`, `telemetry.py`, `builds.py`, `build_tables.py`.

```
src/fnf/
  fights.py            # 1.1 segmentation v1 (replaces kill-feed v0)
  snapshot.py          # 1.2 features at t0
  models/fight_snapshot.py   # 1.3 logistic / LightGBM / set-model net
  features/fwae.py     # 1.4
  features/latency.py  # 1.5
  forecast/            # 1.6 ratings, ranker, hierarchical model, evaluation
  models/fight_seq.py  # Stage 2
  models/encoder.py    # Stage 3
```

New dependencies when Stage 1 modeling starts: `scikit-learn`, `lightgbm`, `torch`, `openskill`.
