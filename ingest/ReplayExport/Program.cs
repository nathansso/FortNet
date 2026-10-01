// Export per-replay telemetry tables as CSV into data/interim/telemetry/<replay>/.
//
// Usage: dotnet run -c Release -- [replayDir] [outDir] [--force]

using System.Globalization;
using System.Text;
using FortniteReplayReader.Models;
using ReplayExport;

var positional = args.Where(a => !a.StartsWith("--")).ToArray();
var force = args.Contains("--force");
var root = FindRepoRoot();
var replayDir = positional.Length > 0 ? positional[0] : Path.Combine(root, "data", "raw", "replays");
var outRoot = positional.Length > 1 ? positional[1] : Path.Combine(root, "data", "interim", "telemetry");

var files = Directory.EnumerateFiles(replayDir, "*.replay").OrderBy(f => f).ToList();
int ok = 0, skipped = 0;
var failed = new List<string>();

foreach (var file in files)
{
    var name = Path.GetFileNameWithoutExtension(file);
    var outDir = Path.Combine(outRoot, name);
    if (!force && File.Exists(Path.Combine(outDir, "meta.csv")))
    {
        skipped++;
        continue;
    }

    try
    {
        var reader = new TelemetryReader();
        var replay = reader.ReadReplay(file);
        Directory.CreateDirectory(outDir);
        Export(replay, reader, outDir);
        ok++;
    }
    catch (Exception ex)
    {
        failed.Add($"{Path.GetFileName(file)}: {ex.GetType().Name}: {ex.Message}");
    }
}

Console.WriteLine($"Exported {ok}, skipped {skipped}, failed {failed.Count} of {files.Count}");
foreach (var f in failed) Console.WriteLine($"  FAILED {f}");

