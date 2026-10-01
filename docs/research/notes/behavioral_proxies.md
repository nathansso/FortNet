# Behavioral and Telemetry Proxies for Cognitive-Motor Capacity in Fast-Paced Games (Focus: Pro Fortnite)

Research date: 2026-09-27. About 25 search and fetch calls. Several primary sources (ScienceDirect, PubMed, Medium/STRATZ) returned 403 or CAPTCHA pages. Claims from those sources rest on search-result snippets and are flagged below.

## 1. Which studies validate in-game telemetry as a measure of cognition or cognitive aging?

### Takeaway
The strongest direct evidence comes from StarCraft II. Thompson, Blair and Henrey (PLOS ONE 2014, N=3,305, ages 16–44) found that "looking-doing latency" (the time from a screen fixation to the first action) starts slowing at about age 24, by roughly 10 ms per year, and that expertise does not buffer this slowing. Large-N studies from other games point the same way: Aim Lab (N=7,174 longitudinal), Sea Hero Quest (N from 0.5M to 3.9M; 5,896 in a 2025 motor-vs-cognitive decomposition), a pooled reaching-dataset study (N=2,390), and MOBA MMR-by-age profiles. Together they support in-game latency, precision and variability as valid indicators that are sensitive to age. Almost all of these studies are cross-sectional.

