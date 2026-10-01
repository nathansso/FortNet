# Architecture: from fights to placement forecasts

Status: plan, agreed 2026-09-30. Stage 1 is the active work. Stages 2 and 3 are designed but gated on data (see "Entry criteria" in each).

## Goal

Forecast each pro's placement percentile at the next Major or LAN, using only information from before that event. Then test whether age predicts decline once fight skill, reaction latency, tenure, debut cohort, format era and activity are controlled for. Background and literature: [research/literature_review.md](research/literature_review.md).

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

### Data handling

Replays contain account IDs and display names, and many pros are minors. `data/` is never committed. Only aggregated results are published.

## Stage 1: snapshot fight model and FWAE

### 1.1 Fight segmentation (replaces kill-feed v0)

Source: the `damage`, `positions`, `teams`, `elims` and `players` tables.

- **Engagement:** player-to-player damage (`target` not null, `source != target`, `magnitude > 0`) between two teams, using `teams` as of the event time.
- **Grouping:** within a match, link damage events between the same pair of teams when they're ≤ `GAP_S` apart (start with 10 s, tune by inspection). Third-party damage within the window merges in as a multi-team fight. Version 1 keeps two-team fights only and flags the rest.
- **Engagement start** `t0`: the first damage event of the fight. Snapshot features are taken at `t0`, before any damage resolves.
- **Outcome label (per team):**
  - `win` = the opponent team has a member knocked or eliminated first, and this team doesn't.
  - `loss` = the reverse.
  - `disengage` = no knock within the fight. Excluded from the v1 training target and counted separately.
  - Ties (both knocked within 1 s) are dropped.
- **Output table** `fight_sides`: one row per (fight, team), with participants, `t0`, end, outcome and multi-team flag.

Current data: 36k player-to-player damage events across 98 client replays, enough to build and debug segmentation. Distant fights are missing because of relevancy.

### 1.2 Snapshot features at `t0`

Per side (sum/mean/max over the team's players present), plus differences between sides:

| Group | Features | Source / caveat |
|---|---|---|
| Numbers | players alive per team, players engaged | `teams`, `players` death times |
| Health | health + shield | `health` is recorder-only in client replays: use a missing flag plus damage taken since last known value. Full coverage expected in server replays |
| Geometry | horizontal distance, height difference, closing speed, facing angle toward opponent | `positions` |
| Loadout | held item class at `t0` (shotgun / AR / SMG / sniper / build tool / other) | `weapons` |
| Cover | own and enemy pieces within 2 tiles, pieces between the sides, high-ground pieces | `pieces` |
| Context | storm phase, distance to next safe zone, time into match, other teams within N m (third-party risk), season/patch | `safezones`, `matches` |

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

## Evaluation protocol

- **Rolling-origin by event date:** train on everything before event *E*, predict *E*, then advance. No random splits anywhere.
- **Held-out players:** a fixed 20% of pros excluded from all training, evaluated separately. This catches "embedding as a disguised player ID".
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

## Open questions

- Do tournament server replays fill in piece `OwnerPersistentID` / `EditingPlayer`? If so, they replace inferred builders.
- What's the sanctioned source for tournament server replays at scale? (README, Next steps.)
- What's the right outcome label for fights that end in disengagement: exclude, a third class, or net damage?
- How should duo/trio credit be split: by damage share or by Stage 2 WPA?

## Planned code layout

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
