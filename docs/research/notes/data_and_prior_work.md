# Data Sources and Prior Prediction Work for Fortnite Pro Performance (as of Sept 2026)

Research note: several primary pages (fortnite.com PR info page, tracker.gg developer docs, Liquipedia pages and API guidelines, Epic help center, the ScienceDirect LoL career paper, the Kaggle 1st-place writeup body) returned HTTP 403 to automated fetches. Where that happened, claims below rely on search-result snippets from those same URLs and are flagged as such.

## Q1. Where can a data scientist get historical per-player competitive results and in-game telemetry for Fortnite pros?

### Takeaway
There is no single clean, licensed, historical dataset. The practical stack is: (1) Epic's own events/leaderboard service (unofficial, token-authenticated, per-session placement/points/elims/time alive) or a paid reseller of it (Cito API); (2) Fortnite Tracker for event histories and Power Ranking (PR) snapshots; (3) Liquipedia (LPDB API; free only for non-commercial, open-source use) and Esports Earnings (keyed API, 1 req/s) for curated tournament placements, earnings, and player metadata; (4) replay files parsed with Shiqan's FortniteReplayDecompressor for fine-grained telemetry (positions, kills, storm), which requires obtaining tournament/server replays. A major 2026 change: Epic launched its own official Power Rankings on June 5, 2026, separate from Fortnite Tracker's long-running PR.

### Cited Findings