### Cited Findings
**StarCraft II (Thompson/Blair lab, Simon Fraser University)**
- Thompson, Blair and Henrey, "Over the Hill at 24", PLOS ONE 2014. The sample was 3,305 SC2 players aged 16–44 (mean 21.7, SD 4.2), 98.5% male. The main measure was looking-doing latency (LDL), defined as "the latency to an action after a new fixation of the view-screen". Players complete about 300 looking-doing cycles per game, and the analysis used each player's mean latency — [PMC full text](https://pmc.ncbi.nlm.nih.gov/articles/PMC3981764/)
- Piecewise regression put the breakpoint at age 24 (95% CI 20–29) and fit better than a linear model (χ²=12.7, p<0.05; adjusted R²=0.47 for the best model). A 39-year-old showed about 150 ms more LDL than a 24-year-old, roughly 10 ms per year, which is about 15% of the gap between professional and Bronze league — [PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC3981764/)
- The league (skill) × age interaction was not significant: "this decline is not ameliorated by level of expertise" — [PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC3981764/); [PLOS ONE](https://journals.plos.org/plosone/article?id=10.1371%2Fjournal.pone.0094215)
- Compensation. Older players used more unique hotkeys per timestamp and more offscreen attacks (both p*<0.001), which suggests they swap in interface strategies that lower cognitive load. They also assigned fewer hotkeys, selected hotkeys less often, and used fewer complex units and abilities. Worker production, a dual-task proxy, showed no age effect (p=0.97) — [PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC3981764/)
- The authors list their own limitations: cross-sectional design, possible cohort effects, maximum age of 44, and an almost entirely male sample — [PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC3981764/)
- Thompson et al. 2017 (Topics in Cognitive Science) analysed 3,317 SC2 players across seven skill levels and 996,163 perception-action cycles (PACs). They tested motor-chunking predictions by asking whether first-action latency within a PAC exceeds the latency between actions inside it — [Wiley](https://onlinelibrary.wiley.com/doi/10.1111/tops.12254)
- A follow-up PLOS ONE paper argues that "classic motor chunking theory fails to account for behavioural diversity and speed" in SC2. Its point is that expert action sequences are more varied than simple chunk models predict — [PLOS ONE](https://journals.plos.org/plosone/article?id=10.1371%2Fjournal.pone.0218251)

**Aim trainers (Aim Lab / Statespace; KovaaK's)**
- Listman, Tsay et al., "Long-Term Motor Learning in the 'Wild' With High Volume Video Game Data", Frontiers in Human Neuroscience, Dec 2021. The analysis covered 7,174 Aim Lab players and more than 62,170 game-days, drawn from a platform of over 20 million players, all playing on their own hardware at home. Shooting accuracy saturated within a few days. Motor acuity, measured as a shift in the speed-accuracy tradeoff, kept improving, with diminishing returns after about 30–60 minutes of practice per day — [PubMed](https://pubmed.ncbi.nlm.nih.gov/34987368/); [PMC](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC8720934/)
- Donovan et al. (Statespace), "Assessment of human expertise and movement kinematics in FPS games", Frontiers in Human Neuroscience 2022. N=32 professional and semi-pro male players (Valorant, PUBG, R6 Siege), mean age 22.47 ± 3.62. The tasks were Gridshot and Sixshot, with orientation logged at 120 Hz. The derived kinematic measures, called SPAR, were:
  - reaction time: target onset to movement initiation
  - peak speed
  - precision: distance to the target
  - accuracy
  - "swipiness": when the shot fires relative to the movement midpoint

  Players with higher motor acuity had faster reaction times, greater precision and earlier shot timing. The study did no age analysis and had no amateur group — [Frontiers](https://www.frontiersin.org/journals/human-neuroscience/articles/10.3389/fnhum.2022.979293/full); [PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC9744923/)
- A KovaaK's pilot study proposes the aim trainer as a reliable metrics platform for assessing shooting proficiency in esports players. I saw only the title and abstract listing, not the ICC values — [ResearchGate](https://www.researchgate.net/publication/378899828_KovaaK's_aim_trainer_as_a_reliable_metrics_platform_for_assessing_shooting_proficiency_in_esports_players_a_pilot_study)

**Large reaching datasets (a lab analogue of aim)**
- A 2025 Communications Psychology paper harmonized 2,390 participants from four reaching studies. Older age was associated with slower reaction time (1.3 ms per year), slower movement time (4.3 ms per year) and worse precision (0.04° per year). Once video-game use, computer use and sleep were modelled, sex/gender gaps largely disappeared, but age stayed a consistent predictor — [Nature Comms Psych](https://www.nature.com/articles/s44271-025-00383-7); [bioRxiv](https://www.biorxiv.org/content/10.1101/2025.05.01.651757.full.pdf)

**Sea Hero Quest (navigation)**
- Current Biology (Coutrot et al. 2018), as reported in press materials: data from more than half a million players in 57 countries showed navigation ability declining steadily across adulthood, near-linearly from the early 20s. The dataset later grew to 3.9M people in 63 countries — [Northumbria press](https://www.northumbria.ac.uk/about-us/news-events/news/2018/08/navigation-skills---sea-hero-quest/); [Spiers et al. 2023, TopiCS](https://onlinelibrary.wiley.com/doi/abs/10.1111/tops.12590)
- Lancia, ..., Spiers and Pezzulo, iScience, Aug 2025. N=5,896 aged 19–70. They separated **motor** proxies (angular velocity, speed) from a **cognitive** proxy, "relative goal-directedness", which comes from fitting observed trajectories to MDP policy models: goal-directed versus visibility-based. Both declined with age:
  - speed: r=−0.47
  - angular inefficiency: |r|=0.27
  - goal-directedness: r=−0.14

  A joint model beat either proxy alone, so the two declines are separable. Decline was continuous and linear, with no threshold — [PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC12481093/)

**MOBAs (League of Legends / Dota 2)**
- Kokkinakis et al., PLOS ONE 2017. Performance in League of Legends correlates with fluid intelligence. MMR age profiles in LoL and Dota 2 look like the age profile of fluid intelligence, peaking in the early-to-mid 20s — [PLOS ONE](https://journals.plos.org/plosone/article?id=10.1371%2Fjournal.pone.0186621); [PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC5687598/)
- "From rising stars to early retirees" (2025) covers 4,159 professional LoL players across 1,605 competitions (2010–2024) and reports peak performance around age 21 followed by decline. This comes from a search snippet only (403 on fetch); the metric definitions are unverified — [ScienceDirect](https://www.sciencedirect.com/org/science/article/pii/S1352759225000120)
- A STRATZ (Dota 2 analytics) blog post claims Dota 2 performance declines through the 20s and gives an average pro age of 22.9. This is industry analysis, not peer-reviewed, and the page could not be fetched — [Medium/STRATZ](https://medium.com/stratz/the-effects-of-age-on-dota-2-performance-cdcf7fee664f)

**Typing**
- Dhakal, Feit, Kristensson and Oulasvirta, CHI 2018. 168,000 volunteers produced 136 million keystrokes. Inter-key intervals, rollover typing and clustering yielded 8 typist types. The dataset includes demographics, but I did not verify its age-effect results — [Aalto](https://userinterfaces.aalto.fi/136Mkeystrokes/); [ACM](https://dl.acm.org/doi/pdf/10.1145/3173574.3174220)

### Inferences
- LDL and PAC measures are the best template for Fortnite. They are self-paced, occur many times per match (about 300 per game in SC2), are computed from timestamped logs, and have published age curves.
- The expected size of age-related slowing in young adulthood is small at the level of a single trial. SC2 showed about 10 ms per year after 24; lab reaching showed about 1.3 ms per year of RT across the lifespan. Detecting within-player change over 2–5 years will therefore need many events per player and aggregation across matches.
- Compensation shows up in behavior: older players shift to interface strategies that lower cognitive load. For Fortnite this means changes in playstyle or loadout could mask declining raw speed, and should be modelled as a separate signal rather than treated as noise.

### Gaps
- I found no published peer-reviewed analysis of Aim Lab or KovaaK's performance by age across its full user base. Statespace published learning and kinematics papers but no age-curve paper that I could locate.
- I found no large-scale osu! or Tetris age-performance studies in this search.
- Almost everything is cross-sectional. I found no longitudinal within-player telemetry study of age-related decline in esports pros.

## 2. Fortnite-specific mechanical metrics: what exists and what can be extracted (replays, Fortnite Tracker, creative maps)

### Takeaway
Fortnite `.replay` files, parsed with the actively maintained FortniteReplayDecompressor (v3.1.0, 2026-09-13) or xNocken's replay-reader, contain timestamped player locations with yaw, shots (weapon, damage, crit, fatal, target), damage taken (with attacker and shield), health changes, weapon switches and inventory, and the kill feed (knocks and eliminations, with positions, weapon and distance). That is enough to build reaction-latency, accuracy and fight-outcome features. Building and edit events are not documented in either parser, so extracting them is a gap. Fortnite Tracker and the Power Rankings API mostly give tournament placements and points, which are outcome measures and not mechanical ones.

### Cited Findings
- FortniteReplayDecompressor's player-data guide documents these fields:
  - `Locations`: X, Y, Z, yaw, vehicle and state flags, timestamped with `DeltaGameTimeSeconds` and `WorldTime`. Sampling frequency is configurable via `LocationChangeDeltaMS`. `PrivateTeamLocations`, `LandingLocation` and `LastKnownLocation` are also available.
  - `Shots`: "weapon, damage, critical hits, fatal shots, and hit player identification", which requires `IgnoreShots=false`.
  - `DamageTaken`: amount, shield impact, attacker and timestamp.
  - Health and shield changes.
  - Inventory and weapon switches with timestamps, which require `ParseType.Full`.
  - Status changes (knocked, killed, revived).

  The documentation does not mention building or edits, and some data is limited to the replay owner's perspective — [Mintlify guide](https://mintlify.wiki/SL-x-TnT/FortniteReplayDecompressor/guides/extracting-player-data)
- Elimination events record eliminator and eliminated IDs, the 3D position and rotation of each player, player type (human or bot), DeathCause (weapon), the distance between players, and whether the event was a knock (DBNO) — [Mintlify PlayerElimination](https://sl-x-tnt-fortnitereplaydecompressor.mintlify.app/api/models/player-elimination)
- Replays hold a baseline world state, periodic checkpoints and incremental network changes (actor replication and RPCs). Decompressing them needs Oodle, via Fortnite's own `oodle` DLL. Event types include player statistics, match statistics and kill-feed events — [ReadTheDocs overview](https://fortnitereplaydecompressor.readthedocs.io/en/latest/overview/)
- Maintenance: the CHANGELOG lists v3.0.0 (2026-04-04, .NET 10) through v3.1.0 (2026-09-13, 10–25% faster parsing). It mentions support for Fortnite v25, v26 and v32 and killfeed events (knocks, eliminations, revives) — [CHANGELOG](https://github.com/Shiqan/FortniteReplayDecompressor/blob/master/CHANGELOG.md). An open issue from 2026 reports a hang in full net-data parsing on some replays, while EventsOnly mode works — [Issue #74](https://github.com/Shiqan/FortniteReplayDecompressor/issues/74)
- xNocken/replay-reader (Node.js) claims it can parse "99% (or more) of fortnite replays". It supports `parseLevel` settings and user-defined custom net-field exports, which could in principle expose more replicated properties — [GitHub](https://github.com/xNocken/replay-reader)
- Other parsers: lanslide-team/FortniteReplayParser, a .NET tool that writes match and player stats to a database, and tpatel/fortnite-replay-reader — [lanslide](https://github.com/lanslide-team/FortniteReplayParser); [tpatel](https://github.com/tpatel/fortnite-replay-reader)
- Fortnite Tracker's Power Rankings API takes player, region and platform and returns rankings built from placements in official Epic tournaments. The rate limit is 90 requests per minute — [Tracker.gg docs](https://tracker.gg/developers/docs/titles/fortnitepr); [Fortnite Tracker article](https://fortnitetracker.com/article/944/calling-all-developers-power-rankings-api-is). Epic also publishes an official Power Rankings page — [fortnite.com](https://www.fortnite.com/competitive/power-rankings)
- Creative edit courses exist, for example Raider464's courses with solo highscores and 1v1 edit races, and Fortnite Tracker lists creative maps. I found no public, scrapable per-player timing leaderboard — [FortniteCreativeHQ](https://www.fortnitecreativehq.com/raiders-1v1-edit-race-course-3/); [Fortnite Tracker creative](https://fortnitetracker.com/creative/0744-7641-9247)
- The only peer-reviewed study I found with Fortnite pros is a caffeine trial: 15 pros (7 Fortnite, 8 CS:GO). A 3 mg/kg dose improved hit time, hit accuracy and simple RT on a shooting task. This shows pros can be tested with standardized aim tasks — [Frontiers 2024](https://www.frontiersin.org/journals/sports-and-active-living/articles/10.3389/fspor.2024.1437700/full)

### Inferences
The features below are proposed derivations from the documented fields. None has been validated.
- **Hit-to-return-fire latency** is the closest Fortnite analogue to LDL. It runs from a `DamageTaken` timestamp on player P to P's next `Shot` event. Its median and its intra-individual SD can be computed per match.
- **Weapon-switch-to-first-shot latency** runs from a weapon-switch event to the next shot. It proxies motor-sequencing and "piece control" speed for combat actions.
- **Accuracy features** are hits/shots, crit (headshot) share, and damage per shot by weapon class. **Inter-shot interval CV** within a fight is another candidate.
- **Engagement segmentation** would cluster Shot and DamageTaken events between two players into "fights". From each fight: time-to-first-shot after first contact, fight duration, damage traded, knock-to-elimination conversion time, and fight win rate from the kill feed.
- **Time-to-first-shot after an enemy appears** needs line-of-sight reconstruction from both players' positions and view. Only yaw is documented, and pitch plus terrain and builds would be needed, so this is harder and noisier than the damage-anchored latencies.
- **Rotation and decision features** come from location trajectories: path efficiency, timing of zone entry, and a Sea-Hero-Quest-style goal-directedness model. Zone data is not confirmed in the docs I read.
- **Build and edit speed** is the signature Fortnite mechanic, but it would need custom net-field exports for building actors. Replication of edits and placements is probably present in the network stream but is undocumented.
- Pros record client replays of their own matches. Tournament replays that include every player's perspective are not public, as far as I found. Obtaining data at scale would probably mean collecting replays from pros or orgs, or using Epic's own server-side data.

### Gaps
- There is no documentation confirming that building placement or edit events, pitch/aim vectors, or storm/zone state can be extracted with the current parsers.
- I found no public dataset of per-player edit-course or aim-map completion times, and no API for creative-map leaderboards.
- I did not check whether Fortnite Tracker exposes accuracy or damage-per-match for competitive play through an API. The PR API is placement-only.
- I found no peer-reviewed study using Fortnite replay telemetry to measure cognition.

## 3. Aim Lab / Statespace / esports-science evidence on age effects, and pros vs amateurs by age

### Takeaway
Esports players have reliably faster RT than non-gamers, and aim-trainer kinematics separate expertise levels. I found no published large-N analysis of aim performance by age from Aim Lab, KovaaK's or Statespace. The best age-curve evidence comes from SC2 (LDL), lab reaching and MOBA MMR profiles.

### Cited Findings
- Esports competitors had visuomotor RT of 175 ± 26 ms, against 224 ± 31 ms for non-gaming sedentary controls — [ResearchGate](https://www.researchgate.net/publication/350852240_Reaction_Times_for_Esport_Competitors_and_Traditional_Physical_Athletes_are_Faster_than_Noncompetitive_Peers)
- In a comparison of FPS and MOBA players, FPS players showed better sustained attention, RT and inhibition — [ScienceDirect 2024](https://www.sciencedirect.com/science/article/abs/pii/S1875952124000089)
- The Statespace pro sample (mean age 22.5, SD 3.6) had too little age range for an age analysis. What separated experts was faster RT, greater precision and earlier shot timing — [Frontiers 2022](https://www.frontiersin.org/journals/human-neuroscience/articles/10.3389/fnhum.2022.979293/full)
- The SC2 age decline did not differ across skill leagues, pros included — [PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC3981764/)
- Lab reaching (N=2,390) showed RT slowing by 1.3 ms per year, with age still a predictor after controlling for video-game experience — [Nature Comms Psych 2025](https://www.nature.com/articles/s44271-025-00383-7)

### Inferences
- Pros probably sit at a higher intercept but on a similar slope, because the SC2 study found no expertise × age interaction. Expertise shifts the curve rather than preventing decline.
- The 30–60 minute diminishing-returns finding in Aim Lab suggests practice volume should be a covariate. Training intensity can offset or mask small age-related declines.

### Gaps
- I found no Aim Lab or Statespace publication, and no "esports aging" talk with citable data, that reports RT or accuracy by age.
- I found no data on pro vs amateur RT stratified by age.

## 4. Intra-individual variability (IIV) in RT as an early marker of decline

### Takeaway
Trial-to-trial RT inconsistency rises with age. In ageing and in some neurological conditions it appears to come before mean slowing, and it predicts later cognitive outcomes better than mean RT does. In-game latency SD, CV or ex-Gaussian tau should be a core feature.

### Cited Findings
- Greater inconsistency predicted membership in a maladaptive cognitive-outcome group 5 years later. Relative risk was higher for being more inconsistent than for being slower, and moderately demanding tasks gave the most sensitive IIV — [PubMed 20853957](https://pubmed.ncbi.nlm.nih.gov/20853957/); [ResearchGate](https://www.researchgate.net/publication/46379476_Intraindividual_Variability_in_Reaction_Time_Predicts_Cognitive_Outcomes_5_Years_Later)
- A systematic review in JINS (Haynes et al. 2017) screened 688 studies and included 22. Nine had longitudinal IIV and seventeen predicted outcomes from baseline IIV, covering age-related decline, dementia and mortality. It describes IIV as rising with normal and pathological ageing and as a possible marker of neurobiological integrity. Details come from the abstract and search snippet only — [Cambridge Core](https://www.cambridge.org/core/journals/journal-of-the-international-neuropsychological-society/article/systematic-review-of-longitudinal-associations-between-reaction-time-intraindividual-variability-and-agerelated-cognitive-decline-or-impairment-dementia-and-mortality/0D276A8E4CF3A5C07D62001204168559)
- In MS, a two-year study found that higher IIV was the earliest indicator of cognitive change, appearing before slowing — [PMC11299566](https://pmc.ncbi.nlm.nih.gov/articles/PMC11299566/)
- IIV is associated with white-matter integrity in healthy ageing and early Alzheimer's disease — [ScienceDirect](https://www.sciencedirect.com/science/article/abs/pii/S0028393211005355)
- The Sydney Memory and Ageing Study tested whether RT IIV independently predicts mortality in old age — [PMC5549897](https://pmc.ncbi.nlm.nih.gov/articles/PMC5549897/)

### Inferences
- IIV features for Fortnite would be computed for each player and each match, or each rolling window:
  - SD, CV or ex-Gaussian tau of hit-to-return-fire latency
  - SD, CV or ex-Gaussian tau of switch-to-shot latency
  - SD, CV or ex-Gaussian tau of inter-shot intervals
  - variability of accuracy across fights
- Game context (weapon, distance, fight type) inflates variance, so these should be residualized on it first.
- For a forecasting model, IIV is a plausible leading indicator and mean latency a lagging one.

### Gaps
- The IIV literature is mostly about middle-aged and older adults. I found no evidence on whether IIV rises detectably between ages 18 and 30, the age range of Fortnite pros.
- I found no esports study using in-game IIV.

## 5. Distinguishing mechanical decline from strategic/decision factors; fatigue, tilt and burnout vs ageing

### Takeaway
The SHQ decomposition is the best worked example for separating motor from decision components in game telemetry. It models motor efficiency (speed, angular velocity) separately from a model-fitted strategy parameter (goal-directedness). Acute fatigue in esports produces measurable within-session executive decline with pupil constriction, independent of how fatigued players feel. Ageing should therefore be modelled as a slow trend across seasons, and fatigue, tilt and burnout as within-session or within-period deviations.

### Cited Findings
- SHQ (iScience 2025): motor proxies and a cognitive, model-derived goal-directedness proxy both declined with age, and each contributed independently (bootstrap, joint model better). The methods were MDP policy fitting by log-likelihood and mixed-effects models — [PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC12481093/)
- In SC2, raw speed (LDL) declined while strategy changed: more hotkey use and offscreen attacks, fewer complex units — [PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC3981764/)
- Matsui et al., Computers in Human Behavior, July 2024: prolonged esports play caused cognitive (executive-function) decline with pupil constriction, independent of subjective fatigue, at every expertise level. Details come from snippets; the full text returned 403 — [ScienceDirect](https://www.sciencedirect.com/science/article/pii/S0747563224000876); [ResearchGate](https://www.researchgate.net/publication/379314906_Cognitive_decline_with_Pupil_Constriction_Independent_of_subjective_fatigue_during_prolonged_esports_across_player_expertise_levels)
- A search summary reports that about 1 hour of play improves reaction speed and mood, while more than 2 hours reduces reaction speed and accuracy, and that executive function declines over 2 to 2.5 hours in skilled players. This is secondary summarization and was not verified in full text — [ScienceDirect](https://www.sciencedirect.com/science/article/pii/S0747563224000876)
- A registered trial (NCT06729060) is testing the effect of mental fatigue on esports RT and game performance using Aim Lab — [ClinicalTrials.gov](https://clinicaltrials.gov/study/NCT06729060)

### Inferences
Proposed separation strategy:
- **Mechanical decline** shows as a slow trend in latency and IIV that survives adjustment for time-in-session, time-of-day, match importance and recent results.
- **Fatigue** shows as within-session slopes: latency and IIV rising with the match index in a session.
- **Tilt** shows as a short-term shift after losses or deaths, for example more aggressive engagement, lower accuracy or shorter fight entry times after an elimination. It reverts.
- **Burnout or motivation** shows as reduced volume (fewer matches or tournaments) and flat effort markers, with mechanical metrics intact when the player does play.
- **Decision factors** show in rotation/path metrics, engagement selection (which fights are taken, win rate given taking a fight), and placement not explained by fight mechanics.

### Gaps
- I found no study that separates ageing from burnout in esports behavioral data.
- The "tilt" markers are my own inferences, with no validation literature found.

## 6. Wearable, biometric and lab-test approaches used by esports organizations (brief)

### Takeaway
The esports literature is dominated by HR/HRV, followed by eye tracking, EDA and EEG. Most studies are small, and linking the signals to performance is weak without fine-grained in-game context.

### Cited Findings
- Scoping review of 30 studies: cardiovascular/HRV was used in 20, oculometry in 10, EDA in 9 and EEG in 5 — [PubMed scoping review](https://pubmed.ncbi.nlm.nih.gov/42506364/) (from a snippet)
- A systematic review of HRV in esports and an HRV monitoring study found high within-player HRV variability during sessions. Linking HRV to performance "without high resolution contextual information" was not possible. In one study SDRR was lower in winning than in losing teams — [ScienceDirect](https://www.sciencedirect.com/science/article/pii/S146902922300119X); [IJEsports](https://www.ijesports.org/article/60/html)
- EEG recorded before a match predicted esports match outcomes, with LightGBM reaching up to 80% accuracy (Computers in Human Behavior 2024) — [ACM DL](https://dl.acm.org/doi/10.1016/j.chb.2024.108351)
- A study of professional LoL players tracked HR, HRV, respiratory rate and perceived stress in training and competition (N=7) — [JEGE 2024](https://doi.org/10.1123/jege.2024-0033)
- A 2026 systematic review covers sensor-driven ML for cognitive state and performance-risk assessment in esports — [Electronics](https://doi.org/10.3390/electronics15071465)

### Inferences
- Biometrics are useful for labelling state (fatigue, stress) so it can be separated from trait decline. For a forecasting project using only public data they are impractical. Standardized aim-trainer tasks (Aim Lab/KovaaK's SPAR-style metrics at 120 Hz) are the most feasible "lab anchor" for validating replay-derived features in consenting pros.

### Gaps
- I found no public disclosure of which Fortnite orgs use which biometric protocols, and no age-related findings from org data.