static void Export(FortniteReplay replay, TelemetryReader reader, string dir)
{
    var g = replay.GameData;
    var players = replay.PlayerData.ToList();
    // IsReplayOwner isn't set on 2026 builds. In a client replay only the
    // recorder's health set is replicated, so use the most frequent health owner.
    var owner = players.FirstOrDefault(p => p.IsReplayOwner)?.PlayerId
        ?? reader.Health.Where(h => h.Player != null).GroupBy(h => h.Player)
            .OrderByDescending(x => x.Count()).FirstOrDefault()?.Key
        // Some Creative modes don't replicate health; the recorder's own pawn updates most often.
        ?? reader.Positions.Where(r => r.Player != null).GroupBy(r => r.Player)
            .OrderByDescending(x => x.Count()).FirstOrDefault()?.Key;
    var s = replay.Stats;

    WriteCsv(Path.Combine(dir, "meta.csv"),
        ["branch", "session_id", "playlist", "utc_start", "match_end_time", "max_players", "team_size",
         "total_teams", "total_bots", "tournament_round", "winning_team", "aircraft_start", "replay_owner",
         "rec_eliminations", "rec_assists", "rec_accuracy", "rec_weapon_damage", "rec_other_damage",
         "rec_damage_taken", "rec_damage_to_structures", "rec_materials_gathered", "rec_materials_used",
         "rec_total_traveled", "rec_revives"],
        [[replay.Header.Branch, g.GameSessionId, g.CurrentPlaylist, g.UtcTimeStartedMatch?.ToString("o"), g.MatchEndTime,
          g.MaxPlayers, g.TeamSize, g.TotalTeams, g.TotalBots, g.TournamentRound, g.WinningTeam, g.AircraftStartTime, owner,
          s?.Eliminations, s?.Assists, s?.Accuracy, s?.WeaponDamage, s?.OtherDamage, s?.DamageTaken,
          s?.DamageToStructures, s?.MaterialsGathered, s?.MaterialsUsed, s?.TotalTraveled, s?.Revives]]);

    WriteCsv(Path.Combine(dir, "players.csv"),
        ["player_id", "name", "is_bot", "team_index", "placement", "kills", "team_kills", "is_replay_owner",
         "state_player_id", "world_player_id",
         "platform", "death_time", "death_cause", "death_x", "death_y", "death_z"],
        players.Select(p => new object?[] {
            p.PlayerId, p.PlayerName, p.IsBot, p.TeamIndex, p.Placement, p.Kills, p.TeamKills, p.IsReplayOwner,
            p.Id, p.PlayerNumber,
            p.Platform, p.DeathTimeDouble ?? p.DeathTime, p.DeathCause, p.DeathLocation?.X, p.DeathLocation?.Y, p.DeathLocation?.Z }));

    WriteCsv(Path.Combine(dir, "positions.csv"),
        ["t", "channel", "player_id", "x", "y", "z", "yaw", "pitch", "vx", "vy", "vz",
         "downed", "in_storm", "targeting", "crouched", "sprinting", "jumping", "skydiving"],
        reader.Positions.Select(r => new object?[] {
            r.T, r.Channel, r.Player, r.X, r.Y, r.Z, r.Yaw, r.Pitch, r.Vx, r.Vy, r.Vz,
            r.Downed, r.InStorm, r.Targeting, r.Crouched, r.Sprinting, r.Jumping, r.Skydiving }));

    // Replay events carry a reliable timestamp (ms) and both players' locations;
    // the stock KillFeed is stamped with the never-replicated game-state clock.
    WriteCsv(Path.Combine(dir, "eliminations.csv"),
        ["t", "eliminated", "eliminator", "knocked", "gun_type", "distance",
         "victim_x", "victim_y", "victim_z", "actor_x", "actor_y", "actor_z"],
        replay.Eliminations.Select(e => new object?[] {
            e.Info.StartTime / 1000.0, e.Eliminated, e.Eliminator, e.Knocked, e.GunType, e.Distance,
            e.EliminatedInfo.Location?.X, e.EliminatedInfo.Location?.Y, e.EliminatedInfo.Location?.Z,
            e.EliminatorInfo.Location?.X, e.EliminatorInfo.Location?.Y, e.EliminatorInfo.Location?.Z }));

    WriteCsv(Path.Combine(dir, "damage.csv"),
        ["t", "source_channel", "source", "hit_actor", "target", "magnitude", "fatal", "critical", "shield",
         "shield_destroyed", "ballistic", "weapon_activate", "x", "y", "z"],
        reader.Damage.Select(d => new object?[] {
            d.T, d.SourceChannel, d.SourcePlayer, d.HitActor, d.TargetPlayer, d.Magnitude, d.Fatal, d.Critical,
            d.Shield, d.ShieldDestroyed, d.Ballistic, d.WeaponActivate, d.X, d.Y, d.Z }));

    WriteCsv(Path.Combine(dir, "health.csv"),
        ["t", "channel", "player_id", "health", "shield"],
        reader.Health.Select(h => new object?[] { h.T, h.Channel, h.Player, h.Health, h.Shield }));

    WriteCsv(Path.Combine(dir, "builds.csv"),
        ["spawn_t", "channel", "path", "x", "y", "z", "yaw", "close_t", "close_reason",
         "owner_persistent_id", "team_index", "max_health", "min_health", "player_placed", "editors"],
        reader.Builds.Select(b => new object?[] {
            b.SpawnT, b.Channel, b.Path, b.X, b.Y, b.Z, b.Yaw, b.CloseT, b.CloseReason,
            b.OwnerPersistentId, b.TeamIndex, b.MaxHealth, b.MinHealth, b.PlayerPlaced, string.Join(';', b.Editors) }));

    WriteCsv(Path.Combine(dir, "teams.csv"),
        ["t", "player_id", "team_index"],
        reader.Teams.Select(r => new object?[] { r.T, r.Player, r.TeamIndex }));

    WriteCsv(Path.Combine(dir, "weapons.csv"),
        ["t", "channel", "player_id", "weapon_guid", "weapon_class"],
        reader.Weapons.Select(w => new object?[] { w.T, w.Channel, w.Player, w.WeaponGuid, reader.ClassOf(w.WeaponGuid) }));

    WriteCsv(Path.Combine(dir, "actor_classes.csv"),
        ["path", "spawns"],
        reader.ActorClasses.OrderByDescending(kv => kv.Value).Select(kv => new object?[] { kv.Key, kv.Value }));

    WriteCsv(Path.Combine(dir, "safezones.csv"),
        ["start_shrink", "finish_shrink", "radius", "next_radius", "next_x", "next_y"],
        replay.MapData.SafeZones.Select(z => new object?[] {
            z.StartShrinkTime, z.FinishShrinkTime, z.Radius, z.NextRadius, z.NextCenter?.X, z.NextCenter?.Y }));
}

static void WriteCsv(string path, string[] header, IEnumerable<object?[]> rows)
{
    var sb = new StringBuilder();
    sb.AppendLine(string.Join(',', header));
    foreach (var row in rows) sb.AppendLine(string.Join(',', row.Select(Format)));
    File.WriteAllText(path, sb.ToString());
}

static string Format(object? v) => v switch
{
    null => "",
    bool b => b ? "1" : "0",
    string s => s.Contains(',') || s.Contains('"') || s.Contains('\n') ? $"\"{s.Replace("\"", "\"\"")}\"" : s,
    IFormattable f => f.ToString(null, CultureInfo.InvariantCulture),
    _ => v.ToString() ?? "",
};

static string FindRepoRoot()
{
    var dir = new DirectoryInfo(AppContext.BaseDirectory);
    while (dir != null && !File.Exists(Path.Combine(dir.FullName, "pyproject.toml"))) dir = dir.Parent;
    return dir?.FullName ?? Directory.GetCurrentDirectory();
}