**Epic official competitive data (events / leaderboards service)**
- Epic's events service base URL is `https://events-public-service-live.ol.epicgames.com` and requires a Fortnite access token (bearer auth), per the fortnitepy library's HTTP module — [fortnitepy docs](https://fortnitepy.readthedocs.io/en/latest/_modules/fortnitepy/http.html)
- Community-documented endpoints include `/api/v1/players/Fortnite/{accountId}`, `/api/v1/events/Fortnite/download/{accountId}`, `/api/v1/events/Fortnite/{eventId}/history/{accountId}`, and `/api/v1/leaderboards/Fortnite/{eventId}/{eventWindowId}/{accountId}` — [fortnitepy docs](https://fortnitepy.readthedocs.io/en/latest/_modules/fortnitepy/http.html); [FortniteEndpointsDocumentation discussion #320](https://github.com/LeleDerGrasshalmi/FortniteEndpointsDocumentation/discussions/320)
- The community repo LeleDerGrasshalmi/FortniteEndpointsDocumentation has an "Events Service" folder; requests need `Authorization: bearer {accessToken}`; the repo does not discuss Epic ToS — [GitHub](https://github.com/LeleDerGrasshalmi/FortniteEndpointsDocumentation)
- Public leaderboards are browsable on fortnite.com (e.g., FNCS Global Championship LAN leaderboard by region) — [fortnite.com competitive](https://www.fortnite.com/competitive/events/FNCS%20GC%20LAN/leaderboard?region=NAC)

**Epic official Power Rankings (new, 2026)**
- Fortnite Tracker article dated May 29, 2026: Epic's new universal skill rating launches June 5 (2026), uses a player's 20 best Battle Royale and Reload tournament results, updates weekly, uses results from the past two years, incorporates seasonal Ranked tier data, accounts for event difficulty and opponent strength; results lose value after 180 days and are worthless after 720 days; weaker tournaments don't lower ratings — [Fortnite Tracker](https://fortnitetracker.com/article/2426/fortnite-adds-power-rankings-unreal-legends-rank-and-reveals-next-seasons-tournaments)
- Epic describes PR as an Elo-style rating of the top 20 tournament performances, updated weekly (Thursdays); players with fewer than 20 events enter an "Initial Rating Period"; Epic's PR "is not related to, or connected with" the Fortnite Tracker PR system (search snippets) — [Epic Help Center](https://www.epicgames.com/help/c-202300000001636/c-202300000001722/what-are-the-official-fortnite-power-rankings-a202300000087608); [fortnite.com PR info](https://www.fortnite.com/competitive/power-rankings-information)
- Per search snippet of fortnite.com: PR is "a multiplier Elo calculation that weighs you separately against each opponent"; raw performance rating is multiplied by event weight; only the top 20 results count; results decay to zero at 720 days — [fortnite.com PR info](https://www.fortnite.com/competitive/power-rankings-information)
- Fortnite Tracker now hosts an "Epic PR Leaderboard" page mirroring Epic's rankings — [Fortnite Tracker Epic PR leaderboard](https://fortnitetracker.com/epic-pr-leaderboard)

**Fortnite Tracker (Tracker Network) PR and events**
- Fortnite Tracker's own PR leaderboards (global, by platform/region) remain online — [Fortnite Tracker PR leaderboard](https://fortnitetracker.com/events/powerrankings?platform=pc&region=global)
- Player profiles have per-player event history pages (e.g., `/profile/all/{name}/events`) — [Fortnite Tracker example](https://fortnitetracker.com/profile/all/Apis./events?id=799adf61-3954-4b5b-9cbf-96667bd7ebf1)
- The PR API was announced Feb 5, 2020; returns Points (PR points), CashPrize (lifetime), Events (participation count), Rank (in region/platform), Percentile; input is player name + region + platform; rate limit 90 requests/minute — [Fortnite Tracker article](https://fortnitetracker.com/article/944/calling-all-developers-power-rankings-api-is); docs at [tracker.gg developers](https://tracker.gg/developers/docs/titles/fortnitepr) (403 to fetch; current status unverified)
- The broader Tracker REST API lives under `https://api.fortnitetracker.com/v1` with a `TRN-Api-Key` header, covering profile lifetime stats, leaderboards, power rankings, store and challenges (third-party profile) — [api-evangelist/fortnite](https://github.com/api-evangelist/fortnite)
- Note: the PR API returns current snapshot values only (no historical time series per the documented fields), so historical PR trajectories would need periodic scraping/archiving — [Fortnite Tracker article](https://fortnitetracker.com/article/944/calling-all-developers-power-rankings-api-is)

**Cito API (commercial reseller of competitive data)**
- Offers placement and points, eliminations with timelines, team members, time alive, player-by-player kill feeds, storm circles and placement events (for supported replay events), and earnings history; claims 6.1K+ players and 2.6M+ tournament results indexed; earnings charts span 2019–2026 — [Cito API Fortnite](https://citoapi.com/fortnite/)
- Sources: "Epic leaderboard sessions for placement, kills, time alive" plus parsed server replays for FNCS, LAN-style, Milk Cup and other closed-lobby events; smaller events keep leaderboard data only — [Cito API Fortnite](https://citoapi.com/fortnite/)
- Free tier 500 requests/month; paid from $25/month — [Cito API Fortnite](https://citoapi.com/fortnite/); endpoints include player/org tournament history, org rosters, earnings — [achillesscriptsvip/fortnite-esports-api](https://github.com/achillesscriptsvip/fortnite-esports-api) (these GitHub repos appear to be marketing pointers to Cito rather than independent code)

**Liquipedia Fortnite (LPDB)**
- Free LPDB API access is reserved for educational use, non-commercial public websites, and community features, and the project's code must be open-sourced; content is CC-BY-SA 3.0 with attribution required; a custom User-Agent with contact info is required (search snippets) — [Liquipedia API Usage Guidelines](https://liquipedia.net/commons/Liquipedia:API_Usage_Guidelines); [Liquipedia API Terms](https://liquipedia.net/api-terms-of-use)
- MediaWiki API limits: ≤60 requests/hour, ≤1 request per 2 seconds, `action=parse` ≤1 per 30 seconds (search snippet) — [Liquipedia API Usage Guidelines](https://liquipedia.net/commons/Liquipedia:API_Usage_Guidelines)
- Commercial tiers reported at $49/month per data type (~1000 req/h) and $199/month (~5000 req/h) — [apisports.net review (aggregator)](https://apisports.net/providers/liquipedia); overview at [liquipedia.net/api](https://liquipedia.net/api). Pricing is from a third-party aggregator; verify with Liquipedia.
- Unofficial Python wrapper exists (scrapes Liquipedia) — [liquipediapy](https://github.com/c00kie17/liquipediapy)

**Esports Earnings**
- Keyed API (register in Development Area, accept Terms of Use); max 1 request/second; caching encouraged; JSON/XML/CSV output — [Esports Earnings API docs](https://www.esportsearnings.com/apidocs)
- Endpoints: LookupPlayerById, LookupPlayerTournaments (100 results per call, sortable by date), LookupHighestEarningPlayersByGame, LookupRecentTournaments, LookupTournamentById, tournament results (individual vs team) — [Esports Earnings API docs](https://www.esportsearnings.com/apidocs)
- Player fields: first/last name, handle, ISO country code, world/country rank, total USD prize money, tournament count. Birth date is not listed in the API docs — [Esports Earnings API docs](https://www.esportsearnings.com/apidocs)
- Coverage limited to prize-winning results (placement + prize), not points/elims/telemetry — inferred from the documented fields, [Esports Earnings API docs](https://www.esportsearnings.com/apidocs)

**Replay files and parsers (telemetry)**
- Shiqan/FortniteReplayDecompressor: C# (.NET) parser with full Unreal Engine replay support; extracts game data, player data, team data, and map info (llama/supply-drop locations) — [GitHub](https://github.com/Shiqan/FortniteReplayDecompressor); [docs](https://app.readthedocs.org/projects/fortnitereplaydecompressor/)
- Still maintained into 2026: a PR addresses build 41.00 changes (pawn RepMovement rotation widened) — [PR #77](https://github.com/Shiqan/FortniteReplayDecompressor/pull/77); changelog — [CHANGELOG](https://github.com/Shiqan/FortniteReplayDecompressor/blob/master/CHANGELOG.md)
- A fork adds JSON/text export and console tooling — [backdoorkain fork](https://github.com/backdoorkain/Play.Parse.Analyze.Repeat...Fortnite.Replay.Decompressor); related tool — [Shiqan/fortnite-replay-reader](https://github.com/Shiqan/fortnite-replay-reader)

**Osirion (commercial analytics)**
- Provides stats, analytics tools, AI coaching, automated replay review, 2D replay viewer for tournament matches, drop maps; acquired Fortnite-replay.info (tournament data, 2D replay viewer); tracks tournament matches regardless of platform — [Osirion](https://osirion.gg/); [About](https://osirion.gg/about); [FAQ](https://osirion.gg/faq?category=general); [Pricing](https://osirion.gg/pricing)
- No public data API for Osirion was found in this research.

**Kaggle Fortnite datasets**
- "Fortnite Players Stats": 5 modes (Solo, Duo, Trios, Squads, LTM) with score, wins, K/D, win ratio, matches, eliminations, minutes played; collected Chapter 2 Season 6 (April 2021) via the Fortnite Tracker API — casual lifetime stats, not competitive — [Kaggle](https://www.kaggle.com/datasets/iyadali/fortnite-players-stats)
- "Fortnite Player Performance" (Dec 2022) — [Kaggle](https://www.kaggle.com/datasets/thedevastator/unlocking-fortnite-player-performance-with-88-ga)
- No Kaggle dataset dedicated to FNCS/pro competitive results was found.

**Wikipedia summary tables**
- Curated lists usable for sanity checks: highest-earning players; competitive records and statistics; FNCS history (since 2019) — [Highest-earning players](https://en.wikipedia.org/wiki/List_of_highest-earning_Fortnite_players); [Records & statistics](https://en.wikipedia.org/wiki/Competitive_Fortnite_records_and_statistics); [FNCS](https://en.wikipedia.org/wiki/Fortnite_Championship_Series)
- 2026 FNCS: three Majors, a Last Chance Major and a Global Championship, USD $10M total (per a betting-guide site, secondary) — [esportbet.com](https://esportbet.com/fortnite-battle-royale/champion-series/)

### Inferences
- For a decline-forecasting project, the most defensible longitudinal backbone is tournament-level placement/points from Epic's leaderboard service (via direct unofficial calls or Cito), joined to Liquipedia/Esports Earnings for identity resolution (Epic account IDs vs display names change often) and earnings. Replay telemetry (damage, accuracy, build/edit stats) is only feasible for a subset of events where replays can be obtained.
- Granular stats such as damage, accuracy, materials/builds/edits and storm-surge are replay-derived; the Epic leaderboard sessions appear to expose placement, eliminations and time alive only (per Cito's description of its sources).
- Two PR systems now coexist (Fortnite Tracker PR, and Epic's official PR since June 2026), with different formulas; any historical "rating" feature before mid-2026 must come from Tracker's PR or be recomputed.
- Using Epic's internal endpoints with a player access token is not a sanctioned public API; commercial or large-scale scraping carries ToS risk. Liquipedia's free tier forbids closed-source/commercial use.

### Gaps
- Could not verify exact Epic ToS language for automated access to events-public-service; no Epic public developer documentation for competitive data was found.
- Could not confirm whether Fortnite Tracker's PR API is still live in 2026 (tracker.gg docs returned 403), nor whether historical PR snapshots are downloadable.
- fortnite-api.com, Yunite (tournament hosting/Discord bot), and dedicated FNCS stats sites were not verified in this pass; by background knowledge fortnite-api.com serves casual BR stats/cosmetics/shop, not tournament data, and Yunite provides tournament tooling for custom/community events — both unverified here.
- Exact historical depth of Epic's leaderboard API (whether 2018–2019 events are still retrievable) was not confirmed.
- Whether storm-surge or build/edit stats are recoverable from current replay builds was not confirmed beyond the parser's stated fields.

## Q2. Does any source include player birthdates/ages?

### Takeaway
None of the structured competitive data APIs found (Epic, Fortnite Tracker, Esports Earnings, Cito) exposes birthdate. Age must come from Liquipedia player infoboxes (which commonly carry a "Born" field, but could not be fetched to verify here) and Wikipedia biographies for top pros, supplemented by interviews.

### Cited Findings
- Esports Earnings player records include name, handle, country, rank, earnings and tournament count — birth date is not mentioned in the API documentation — [Esports Earnings API docs](https://www.esportsearnings.com/apidocs)
- Fortnite Tracker PR API fields: Points, CashPrize, Events, Rank, Percentile — no age — [Fortnite Tracker article](https://fortnitetracker.com/article/944/calling-all-developers-power-rankings-api-is)
- Wikipedia maintains biographies for top pros (e.g., Bugha, Peterbot, Mongraal, Clix, Pollo, Kami and Setty) which typically list birth dates — [Bugha](https://en.wikipedia.org/wiki/Bugha_(gamer)); [Peterbot](https://en.wikipedia.org/wiki/Peterbot); [Mongraal](https://en.wikipedia.org/wiki/Mongraal); [Clix](https://en.wikipedia.org/wiki/Clix_(gamer)); [Pollo](https://en.wikipedia.org/wiki/Pollo_(gamer)); [Kami and Setty](https://en.wikipedia.org/wiki/Kami_and_Setty)

### Inferences
- Age coverage will be heavily biased toward famous/top earners; many mid-tier pros will have missing or approximate ages (year only), creating selection bias if age is a model feature.
- Liquipedia LPDB "player" records likely include a birthdate field accessible via the API, which would be the most scalable source; this needs verification.
- Many Fortnite pros are minors, so collecting/publishing exact birthdates raises privacy considerations.

### Gaps
- Could not fetch Liquipedia Fortnite player pages (403) to confirm the presence and fill-rate of birthdate fields.
- No dataset of Fortnite pro ages was found.

## Q3. Existing prediction work: Fortnite, battle royale, and esports rating/forecasting/career trajectory

### Takeaway
There is essentially no published academic work on forecasting Fortnite pro placements or careers. Closest analogues: the Kaggle PUBG Finish Placement competition (within-match placement from end-of-match stats, won by gradient boosting plus per-match rank post-processing), Dehpanah et al.'s evaluations of Elo/Glicko/TrueSkill and behavioral ratings for battle royale, Epic's own Elo-style PR, and esports aging/career studies (StarCraft 2 reaction-time decline from age 24; a League of Legends career-trajectory paper).

### Cited Findings

**Fortnite-specific**
- An arXiv search found no paper specifically on Fortnite placement prediction; a 2026 aimbot-detection paper uses Fortnite as a proof of concept — [Detecting Aimbot Cheaters in MOGs](https://arxiv.org/html/2606.07650v1)
- Epic PR is itself a forecasting-adjacent rating: Elo-style, top 20 results, event weights, 720-day decay — [fortnite.com PR info](https://www.fortnite.com/competitive/power-rankings-information); [Fortnite Tracker 2026 article](https://fortnitetracker.com/article/2426/fortnite-adds-power-rankings-unreal-legends-rank-and-reveals-next-seasons-tournaments)
- Third-party blog explainers of 2026 PR (secondary; include Ranked bonuses from BR and Reload) — [alviran.net](https://alviran.net/blog/fortnite-power-rankings-guide-2026/); [technerdiness](https://www.technerdiness.com/fortnite/fortnite-power-rankings-explained/)
- Open-source PR retrieval tool — [JulesLucas/fortnite-api-pr](https://github.com/JulesLucas/fortnite-api-pr)

**PUBG Finish Placement Prediction (Kaggle, 2018)**
- Task: predict `winPlacePerc` (0–1) from end-of-match stats for 65,000+ games of anonymized data from the PUBG developer API; metric MAE — [Kaggle competition](https://www.kaggle.com/c/pubg-finish-placement-prediction/); [data page](https://www.kaggle.com/c/pubg-finish-placement-prediction/data)
- Key trick: only relative ranking within a match matters, so re-ranking predictions within each match and spacing them evenly between 0 and 1 improved scores — [search summary referencing solutions](https://github.com/yansun1996/PUBG-Finish-Placement-Prediction); 1st-place writeup — [Kaggle 1st place "Minions of Mordred"](https://www.kaggle.com/competitions/pubg-finish-placement-prediction/writeups/minions-of-mordred-1st-place-solution) (body not retrievable)
- LightGBM/gradient boosting dominated; one student model reached MAE 0.0245; walk distance and killPlace were top features — [UT Austin EE460J project](https://cliveunger.github.io/EE460J_Final_Project_PUBG/)
- Other solution repos — [jerryji1993](https://github.com/jerryji1993/PUBG_winner_prediction); [deepikakanade](https://github.com/deepikakanade/Kaggle-Project-PUBG-Finish-Placement-Prediction)

**Battle royale rating systems (academic)**
- Dehpanah, Ghori, Gemmell, Mobasher (2021, ICAI'21): evaluated rating systems on 25,000+ team battle royale matches; NDCG was the most reliable evaluation metric; new-player inclusion strongly affects metric reliability — [arXiv 2105.14069](https://arxiv.org/abs/2105.14069)
- They extended Elo to team battle royale by summing pairwise win probabilities vs every other team (search snippet) — [arXiv 2105.14069 PDF](https://arxiv.org/pdf/2105.14069)
- Evaluation of Elo, Glicko, TrueSkill for free-for-all (PUBG) games — [arXiv 2008.06787](https://arxiv.org/pdf/2008.06787)
- Behavioral player modeling from in-game stats over 75,000+ battle royale matches, compared against Elo/Glicko/TrueSkill — [arXiv 2112.04379](https://arxiv.org/pdf/2112.04379); [Behavioral Player Rating, arXiv 2207.00528](https://arxiv.org/pdf/2207.00528)
- General performance-rating theory (chess, tennis) — [arXiv 2312.12700](https://arxiv.org/pdf/2312.12700)

**Esports aging and career trajectories**
- Thompson, Blair, Henrey (PLOS ONE, 2014): 3,305 StarCraft 2 players aged 16–44; age-related slowing of in-game self-initiated response times begins at ~24; expertise did not attenuate the decline — [PLOS ONE](https://journals.plos.org/plosone/article?id=10.1371%2Fjournal.pone.0094215); [PMC](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC3981764/)
- "From rising stars to early retirees: the accelerated career trajectories of League of Legends esports players" (ScienceDirect, 2025; details not retrievable) — [ScienceDirect](https://www.sciencedirect.com/org/science/article/pii/S1352759225000120)
- Other related: structure of performance and training in esports — [PLOS ONE 2020](https://journals.plos.org/plosone/article?id=10.1371%2Fjournal.pone.0237584); within-expertise transfer during domain change — [PLOS ONE](https://journals.plos.org/plosone/article?id=10.1371%2Fjournal.pone.0295037); career transition — [Life After Esports](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC7214923/)
- Explainable esports win prediction in streaming (Entertainment Computing 2025) — [arXiv 2510.19671](https://arxiv.org/abs/2510.19671)

### Inferences
- The PUBG Kaggle approach is within-match placement from post-hoc stats, not forward forecasting; for pro-career forecasting, the more transferable ideas are within-lobby rank normalization and pairwise-Elo extensions to multi-team lobbies.
- Epic's PR design (top-N best results, decay) intentionally hides declines (bad events don't lower rating), so PR alone is a lagging, upward-biased indicator of decline; raw per-event placement percentiles are needed.
- The StarCraft "24" result is a natural prior for age effects but is about RTS response times; Fortnite-specific evidence is absent.

### Gaps
- No Fortnite-specific academic paper, thesis, or conference paper (IEEE CoG, FDG) on placement or career forecasting was found; searches were limited and Google Scholar was not directly queried.
- HLTV Rating methodology and Apex Legends-specific prediction work were not researched in this pass.
- Could not retrieve the LoL career-trajectory paper's findings (peak age, career length).

## Q4. Community/commercial prediction projects, betting markets, fantasy Fortnite

### Takeaway
Fortnite prediction markets exist but are thin: Kalshi lists an FNCS Global Championship 2026 winner market, a few sportsbooks offer outrights around major events, and a community "Fantasy Fortnite" app lets users pick top finishers. No public statistical FNCS/LAN forecasting model was found.

### Cited Findings
- Kalshi has a market on the FNCS Global Championship 2026 champion — [Kalshi](https://kalshi.com/markets/kxfortnite/fortnite-tournament/kxfortnite-fncsgc26)
- Only a handful of books price Fortnite, opening markets around big events; points-based lobbies mean few head-to-head lines, so outrights dominate (e.g., Clix to win the 2026 Global Championship) — [esportbonus.com](https://esportbonus.com/fortnite-betting/); [esportsbetadvisor](https://esportsbetadvisor.com/fortnite/); [sbo.net](https://www.sbo.net/esports/fortnite/)
- Odds comparison listing for Fortnite — [Strafe](https://www.strafe.com/esports-betting/odds/fortnite/)
- Fantasy Fortnite: users predict top finishers of competitive tournaments and compete on a global leaderboard — [fantasyfortnite.app](https://fantasyfortnite.app/)
- Osirion markets "tournament insights" and AI coaching (not explicit forecasting) — [Osirion](https://osirion.gg/)

### Inferences
- Kalshi/sportsbook outright prices could serve as a market-implied benchmark to evaluate a forecasting model for majors.

### Gaps
- No public open-source FNCS result-prediction model or historical odds dataset was found.

## Q5. Studies of online vs LAN performance differences

### Takeaway
No peer-reviewed study quantifying online vs LAN performance differences in Fortnite (or rigorously in other esports) was found; available material is journalistic/betting commentary describing latency, stage pressure, and team-specific effects.

### Cited Findings
- LAN removes ping issues but adds stage lights, cameras, and crowd pressure; players respond differently — [siege.gg](https://siege.gg/news/lan-vs-online-why-some-teams-thrive-or-collapse-on-stage)
- Some teams excelled online during the pandemic but struggled when LAN returned, suggesting team/player-specific effects — [siege.gg](https://siege.gg/news/lan-vs-online-why-some-teams-thrive-or-collapse-on-stage); [EspoWorld (Medium)](https://espoworld.medium.com/format-wars-online-vs-lan-51ef80b53508)
- Betting-oriented commentary treats LAN vs online as a material factor — [Esportz Network](https://www.esportznetwork.com/how-does-lan-vs-online-affect-esports-betting/)
- Physiological/cognitive responses to competitive esports sessions (not LAN-specific) — [PMC7272664](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC7272664/)

### Inferences
- Fortnite is well suited to studying this because most events are online while FNCS Global Championships/LANs are in-person with the same players; a within-player LAN indicator is feasible to construct from event metadata (Liquipedia/Epic event names such as "FNCS GC LAN").

### Gaps
- No quantitative LAN-vs-online study found for any esport; Google Scholar not queried directly.
