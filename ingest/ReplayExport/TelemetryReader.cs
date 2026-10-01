using FortniteReplayReader;
using FortniteReplayReader.Models.NetFieldExports;
using FortniteReplayReader.Models.NetFieldExports.RPC;
using FortniteReplayReader.Models.NetFieldExports.Vehicles;
using Unreal.Core;
using Unreal.Core.Contracts;
using Unreal.Core.Models;
using Unreal.Core.Models.Enums;

namespace ReplayExport;

public record DamageRow(
    double T, uint SourceChannel, string? SourcePlayer, uint? HitActor, string? TargetPlayer,
    float? Magnitude, bool? Fatal, bool? Critical, bool? Shield, bool? ShieldDestroyed,
    bool? Ballistic, bool? WeaponActivate, double? X, double? Y, double? Z);

public class BuildRow
{
    public double SpawnT { get; init; }
    public uint Channel { get; init; }
    public required string Path { get; init; }
    public double? X { get; init; }
    public double? Y { get; init; }
    public double? Z { get; init; }
    public float? Yaw { get; init; }
    public double? CloseT { get; set; }
    public string? CloseReason { get; set; }

    // Decoded from the piece's replicated properties (BuildPieces.g.cs).
    public uint? OwnerPersistentId { get; set; }
    public int? TeamIndex { get; set; }
    public short? MaxHealth { get; set; }
    public short? MinHealth { get; set; }
    public bool? PlayerPlaced { get; set; }
    public HashSet<string> Editors { get; } = new();
}

public record HealthRow(double T, uint Channel, string? Player, float Health, float Shield);

public record TeamRow(double T, string Player, int TeamIndex);

public record WeaponRow(double T, uint Channel, string? Player, uint WeaponGuid);

public record PositionRow(
    double T, uint Channel, string? Player, double X, double Y, double Z, float? Yaw, float? Pitch,
    double? Vx, double? Vy, double? Vz, bool? Downed, bool? InStorm, bool? Targeting, bool? Crouched,
    bool? Sprinting, bool? Jumping, bool? Skydiving);

/// <summary>
/// The stock reader builds players, kill feed, teams and storm, but drops
/// damage cues and health, and on 2026 builds stamps everything with a
/// game-state clock that is never replicated (always 0). This subclass uses
/// the demo frame time instead, records positions, damage and health itself,
/// and resolves pawn channels to player ids at read time, since channels are
/// reused after an actor is destroyed.
/// </summary>
public class TelemetryReader() : ReplayReader(null, ParseMode.Full)
{
    public List<DamageRow> Damage { get; } = new();
    public List<HealthRow> Health { get; } = new();
    public List<PositionRow> Positions { get; } = new();
    public List<BuildRow> Builds { get; } = new();

    /// <summary>Team assignments over time; Creative modes reshuffle teams between rounds.</summary>
    public List<TeamRow> Teams { get; } = new();

    /// <summary>Held-item changes per pawn (building tool, weapons, pickaxe).</summary>
    public List<WeaponRow> Weapons { get; } = new();

    private readonly Dictionary<uint, string> _guidToClass = new();
    private readonly Dictionary<uint, uint> _lastWeapon = new();

    /// <summary>Class path of a spawned actor, by its network GUID.</summary>
    public string? ClassOf(uint guid) => _guidToClass.GetValueOrDefault(guid);

    /// <summary>Spawn count per actor class path, for discovering what a replay contains.</summary>
    public Dictionary<string, int> ActorClasses { get; } = new();

    // Player-built pieces: PBWA_<material><tier>_<shape>_C, e.g. PBWA_W1_Solid_C (wood wall),
    // PBWA_S1_StairW_C (brick stair), PBWA_W1_ArchwayLarge_C (edited wall).
    private const string PlayerBuildPrefix = "PBWA_";

    private double _time;
    private readonly Dictionary<uint, BuildRow> _openBuilds = new();
    private readonly Dictionary<uint, uint> _guidToChannel = new();
    private readonly Dictionary<uint, uint> _pawnToStateGuid = new();
    private readonly Dictionary<uint, string> _stateChannelToPlayer = new();

    public override void ReadDemoFrameIntoPlaybackPackets(FArchive archive)
    {
        // Peek the frame timestamp, then let the base reader consume the frame.
        var start = archive.Position;
        if (archive.NetworkVersion >= NetworkVersionHistory.HISTORY_MULTIPLE_LEVELS)
        {
            archive.ReadInt32();
        }
        _time = archive.ReadSingle();
        archive.Seek(start);

        base.ReadDemoFrameIntoPlaybackPackets(archive);
    }

    protected override void OnChannelOpened(uint channelIndex, NetworkGUID? actor)
    {
        if (actor != null)
        {
            _guidToChannel[actor.Value] = channelIndex;
            _pawnToStateGuid.Remove(channelIndex);
            _stateChannelToPlayer.Remove(channelIndex);
            _lastWeapon.Remove(channelIndex);
            RecordSpawn(channelIndex);
        }
        base.OnChannelOpened(channelIndex, actor);
    }

