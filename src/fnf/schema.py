"""Authoritative data schema for every table in the pipeline.

This module is the single source of truth. docs/data_schema.md is generated
from it (`uv run fnf-schema-doc`), and a test fails if the doc is stale.

Conventions (apply to every table):
- match_id: the replay file stem, e.g. "UnsavedReplay-2026.09.21-20.53.39".
- player_id: Epic account ID, 32 uppercase hex chars. Bots: the bot's unique id, or
  "BOT_<state_player_id>" (match-scoped) for named NPC bots that have none.
- t: seconds since replay start (demo frame clock). Event-derived times
  (t_ms) use the same clock in milliseconds; aligned to ~15 ms.
- Positions are Unreal units (1 uu = 1 cm). Build grid: 512 uu horizontal,
  384 uu vertical. Angles in degrees.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd

from fnf import DATA, ROOT

@dataclass(frozen=True)
class Col:
    name: str
    type: str  # string | float | int | bool
    nullable: bool = False
    desc: str = ""
    unit: str = ""


@dataclass(frozen=True)
class Table:
    name: str
    layer: str  # raw | interim | processed
    path: str
    grain: str
    key: tuple[str, ...]
    columns: tuple[Col, ...]
    desc: str = ""
    status: str = "built"  # built | planned
    notes: tuple[str, ...] = field(default=())

    @property
    def column_names(self) -> list[str]:
        return [c.name for c in self.columns]


def _c(name, type_, nullable=False, desc="", unit=""):
    return Col(name, type_, nullable, desc, unit)


MATCH_ID = _c("match_id", "string", desc="Replay file stem")
T = _c("t", "float", desc="Time since replay start", unit="s")
XYZ = (_c("x", "float", unit="uu"), _c("y", "float", unit="uu"), _c("z", "float", unit="uu"))
XYZ_NULL = tuple(Col(c.name, c.type, True, c.desc, c.unit) for c in XYZ)

_REC_STATS = tuple(
    _c(f"rec_{n}", t, True, "Recorder's end-of-match stat (AthenaMatchStats event)")
    for n, t in [
        ("eliminations", "int"), ("assists", "int"), ("accuracy", "float"), ("weapon_damage", "int"),
        ("other_damage", "int"), ("damage_taken", "int"), ("damage_to_structures", "int"),
        ("materials_gathered", "int"), ("materials_used", "int"), ("total_traveled", "int"), ("revives", "int"),
    ]
)

_BUILD_COLS = (
    _c("spawn_t", "float", desc="Piece spawn time (predicted spawn time if one preceded it)", unit="s"),
    _c("channel", "int", desc="Actor channel index (reused after close)"),
    _c("path", "string", desc="Actor class, PBWA_<material><tier>_<shape>_C"),
    *XYZ,
    _c("yaw", "float", desc="Piece rotation", unit="deg"),
    _c("close_t", "float", True, "Channel close time; null if open at replay end", "s"),
    _c("close_reason", "string", True, "Destroyed (broken/edited/removed) | Dormancy | Relevancy | ..."),
    _c("owner_persistent_id", "int", True, "Builder field; empty in client replays"),
    _c("team_index", "int", True, "Team that owns the piece (null on predicted spawns)"),
    _c("max_health", "int", True),
    _c("min_health", "int", True, "Lowest health seen (damage taken)"),
    _c("player_placed", "bool", True),
    _c("editors", "string", True, "Editing players, ';'-separated; empty in client replays"),
)

TABLES: dict[str, Table] = {}


def _add(t: Table) -> None:
    TABLES[t.name] = t


# ---------------------------------------------------------------- raw
_add(Table(
    "manifest", "raw", "data/raw/manifest.csv", "replay file", ("replay_file",),
    desc="Provenance of every replay in data/raw/replays. Written by fnf-import; never edited by hand.",
    columns=(
        _c("replay_file", "string", desc="File name in data/raw/replays"),
        _c("sha256", "string", desc="Content hash; duplicates are skipped on import"),
        _c("size_bytes", "int"),
        _c("source", "string", desc="local_demos | donated | tournament_ingame | partner_osirion | partner_other"),
        _c("replay_kind", "string", desc="client (recorder's view) | server (whole island) | unknown"),
        _c("contributor", "string", True, "Pseudonymous contributor id (never a real name)"),
        _c("consent_ref", "string", True, "Consent record id; required for donated replays"),
        _c("acquired_at", "string", desc="UTC ISO-8601 import time"),
        _c("notes", "string", True),
    ),
))

# ---------------------------------------------------------------- interim (per-replay CSVs) + processed
_add(Table(
    "matches", "processed", "data/processed/matches.parquet", "replay", ("match_id",),
    desc="One row per replay. Interim file: meta.csv.",
    columns=(
        MATCH_ID,
        _c("branch", "string", desc="Game build, e.g. ++Fortnite+Release-42.20"),
        _c("session_id", "string", True, "Epic game session id"),
        _c("playlist", "string", True, "e.g. Playlist_RopeSmileNoBuildDuo; null in some Creative modes"),
        _c("utc_start", "string", True, "Match start, UTC ISO-8601"),
        _c("match_end_time", "float", True, unit="s"),
        _c("max_players", "int", True),
        _c("team_size", "int", True, "Unreliable on 2026 builds (decodes to ~11-33); derive team size from teams"),
        _c("total_teams", "int", True),
        _c("total_bots", "int", True), _c("tournament_round", "int", True), _c("winning_team", "int", True),
        _c("aircraft_start", "float", True, unit="s"),
        _c("replay_owner", "string", True, "Recorder's player_id (inferred: health owner, else most position updates)"),
        *_REC_STATS,
    ),
))
_add(Table(
    "players", "processed", "data/processed/players.parquet", "match x player", ("match_id", "player_id"),
    columns=(
        MATCH_ID, _c("player_id", "string"), _c("name", "string", True, "Display name at match time"),
        _c("is_bot", "bool"), _c("team_index", "int", True, "Final team (see teams for history)"),
        _c("placement", "int", True), _c("kills", "int", True), _c("team_kills", "int", True),
        _c("is_replay_owner", "bool", desc="Not set by 2026 builds; use matches.replay_owner"),
        _c("state_player_id", "int", True), _c("world_player_id", "int", True), _c("platform", "string", True),
        _c("death_time", "float", True, unit="s"), _c("death_cause", "int", True),
        _c("death_x", "float", True, unit="uu"), _c("death_y", "float", True, unit="uu"), _c("death_z", "float", True, unit="uu"),
    ),
))
_add(Table(
    "positions", "processed", "data/processed/positions.parquet", "pawn update", (),
    desc="Every replicated pawn movement update.",
    notes=("Flags are null when not replicated in that update (unchanged), not false.",),
    columns=(
        MATCH_ID, T, _c("channel", "int", desc="Pawn actor channel"), _c("player_id", "string", True),
        *XYZ, _c("yaw", "float", True, unit="deg"), _c("pitch", "float", True, unit="deg"),
        _c("vx", "float", True, unit="uu/s"), _c("vy", "float", True, unit="uu/s"), _c("vz", "float", True, unit="uu/s"),
        _c("downed", "bool", True), _c("in_storm", "bool", True), _c("targeting", "bool", True, "Aiming down sights"),
        _c("crouched", "bool", True), _c("sprinting", "bool", True), _c("jumping", "bool", True),
        _c("skydiving", "bool", True),
    ),
))
_add(Table(
    "damage", "processed", "data/processed/damage.parquet", "damage cue", (),
    desc="NetMulticast_Athena_BatchedDamageCues, called on the instigator's pawn.",
    notes=("Validated: recorder's damage to players vs. game stats r=0.93, median ratio 1.01 (95 matches).",),
    columns=(
        MATCH_ID, T, _c("source_channel", "int"), _c("source", "string", True, "Instigator player_id"),
        _c("hit_actor", "int", True, "Hit actor network GUID"),
        _c("target", "string", True, "Hit player_id; null = non-player hit (structures, props)"),
        _c("magnitude", "float", desc="Damage amount"), _c("fatal", "bool", True), _c("critical", "bool", True, "Headshot"),
        _c("shield", "bool", True, "Hit absorbed by shield"), _c("shield_destroyed", "bool", True),
        _c("ballistic", "bool", True), _c("weapon_activate", "bool", True), *XYZ_NULL,
    ),
))
_add(Table(
    "health", "processed", "data/processed/health.parquet", "health change", (),
    notes=("Client replays: recorder (and sometimes spectated teammates) only.",),
    columns=(MATCH_ID, T, _c("channel", "int"), _c("player_id", "string", True),
             _c("health", "float"), _c("shield", "float")),
))
_add(Table(
    "eliminations", "interim", "data/interim/telemetry/<match_id>/eliminations.csv", "knock or elimination", (),
    desc="Replay elimination events. Processed into the elims table.",
    notes=("victim_*/actor_* locations decode incorrectly on 2026 builds; use positions at t instead.",),
    columns=(
        T, _c("eliminated", "string", True), _c("eliminator", "string", True), _c("knocked", "bool"),
        _c("gun_type", "int", True, "Weapon class enum"), _c("distance", "float", True, unit="uu"),
        _c("victim_x", "float", True), _c("victim_y", "float", True), _c("victim_z", "float", True),
        _c("actor_x", "float", True), _c("actor_y", "float", True), _c("actor_z", "float", True),
    ),
))
_add(Table(
    "elims", "processed", "data/processed/elims.parquet", "knock or elimination", (),
    columns=(MATCH_ID, _c("t_ms", "int", unit="ms"), _c("eliminator", "string", True), _c("eliminated", "string", True),
             _c("knocked", "bool"), _c("gun_type", "string", True), _c("fight_id", "string", desc="Kill-feed fight v0")),
))
_add(Table(
    "builds", "interim", "data/interim/telemetry/<match_id>/builds.csv", "piece actor spawn", (),
    desc="Raw build-piece spawns. Processed into pieces.",
    columns=_BUILD_COLS,
))
_add(Table(
    "pieces", "processed", "data/processed/pieces.parquet", "build piece", (),
    desc="Deduplicated pieces with edits and inferred builder (fnf.builds).",
    columns=(
        MATCH_ID, *_BUILD_COLS,
        _c("material", "string", True, "wood | brick | metal"), _c("shape", "string", True),
        _c("kind", "string", True, "wall | floor | stair | cone"), _c("edited", "bool", desc="Shape is an edit variant"),
        _c("prev_shape", "string", True), _c("prev_close_t", "float", True, unit="s"),
        _c("is_edit", "bool"), _c("is_reset", "bool"),
        _c("builder", "string", True), _c("builder_dist", "float", desc="Builder distance at spawn (inf if none)", unit="uu"),
        _c("builder_source", "string", True, "team | team+tool | team+nearest | tool | nearest"),
    ),
))
_add(Table(
    "teams", "processed", "data/processed/teams.parquet", "team assignment update", (),
    columns=(MATCH_ID, T, _c("player_id", "string"), _c("team_index", "int")),
))
_add(Table(
    "weapons", "processed", "data/processed/weapons.parquet", "held-item change", (),
    columns=(MATCH_ID, T, _c("channel", "int"), _c("player_id", "string", True), _c("weapon_guid", "int"),
             _c("weapon_class", "string", True, "e.g. DefaultBuildingTool_C; null if the item actor was never seen")),
))
_add(Table(
    "safezones", "processed", "data/processed/safezones.parquet", "storm phase", (),
    columns=(MATCH_ID, _c("start_shrink", "float", unit="s"), _c("finish_shrink", "float", unit="s"),
             _c("radius", "float", unit="uu"), _c("next_radius", "float", unit="uu"),
             _c("next_x", "float", True, unit="uu"), _c("next_y", "float", True, unit="uu")),
))
_add(Table(
    "actor_classes", "interim", "data/interim/telemetry/<match_id>/actor_classes.csv", "actor class", ("path",),
    desc="Spawn count per actor class; use it to find new PBWA_* shapes (ingest/gen_build_pieces.py).",
    columns=(_c("path", "string"), _c("spawns", "int")),
))
_add(Table(
    "fights", "processed", "data/processed/fights.parquet", "fight (kill-feed v0)", ("fight_id",),
    columns=(_c("fight_id", "string"), MATCH_ID, _c("t_start_ms", "int", unit="ms"), _c("t_end_ms", "int", unit="ms"),
             _c("n_events", "int"), _c("n_knocks", "int"), _c("n_elims", "int"), _c("duration_ms", "int", unit="ms"),
             _c("n_players", "int")),
))
_add(Table(
    "player_fights", "processed", "data/processed/player_fights.parquet", "fight x player", ("fight_id", "player"),
    columns=(_c("fight_id", "string"), _c("player", "string"), _c("knocks_dealt", "int"), _c("knocks_recv", "int"),
             _c("elims_dealt", "int"), _c("elims_recv", "int"), _c("lost", "bool")),
))

# ---------------------------------------------------------------- planned (Stage 1 and results backbone)
_add(Table(
    "fight_sides", "processed", "data/processed/fight_sides.parquet", "fight x team", ("fight_id", "team_index"),
    desc="Damage-based fights (architecture 1.1, src/fnf/fights.py): player-to-player damage between teams, "
         "segmented per team pair, merged into fights when segments sharing a team overlap in time.",
    columns=(
        _c("fight_id", "string", desc="f'{match_id}:{n}', n in t0 order within the match; deterministic"),
        MATCH_ID, _c("team_index", "int", desc="This side's team (at hit time)"),
        _c("opp_team_index", "int", desc="Primary opponent: the other fight team this side exchanged the most damage with"),
        _c("t0", "float", desc="Engagement start: first engagement damage of the fight (same for all sides)", unit="s"),
        _c("t_end", "float", desc="Last engagement damage of the fight", unit="s"),
        _c("players", "string", desc="';'-separated player_ids of this side that dealt or took engagement damage"),
        _c("outcome", "string", desc="win | loss | tie | disengage (first opposing-team knock in [t0, t_end + GRACE_S] decides)"),
        _c("multi_team", "bool", desc="More than two teams in the fight; excluded from v1 training"),
        _c("n_damage_events", "int", desc="Engagement damage events involving this side (dealt or taken)"),
        _c("hits_dealt", "int", desc="Engagement hits this side landed on the fight's other teams"),
        _c("hits_taken", "int", desc="Engagement hits this side took from the fight's other teams"),
        _c("damage_dealt", "float", desc="Damage this side dealt to the fight's other teams"),
        _c("damage_taken", "float", desc="Damage this side took from the fight's other teams"),
        _c("recorder_involved", "bool", desc="matches.replay_owner is among the fight's engaged players (any side)"),
        _c("has_bots", "bool", desc="Any engaged player in the fight (any side) is a bot"),
        _c("mutual", "bool", desc="Fight-level: at least two teams dealt player damage"),
        _c("minority_damage_share", "float",
           desc="Fight-level: second-largest dealing team's share of the fight's total damage (0 if one-sided)"),
        _c("engagement_type", "string",
           desc="Fight-level: fight | poke. Poke = not mutual, or minority_damage_share < POKE_MINORITY_SHARE; never dropped"),
        _c("dist_median_m", "float", True, "Fight-level: median shooter-target distance over hits; null if positions unknown", "m"),
        _c("dist_max_m", "float", True, "Fight-level: max shooter-target distance over hits; null if positions unknown", "m"),
        _c("seg_version", "string", desc="Parameter set that produced this row, e.g. v1-gap10-tol1-grace3-poke10-conv20"),
    ),
))
_add(Table(
    "pokes", "processed", "data/processed/pokes.parquet", "poke (fight_sides.engagement_type = poke)", ("fight_id",),
    desc="Outcome labels for pokes (architecture 1.1a, src/fnf/pokes.py). Labels look ahead of the poke by "
         "POKE_CONVERT_S by design; the poke's own t0, players and type never do.",
    notes=("v1 thresholds, tuned on local Zero Build pub replays; re-tune on competitive Build data.",),
    columns=(
        _c("fight_id", "string"), MATCH_ID,
        _c("poker_team", "int", desc="Team that dealt the most damage in the poke"),
        _c("target_team", "int", desc="Team the poker dealt the most damage to"),
        _c("t0", "float", desc="Poke start (first engagement damage)", unit="s"),
        _c("t_end", "float", desc="Last engagement damage of the poke", unit="s"),
        _c("net_damage", "float", desc="Damage the poker dealt to the target team minus damage taken back"),
        _c("target_players", "string", desc="';'-separated player_ids the poker hit"),
        _c("converted", "bool", desc="A target player was knocked or eliminated, by anyone, in [t0, t_end + POKE_CONVERT_S]"),
        _c("converted_by", "string", True, "poker | third_party | environment (storm, fall, self); null if not converted"),
        _c("converter_team", "int", True, "Team of the eliminator when converted_by is poker or third_party"),
        _c("t_convert", "float", True, "Seconds from t_end to the first conversion event (negative: during the poke)", "s"),
        _c("storm_death", "bool", desc="A target player died in the window with in_storm true at their last known flag"),
        _c("structure_damage", "float",
           desc="Damage by the poker team to structures within 2 tiles of a target player during the poke"),
        _c("structure_hits", "int", desc="Number of such structure hits (Build matches only in practice)"),
        _c("seg_version", "string", desc="Parameter set that produced this row"),
    ),
))
_add(Table(
    "events", "processed", "data/processed/events.parquet", "competitive event", ("event_id",),
    status="planned", desc="Results backbone: tournaments/sessions to forecast.",
    columns=(
        _c("event_id", "string"), _c("name", "string"), _c("date", "string", desc="UTC date, ISO-8601"),
        _c("region", "string", True), _c("format", "string", desc="solo | duo | trio | squad"),
        _c("is_lan", "bool"), _c("tier", "string", desc="major | lan | qualifier | cash_cup | other"),
        _c("source", "string"), _c("source_key", "string"),
    ),
))
_add(Table(
    "event_results", "processed", "data/processed/event_results.parquet", "event x player", ("event_id", "player_id"),
    status="planned",
    columns=(
        _c("event_id", "string"), _c("player_id", "string"), _c("team_key", "string", desc="Team within the event"),
        _c("placement", "int"), _c("field_size", "int"), _c("points", "float", True), _c("earnings_usd", "float", True),
    ),
))
_add(Table(
    "player_xref", "processed", "data/processed/player_xref.parquet", "player x external id", ("source", "source_key"),
    status="planned", desc="Maps external identities (Liquipedia, Cito, display names) to player_id.",
    columns=(
        _c("player_id", "string"), _c("source", "string"), _c("source_key", "string"),
        _c("valid_from", "string", True), _c("valid_to", "string", True), _c("confidence", "string", desc="exact | manual | fuzzy"),
    ),
))
_add(Table(
    "player_meta", "processed", "data/processed/player_meta.parquet", "player", ("player_id",),
    status="planned", desc="Career attributes for the forecaster.",
    columns=(
        _c("player_id", "string"), _c("display_name", "string"), _c("birth_date", "string", True),
        _c("birth_date_source", "string", True, "URL or citation"), _c("debut_date", "string", True),
        _c("region", "string", True),
    ),
))


# ---------------------------------------------------------------- enforcement
def _to_bool(s: pd.Series) -> pd.Series:
    mapping = {"1": True, "0": False, "true": True, "false": False}
    if s.dtype == object or pd.api.types.is_string_dtype(s):
        s = s.map(lambda v: mapping.get(str(v).strip().lower()) if pd.notna(v) and str(v).strip() != "" else pd.NA)
    return s.astype("boolean")


def coerce(df: pd.DataFrame, table: str) -> pd.DataFrame:
    """Cast known columns to their schema dtypes. Unknown columns are left as is."""
    spec = TABLES[table]
    out = df.copy()
    for col in spec.columns:
        if col.name not in out:
            continue
        s = out[col.name]
        if col.type == "bool":
            s = _to_bool(s)
            if not col.nullable and not s.isna().any():
                s = s.astype(bool)
        elif col.type == "int":
            s = pd.to_numeric(s, errors="coerce").round().astype("Int64")
            if not col.nullable and not s.isna().any():
                s = s.astype("int64")
        elif col.type == "float":
            s = pd.to_numeric(s, errors="coerce").astype("float64")
        else:
            s = s.astype("string")
        out[col.name] = s
    return out


def validate(df: pd.DataFrame, table: str) -> list[str]:
    """Problems with df against the schema; empty list means valid."""
    spec = TABLES[table]
    problems = []
    missing = [c for c in spec.column_names if c not in df]
    extra = [c for c in df if c not in spec.column_names]
    if missing:
        problems.append(f"{table}: missing columns {missing}")
    if extra:
        problems.append(f"{table}: undeclared columns {extra}")
    for col in spec.columns:
        if col.name not in df:
            continue
        s = df[col.name]
        if not col.nullable and s.isna().any():
            problems.append(f"{table}.{col.name}: {int(s.isna().sum())} nulls in non-nullable column")
        ok = {
            "bool": pd.api.types.is_bool_dtype(s),
            "int": pd.api.types.is_integer_dtype(s),
            "float": pd.api.types.is_float_dtype(s),
            "string": pd.api.types.is_string_dtype(s) or s.dtype == object,
        }[col.type]
        if not ok and not (len(s) and s.isna().all()):
            problems.append(f"{table}.{col.name}: dtype {s.dtype}, expected {col.type}")
    if spec.key and not missing and df.duplicated(list(spec.key)).any():
        problems.append(f"{table}: duplicate keys on {spec.key}")
    return problems


# ---------------------------------------------------------------- docs
def render_markdown() -> str:
    lines = [
        "# Data schema",
        "",
        "<!-- Generated by `uv run fnf-schema-doc` from src/fnf/schema.py. Do not edit by hand. -->",
        "",
        "Every table the pipeline reads or writes. `src/fnf/schema.py` is authoritative: tables are",
        "cast with `schema.coerce` on load and checked with `schema.validate` before they're written.",
        "",
        "## Conventions",
        "",
        "- `match_id`: replay file stem, e.g. `UnsavedReplay-2026.09.21-20.53.39`.",
        "- `player_id`: Epic account ID, 32 uppercase hex characters. Bots: the bot's unique id, or `BOT_<state_player_id>`",
        "  (match-scoped) for named NPC bots that have none.",
        "- `t`: seconds since replay start (demo frame clock). `t_ms` is the same clock in ms (aligned to ~15 ms).",
        "- Positions in Unreal units (1 uu = 1 cm). Build grid: 512 uu horizontal, 384 uu vertical. Angles in degrees.",
        "- Interim per-replay CSVs (`data/interim/telemetry/<match_id>/<table>.csv`) have the processed columns minus `match_id`",
        "  (the folder name). `meta.csv` becomes `matches`; `eliminations.csv` becomes `elims`; `builds.csv` becomes `pieces`.",
        "- Types: `string`, `int`, `float`, `bool`. Nullable columns are marked; a null boolean flag means \"not replicated in",
        "  this update\", not false.",
        "",
    ]
    for layer in ("raw", "interim", "processed"):
        for status in ("built", "planned"):
            tables = [t for t in TABLES.values() if t.layer == layer and t.status == status]
            if not tables:
                continue
            title = {"raw": "Raw", "interim": "Interim (per-replay)", "processed": "Processed"}[layer]
            lines += [f"## {title}{' (planned)' if status == 'planned' else ''}", ""]
            for t in tables:
                lines += [f"### `{t.name}`", "", f"`{t.path}`. Grain: {t.grain}."
                          + (f" Key: `{', '.join(t.key)}`." if t.key else ""), ""]
                if t.desc:
                    lines += [t.desc, ""]
                for n in t.notes:
                    lines += [f"> {n}", ""]
                lines += ["| column | type | null | unit | description |", "|---|---|---|---|---|"]
                for c in t.columns:
                    desc = c.desc.replace("|", r"\|")  # literal pipes would split the Markdown cell
                    lines.append(f"| `{c.name}` | {c.type} | {'yes' if c.nullable else ''} | {c.unit} | {desc} |")
                lines.append("")
    return "\n".join(lines).rstrip() + "\n"


DOC_PATH = ROOT / "docs" / "data_schema.md"


def write_doc() -> None:
    DOC_PATH.write_text(render_markdown(), encoding="utf-8")
    print(f"wrote {DOC_PATH}")


def validate_processed() -> None:
    """CLI: validate every built processed table on disk (and the raw manifest)."""
    ap = argparse.ArgumentParser(description=validate_processed.__doc__)
    ap.parse_args()
    bad = 0
    for t in TABLES.values():
        if t.status != "built" or t.layer == "interim":
            continue
        p = DATA / t.path.removeprefix("data/")
        if not p.exists():
            print(f"skip   {t.name} (no {t.path})")
            continue
        df = pd.read_parquet(p) if p.suffix == ".parquet" else coerce(pd.read_csv(p), t.name)
        problems = validate(df, t.name)
        bad += bool(problems)
        print(("ok     " if not problems else "FAIL   ") + f"{t.name} ({len(df)} rows)")
        for msg in problems:
            print(f"       {msg}")
    raise SystemExit(1 if bad else 0)