    /// <summary>
    /// Player-built pieces have no position property; their location and class
    /// (piece, material, edit variant) come from the actor spawn itself.
    /// </summary>
    private void RecordSpawn(uint channelIndex)
    {
        var spawned = Channels[channelIndex]?.Actor;
        if (spawned?.Archetype is null || !_netGuidCache.TryGetPathName(spawned.Archetype.Value, out var path))
        {
            return;
        }

        ActorClasses[path] = ActorClasses.GetValueOrDefault(path) + 1;
        _guidToClass[spawned.ActorNetGUID.Value] = path;
        if (!path.StartsWith(PlayerBuildPrefix))
        {
            return;
        }

        var row = new BuildRow
        {
            SpawnT = _time, Channel = channelIndex, Path = path,
            X = spawned.Location?.X, Y = spawned.Location?.Y, Z = spawned.Location?.Z, Yaw = spawned.Rotation?.Yaw,
        };
        Builds.Add(row);
        _openBuilds[channelIndex] = row;
    }

    public override bool ReceivedSequencedBunch(DataBunch bunch)
    {
        // Destroyed = the piece was broken, edited (replaced) or removed; Dormancy/Relevancy = it
        // just stopped replicating to this client.
        if (bunch.bClose && _openBuilds.Remove(bunch.ChIndex, out var row))
        {
            row.CloseT = _time;
            row.CloseReason = bunch.CloseReason.ToString();
        }
        return base.ReceivedSequencedBunch(bunch);
    }

    protected override void OnExportRead(uint channelIndex, INetFieldExportGroup? exportGroup)
    {
        switch (exportGroup)
        {
            case FortPlayerState state:
                var id = state.bIsABot == true ? state.BotUniqueId : state.UniqueId ?? state.UniqueID;
                if (string.IsNullOrEmpty(id) && state.bIsABot == true && ((int?)state.PlayerId ?? state.PlayerID) is int botNumber)
                {
                    id = BotId(botNumber);  // named NPC bots have no unique id
                }
                if (!string.IsNullOrEmpty(id)) _stateChannelToPlayer[channelIndex] = id;
                if (state.TeamIndex is int team && _stateChannelToPlayer.GetValueOrDefault(channelIndex) is string teamPlayer)
                {
                    Teams.Add(new TeamRow(_time, teamPlayer, team));
                }
                break;

            case PlayerPawn pawn:
                if (pawn.PlayerState.HasValue) _pawnToStateGuid[channelIndex] = pawn.PlayerState.Value;
                if (pawn.CurrentWeapon is uint weapon && _lastWeapon.GetValueOrDefault(channelIndex) != weapon)
                {
                    _lastWeapon[channelIndex] = weapon;
                    Weapons.Add(new WeaponRow(_time, channelIndex, PlayerForChannel(channelIndex), weapon));
                }
                if (pawn.ReplicatedMovement is FRepMovement m && m.Location != null)
                {
                    Positions.Add(new PositionRow(_time, channelIndex, PlayerForChannel(channelIndex),
                        m.Location.X, m.Location.Y, m.Location.Z, m.Rotation?.Yaw, m.Rotation?.Pitch,
                        m.LinearVelocity?.X, m.LinearVelocity?.Y, m.LinearVelocity?.Z,
                        pawn.bIsDBNO, pawn.bIsInAnyStorm, pawn.bIsTargeting, pawn.bIsCrouched,
                        pawn.bIsSprinting, pawn.bIsJumping, pawn.bIsSkydiving));
                }
                break;

            case BaseBuild piece when _openBuilds.TryGetValue(channelIndex, out var row):
                row.OwnerPersistentId = piece.OwnerPersistentID ?? row.OwnerPersistentId;
                row.TeamIndex = piece.TeamIndex ?? row.TeamIndex;
                row.MaxHealth = piece.MaxHealth ?? row.MaxHealth;
                row.PlayerPlaced = piece.bPlayerPlaced ?? row.PlayerPlaced;
                if (piece.Health is short hp && (row.MinHealth is null || hp < row.MinHealth)) row.MinHealth = hp;
                if (piece.EditingPlayer is { Value: > 0 } editor
                    && _guidToChannel.TryGetValue(editor.Value, out var editorChannel)
                    && PlayerForChannel(editorChannel) is string editorId)
                {
                    row.Editors.Add(editorId);
                }
                break;

            case HealthSet hs:
                Health.Add(new HealthRow(_time, channelIndex, PlayerForChannel(channelIndex),
                    hs.HealthCurrentValue, hs.ShieldCurrentValue));
                break;

            case BatchedDamageCues cue when cue.bIsValid != false:
                string? target = null;
                if (cue.HitActor is uint hit && _guidToChannel.TryGetValue(hit, out var targetChannel))
                {
                    target = PlayerForChannel(targetChannel);
                }
                Damage.Add(new DamageRow(_time, channelIndex, PlayerForChannel(channelIndex), cue.HitActor, target,
                    cue.Magnitude, cue.bIsFatal, cue.bIsCritical, cue.bIsShield, cue.bIsShieldDestroyed,
                    cue.bIsBallistic, cue.bWeaponActivate, cue.Location?.X, cue.Location?.Y, cue.Location?.Z));
                break;
        }

        base.OnExportRead(channelIndex, exportGroup);
    }

    /// <summary>Match-scoped id for bots without a unique id; must match players.csv.</summary>
    public static string BotId(int statePlayerId) => $"BOT_{statePlayerId}";

    /// <summary>Player id for a pawn channel, or for a player-state channel directly.</summary>
    private string? PlayerForChannel(uint channel)
    {
        if (_pawnToStateGuid.TryGetValue(channel, out var stateGuid)
            && _guidToChannel.TryGetValue(stateGuid, out var stateChannel)
            && _stateChannelToPlayer.TryGetValue(stateChannel, out var player))
        {
            return player;
        }
        return _stateChannelToPlayer.GetValueOrDefault(channel);
    }
}
