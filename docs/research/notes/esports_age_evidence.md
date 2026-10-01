# Empirical Evidence on Age and Performance in Esports, with a Focus on Fortnite Competitive Players

(Research notes compiled 2026-09-27. Evidence tiers used below: **[Peer-reviewed]**, **[Rigorous non-academic analysis]**, **[Industry/marketing study]**, **[Journalism/biographical]**, **[Anecdotal]**.)

## 1. Which rigorous studies estimate peak age or age-related decline in esports?

### Takeaway
Only a handful of rigorous studies exist, and none estimates a within-player age curve for Fortnite specifically. The strongest evidence says cognitive-motor speed starts to decline in the mid-20s (StarCraft II, onset at 24, 95% CI 20–29, cross-sectional). Studies built on earnings and pro performance put peaks around 21 in PC titles and around 19 in battle royale games. These are mostly cross-sectional designs or designs based on prize money, so they mix biological aging with cohort, selection and exit effects.

### Cited Findings

**StarCraft II: Thompson, Blair & Henrey (2014), PLOS ONE, "Over the Hill at 24" [Peer-reviewed]**
- N = 3,305 SC2 players aged 16–44 (mean 21.7, SD 4.2); 99.1% male; data came from replay files parsed with SC2Gears, plus self-reported league (Bronze through Grandmaster), hours and play frequency — [PLOS ONE](https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0094215)
- Method: a cross-sectional piecewise linear regression on "looking-doing latency" (the time from a screen movement to the next action). The breakpoint where slowing begins is age 24 (95% CI 20–29) — [PLOS ONE](https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0094215)
- Magnitude: a 39-year-old Bronze player is about 150 ms slower per latency event than a 24-year-old, which adds up to roughly 30 seconds over a 15-minute game. Each 15 years after 24 costs about 15% of the speed advantage that pros hold over Bronze players — [PLOS ONE](https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0094215)
- Expertise did not slow the decline. Older players appeared to compensate by using more unique hotkeys, attacking offscreen via the minimap and avoiding complex units, and they played fewer hours per week — [PLOS ONE](https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0094215)
- The authors acknowledge that the cross-sectional design cannot separate age effects from cohort effects, such as how early a birth cohort was exposed to RTS games — [PLOS ONE](https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0094215)

**League of Legends: "From rising stars to early retirees" (2025), Team Performance Management (Emerald) [Peer-reviewed]**
- 4,159 global LoL pros, analysed with Generalized Additive Models and Gaussian peak analysis plus interviews with 5 former pros and coaches. Performance rises quickly to a peak near age 21 and then declines "swiftly". The paper proposes a five-stage career model (Entry, Growth, Maturity, Decline, Transition). The qualitative data point to burnout, role inflexibility and limited mental-health support as drivers of decline — [Emerald DOI](https://doi.org/10.1108/TPM-09-2024-0108); [ScienceDirect listing](https://www.sciencedirect.com/org/science/article/pii/S1352759225000120) (full text returned 403; details are from the abstract and search snippets. I could not retrieve the exact decline rate.)

**Cross-title, based on earnings: Jimoon Kang (2026), "The Golden Age of Esports Players", Simulation & Gaming 57(1): 93–114 [Peer-reviewed]**
- 259,522 tournament records covering 50,441 players in 201 games, taken from Esports Earnings for 1997–2023. GAMs of age against prize money — [RePEc abstract](https://ideas.repec.org/a/sae/simgam/v57y2026i1p93-114.html); [SAGE](https://journals.sagepub.com/doi/10.1177/10468781251371070)
- Overall peak prize earnings come at 21.2 years. **Battle Royale and Sports games peak earlier, at about 19.** FPS, MOBA and fighting games peak at about 21. PC games peak at 21, console at 20 and mobile at 19 — [RePEc](https://ideas.repec.org/a/sae/simgam/v57y2026i1p93-114.html)
- Across four time periods, "the competitive window expanded considerably", which the author attributes to professionalization and larger prize pools letting older players sustain their careers — [RePEc](https://ideas.repec.org/a/sae/simgam/v57y2026i1p93-114.html)
- Caveat: the outcome is prize money, not skill, so it is confounded by when a title's prize pools existed and by which ages were present in that era.

**Counter-Strike: HLTV analysis by NER0cs (16 April 2022) [Rigorous non-academic analysis]**
- 79 players who have appeared in HLTV's Top 20 since 2015. The metric is kills per round against Top-20 teams, counting only player-seasons with at least 25 such maps. Performance follows a bell curve. Age 20 has the highest average KPR (0.74), and ages 20–24 are the peak window. KPR declines steadily after 25, reaching 0.65 by age 29, and the decline is gradual rather than steep. Exceptions include f0rest (0.70+ KPR into his 30s) and s1mple — [HLTV](https://www.hltv.org/news/33610/when-do-counter-strike-players-peak)
- Caveat: the sample is conditioned on reaching the Top 20, so it carries survivorship bias.

**Relative age effects: Laxdal & Erikstad (2025), Frontiers in Sports and Active Living [Peer-reviewed]**
- 15,734 professional players across 10 PC titles, including Fortnite, Apex, Valorant, Overwatch, CS, LoL, Dota 2, SC2, CoD and FIFA. Mean age 26.40 (SD 5.24). They found no practically meaningful relative age effect (Cohen's w = .039). The paper gives no age breakdown by title — [Frontiers](https://www.frontiersin.org/journals/sports-and-active-living/articles/10.3389/fspor.2025.1699838/full)
- A 2026 companion paper also finds no relative age effect across nations — [Frontiers in Psychology 2026](https://www.frontiersin.org/journals/psychology/articles/10.3389/fpsyg.2026.1829930/full) (not fetched)

**Chess (a comparison domain): Erilli & Dalar (2025), Scientific Reports [Peer-reviewed]**
- 1,814 grandmasters from the FIDE January 2024 list, modelled with 11 machine-learning methods. The mean peak Elo age is 30.65 (SD 7.61). Players who became GM at 15 or younger peaked at about 22.1. **GMs born in 2000 or later show peaks of about 19.8–21.3, an artefact of right-censoring because these players have not yet had time to peak later.** Only standard time control was analysed; there is no rapid or blitz analysis — [PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC12485108/)
- Japanese shogi: winning rates decline steadily after age 21. The authors cite international chess studies that find an inverted-U curve peaking around 21 — [arXiv 2204.07888](https://arxiv.org/pdf/2204.07888)

**Industry/marketing figures (low rigor)**
- A BetVictor (betting company) study reported by esports.gg in June 2022 says the "peak age" of competitive Fortnite is 16. It reports that 16-year-olds make up 27.15% of competitive players and account for $30.2M of earnings, the lowest peak of any esport, followed by Rocket League and Overwatch. The measure is the modal age among earners, not performance — [esports.gg](https://esports.gg/news/fortnite/fortnites-peak-competitive-age-is-16/)
- Rocket League: the median pro age is 21 per Esports Charts, compared with 25 for LoL and 26 for CS:GO (reported via an X post, July 2023) — [Nemesis_RL on X](https://x.com/Nem_RL/status/1759219890848747586?lang=en)
- Valorant Masters 2023: the average pro age was about 22. Team averages ranged from 19.4 (LOUD) to 29.3 (Team Secret) — [zleague.gg](https://www.zleague.gg/theportal/valorant-age-demographics-whats-the-average-age-of-valorant-players/)

### Inferences
- Across titles, the rigorous evidence clusters around the same figures: cognitive-motor slowing starts around 24 (with a wide CI), performance peaks around 20–24 (CS, LoL) and earnings peak around 19–21. Fortnite's observed "peak" of about 16 is much earlier than any biological estimate. That points to non-biological factors (selection, cohort, exit and meta) as the main drivers.
- The chess paper's finding that players born in 2000 or later peak at about 20 illustrates a trap that applies directly to Fortnite. When a game is young (released 2017) and every player is young, observed peak ages are truncated by construction.
- In SC2, older players compensated by using simpler strategies and playing more efficiently. That implies a biological decline in the early 20s would appear as a small, gradual loss, not a cliff. The HLTV CS data agrees: 0.74 KPR at age 20 against 0.65 at 29.

### Gaps
- No peer-reviewed study estimates a within-player (longitudinal) age curve for Fortnite, PUBG, Apex, Overwatch, Valorant, Rocket League, fighting games, osu! or Tetris. My searches did not find one.
- The exact decline rate from the LoL TPM paper and Kang's per-era lifespan figures sit behind 403 paywalls, so I could not extract them.
- I found no rigorous online blitz or bullet chess age-curve study (Lichess or Chess.com) and no Dota 2 age-curve study.
- "The business of play: careers and earnings in elite esports" (Journal of Cultural Economics, 2026) is relevant, but it was behind a login and I could not extract it — [Springer](https://link.springer.com/article/10.1007/s10824-026-09603-2)

## 2. What is the age distribution of Fortnite pros, and who peaked young and declined (or didn't)?

### Takeaway
Top-level Fortnite has been won mostly by players aged 14–19. Examples: Bugha at 16 (World Cup 2019), Cooper at 16 and Mero at 19 (Globals 2023), and Pollo at 16 and Peterbot at 17 (Globals 2024). The 2025 Globals broke that pattern with a trio that included 23-year-old Queasy. Several 2018–2020 stars (Mongraal, Benjyfishy, Bugha) faded in results by about 17–20. In every case the decline came alongside burnout, streaming, switching titles or changes to the meta, which makes it hard to attribute to biology.

### Cited Findings

**The minimum age is 13.** FNCS has required players to be at least 13 since it began — [Wikipedia: FNCS](https://en.wikipedia.org/wiki/Fortnite_Championship_Series). The 2019 World Cup had the same minimum, and Thiago "King" Lapp competed at 13 — (search snippet referencing [Washington Post](https://www.washingtonpost.com/sports/2019/07/29/who-is-kyle-giersdorf-year-old-who-won-million-fortnite-world-cup/) / [CNBC](https://www.cnbc.com/2019/07/29/fortnite-world-cup-finals-turned-these-teen-gamers-into-millionaires.html); CNBC returned 403 and was not verified directly).

**Champions and their ages**
- **Fortnite World Cup Solo, 28 July 2019: Bugha (Kyle Giersdorf, born 30 Dec 2002), age 16.** He scored 59 points against 33 for second-placed Psalm and won $3M — [Wikipedia: Bugha](https://en.wikipedia.org/wiki/Bugha_(gamer))
- **FNCS Global Championship 2023 (Copenhagen, 13–15 Oct, duos): Cooper (USA) and Mero (Matthew Faitel, Canada).** Cooper was 16. Mero was born 18 Sep 2004, making him 19 — [Wikipedia: FNCS Global Championship](https://en.wikipedia.org/wiki/FNCS_Global_Championship); [VideoGamer](https://www.videogamer.com/news/fortnite-mero-age/); [esports.gg](https://esports.gg/news/fortnite/cooper-and-mero-crowned-as-the-2023-fortnite-global-champions/). Mero had briefly retired before the pair formed in April 2023, and a coin toss decided whether he would return — [Fortnite Tracker](https://tracker.gg/fortnite/articles/the-story-of-fncs-global-championship-winners-mero-cooper)
- **FNCS Global Championship 2024 (Fort Worth, 7–8 Sep, duos): Peterbot (Peter Kata, born 20 Jun 2007), age 17, and Pollo (Miguel Moreno, born 8 May 2008), age 16** — [Wikipedia: Peterbot](https://en.wikipedia.org/wiki/Peterbot); [Wikipedia: Pollo](https://en.wikipedia.org/wiki/Pollo_(gamer))
  - Pollo was FNCS runner-up at 14 (C4S1, March 2023) and at 15 (C5S1), won C5S2 at 15 and C5S3 at 16, and won C6S1 at 16 (Feb 2025). That run tied the record of four consecutive FNCS titles. He began competing in 2020 at age 11–12 — [Wikipedia: Pollo](https://en.wikipedia.org/wiki/Pollo_(gamer))
  - Peterbot: first FNCS Grand Finals in Ch2S7 (2021). He placed 37th at the 2022 Invitational LAN and 26th at the 2023 Globals ("LAN struggles"). His 2024 breakthrough came at age 16–17. He was still winning in 2025–26 (2025 Pro-Am champion) and has about $1M in career earnings — [Wikipedia: Peterbot](https://en.wikipedia.org/wiki/Peterbot)
- **FNCS Global Championship 2025 (Lyon-Décines, 6–7 Sep, trios): SwizzY (Russia), Queasy (Aleksa Cvetković, Serbia, born 17 Apr 2002, so age 23) and Merstach (Latvia).** They won $450k of a $2.001M pool. Merstach had never placed higher than 15th at a LAN before. Queasy's earlier international results were limited by his teammate's visa problems — [Wikipedia: 2025 FNCS Global Championship](https://en.wikipedia.org/wiki/2025_FNCS_Global_Championship); Queasy's birth date is from [Liquipedia: Queasy](https://liquipedia.net/fortnite/Queasy) via search snippet. I did not find ages for SwizzY or Merstach (Liquipedia returned 403).
- **FNCS Global Championship 2026 (Antwerp, 26–27 Sep 2026, duos): SwizzY (Russia) and Pixie (Sweden) are listed as winners** — [Wikipedia: FNCS Global Championship](https://en.wikipedia.org/wiki/FNCS_Global_Championship). The event ended within the last day, so this is a single, very recent source and should be treated as provisional. I did not find Pixie's age. The format was a 2-day LAN of 12 games with $400k for first place and a new "net surge" rule — [Hotspawn, 23 Sep 2026](https://www.hotspawn.com/fortnite/news/fncs-global-championship-2026)

**Aggregate age figures**
- A BetVictor study (via esports.gg, 2022) found 16-year-olds were 27.15% of competitive earners and the modal "peak" — [esports.gg](https://esports.gg/news/fortnite/fortnites-peak-competitive-age-is-16/)
- esports.net (Feb 2025) says Fortnite's average competitive age is "around 16 to 17". It notes a 26-year-old (Sync) with high FNCS placements, and a 51-year-old who qualified for an FNCS event without winning — [esports.net](https://www.esports.net/news/fortnite/fortnite-champion-ages/). The same article lists "Persa" and "Kylie" (both 22) as "recent champions" under the 2024 Global Championship. That conflicts with the Wikipedia record, where the 2024 Globals winners were Peterbot and Pollo, so they are probably regional FNCS winners. **Treat that article as low reliability.**
- 2019 World Cup: search snippets repeatedly say the "average age of finalists was 16", but I could not trace this to a primary source. Kreo (Nate Kou), 18, finished 4th in solos (snippet attributed to CNBC/WaPo coverage, not verified).
- Esports-wide context: the mean age across 15,734 pros in 10 PC titles is 26.4, far older than Fortnite's champions — [Frontiers 2025](https://www.frontiersin.org/journals/sports-and-active-living/articles/10.3389/fspor.2025.1699838/full). Kang (2026) puts the battle royale earnings peak at about 19 — [RePEc](https://ideas.repec.org/a/sae/simgam/v57y2026i1p93-114.html)

**Peaked young, then declined in results**
- **Bugha**: won the World Cup at 16 (2019), then won FNCS Ch2S8 and the 2021 Grand Royale ($95k) at 18 and FNCS C3S1 in 2022 at 19. After that, placements were mostly 5th–23rd (2023) and 7th–14th (2024), with 14th at the 2024 Globals. Yearly earnings per Liquipedia: $3,081,292 (2019), $96,058 (2024), $48,350 (2025), $16,750 (2026 to date). He has 5.5M Twitch followers — [Wikipedia: Bugha](https://en.wikipedia.org/wiki/Bugha_(gamer)); earnings from [Liquipedia: Bugha](https://liquipedia.net/fortnite/Bugha) via search snippet. He is now 23 and still competes, so this is a plateau or decline rather than an exit.
- **Mongraal** (Kyle Jackson, born 13 Aug 2004): signed with Team Secret at 13 (April 2018). At the 2019 World Cup, aged 14–15, he placed 13th in solos and 6th in duos, earning $375k. He won FNCS Ch2S4 in 2020 at 16. He then failed to qualify for FNCS in Ch2 S5–S8 and "effectively retired" in 2021 at about 16–17, citing burnout. He returned in November 2023 when the Chapter 1 map came back, duoed with MrSavage in 2024 and split from him in February 2026. He has 7M Twitch followers — [Wikipedia: Mongraal](https://en.wikipedia.org/wiki/Mongraal)
- **Benjyfishy** (UK): broke through in 2018 at 14. He retired from Fortnite in June 2022 to play Valorant, citing burnout and lost enjoyment. He had played 8–10 hours a day, but in his final season he played only in tournaments — [Esports News UK](https://esports-news.co.uk/2022/06/24/benjyfishy-retires-fortnite-valorant/); [esports.net](https://www.esports.net/news/benjyfishy-reitiring-from-fortnite-too-many-pros-leaving-the-game/)
- **Clix** (Cody Conrod, born 7 Jan 2005): played the 2019 World Cup at 14 and is now 21. He is a leading streamer who has signed with Twitch — [esports.gg](https://esports.gg/news/fortnite/clix-fortnites-biggest-star/); [Wikipedia: Clix](https://en.wikipedia.org/wiki/Clix_(gamer))

**Counterexamples (elite in their 20s)**
- Queasy won the 2025 Globals at 23 — [Wikipedia](https://en.wikipedia.org/wiki/2025_FNCS_Global_Championship)
- SwizzY won back-to-back Globals in 2025 and 2026, per the provisional Wikipedia listing. His age was not found — [Wikipedia](https://en.wikipedia.org/wiki/FNCS_Global_Championship)
- Sync was noted at 26 with high FNCS placements — [esports.net](https://www.esports.net/news/fortnite/fortnite-champion-ages/)
- Bugha is still a top-10 finisher in Majors at 22–23 (6th–7th in early 2025 Majors) — [Wikipedia: Bugha](https://en.wikipedia.org/wiki/Bugha_(gamer))

### Inferences
- Fortnite champions have been getting older on average: roughly 16 (2019), 16/19 (2023), 16/17 (2024), a trio including a 23-year-old (2025), and a possible repeat by the 2025 champion (2026). That fits Kang's finding that competitive windows widen as a scene matures. It is also what you would expect as the original 2017–2019 cohort ages: when the game is young, all its elite players are young.
- The "peaked at 16" pattern among 2018–2020 stars coincides with the game's first boom (Chapter 1 and the 2019 World Cup prize pool of about $30M). A single event with an unusually large prize pool makes 2019 look like everyone's "peak year" in earnings. A 2019 earnings peak like Bugha's is an event artefact, not an age curve.

### Gaps
- No verified mean or median age of FNCS Grand Finalists by year. Building one would require scraping birthdates from Liquipedia, which blocked fetches (403).
- Ages of SwizzY, Merstach, Pixie and Cooper's exact birthdate were not found.
- I could not verify the claim that World Cup 2019 finalists averaged 16 against a primary source.

## 3. What explanations have been offered for Fortnite's young-peak phenomenon?

### Takeaway
Players and journalists overwhelmingly give non-biological explanations: burnout from the grind, the pull of streaming and other titles, and game and meta quality. The biological or reaction-time explanation is mostly asserted by writers and supported only indirectly by the SC2 study. The underlying academic literature on LoL likewise puts burnout, role inflexibility and poor mental-health support ahead of reflexes.

### Cited Findings
- **Burnout and grind:** Benjyfishy cited pressure, burnout, and the mental and physical toll of full-time play after years of 8–10 hours a day — [Esports News UK](https://esports-news.co.uk/2022/06/24/benjyfishy-retires-fortnite-valorant/). Mongraal's retirement in 2021 is framed as burnout, after which he focused on travel and fitness — [Wikipedia: Mongraal](https://en.wikipedia.org/wiki/Mongraal). Staying at the top requires constant grinding in Creative and matches, and Matsoe also left due to burnout — [esports.net](https://www.esports.net/news/benjyfishy-reitiring-from-fortnite-too-many-pros-leaving-the-game/); [Sportskeeda (summary via search)](https://www.sportskeeda.com/fortnite/why-fortnite-competitive-pros-quitting-game-alarming-rate)
- **Game design favors raw speed [Journalism/opinion]:** Sportskeeda argues that Fortnite rarely forces players to think through their play, that buildfights "can often be won just by being significantly faster", and that this rewards speed over strategy and "helps skew the player base younger" — (Sportskeeda content via search snippet; direct fetch returned 405) [Sportskeeda](https://www.sportskeeda.com/fortnite/why-fortnite-competitive-pros-quitting-game-alarming-rate)
- **Game and meta quality:** the same coverage says season quality fell after Chapter 1, lowering pros' motivation — [Sportskeeda (via search)](https://www.sportskeeda.com/fortnite/why-fortnite-competitive-pros-quitting-game-alarming-rate). Mongraal's return was triggered by the Chapter 1 map coming back in November 2023, which suggests meta and nostalgia affect participation — [Wikipedia: Mongraal](https://en.wikipedia.org/wiki/Mongraal)
- **Switching titles:** Benjyfishy moved to Valorant (2022) — [Sportskeeda](https://sportskeeda.com/fortnite/news-fortnite-pro-benjyfishy-quits-game-become-valorant-pro)
- **Streaming and content creation:** top veterans have very large streaming audiences (Mongraal 7M Twitch followers, Bugha 5.5M, Clix a Twitch signing), which gives them an income path that does not depend on results — [Wikipedia: Mongraal](https://en.wikipedia.org/wiki/Mongraal); [Wikipedia: Bugha](https://en.wikipedia.org/wiki/Bugha_(gamer)); [Sportskeeda: Clix](https://www.sportskeeda.com/esports/twitter-reacts-fortnite-pro-clix-officially-re-signs-twitch)
- **Community toxicity:** Itemm quit, calling the community immature — [Sportskeeda](https://sportskeeda.com/esports/news-fortnite-pro-player-itemm-quits-game-says-fortnite-community-immature)
- **LAN versus online:** Peterbot dominated online FNCS but placed 37th (2022 LAN) and 26th (2023 Globals) before winning at LAN in 2024 — [Wikipedia: Peterbot](https://en.wikipedia.org/wiki/Peterbot). This suggests LAN experience is a separate skill that develops with age.
- **Academic analogue (LoL):** burnout, role inflexibility and limited mental-health support accelerate decline — [Emerald TPM 2025](https://doi.org/10.1108/TPM-09-2024-0108)
- **Biological or reaction-time claims** mostly cite the SC2 onset at 24. A Frontiers paper says esports careers "peak and decline earlier" because reaction time, attentional control and decision efficiency matter — [Frontiers 2025](https://www.frontiersin.org/journals/sports-and-active-living/articles/10.3389/fspor.2025.1699838/full). A DBLTap piece on LoL argues against it with "The Myth of Reaction Time" — [DBLTap](https://www.dbltap.com/posts/the-myth-of-reaction-time-and-why-professional-league-of-legends-careers-are-so-short-01ecqq0r749m) (not fetched).

### Inferences
- The documented exits of 2018–2020 stars (Mongraal about 16–17, Benjyfishy about 18) happened years before the SC2 onset estimate of 24. Biological decline is therefore an implausible main cause for those cases. Burnout, alternative income and meta preference fit the documented statements better.
- The best-documented "age" signal pushes the other way: 2025 had an older champion trio, and players' LAN results improve with experience.

### Gaps
- I found no direct interviews with Fortnite coaches that give a specific account of age and performance. Reddit r/FortniteCompetitive threads on age did not surface in search, so anecdotal community views are uncatalogued here.
- No sourced discussion ties school or life obligations, or the earnings plateau, to Fortnite exits specifically.
- No evidence was found that Zero Build affected FNCS careers. FNCS competition has remained in build mode (not verified against an official source).

## 4. How often do Fortnite's competitive format and meta change, and how does that confound comparisons?

### Takeaway
Team size, scoring, surge rules, regions and core movement and building mechanics change roughly every season (about 3–4 FNCS cycles a year) and every chapter (about yearly). Team size alone changed at least 7 times from 2019 to 2026. That makes raw longitudinal comparisons (placements, earnings, points) across seasons weak measures of individual skill change.

### Cited Findings
- **Team-size history:** trios in 2019 (Season X); squads in Ch2S1 (Nov–Dec 2019); duos in Ch2S2 (Mar–Apr 2020); solos in Ch2S3 (Jul–Aug 2020); trios from Ch2S4 (Oct 2020) through Chapter 2; duos in Chapter 3 (2022) and Chapters 4–5 (2023–2024); trios in Chapter 6 (Dec 2024 into 2025); duos again in 2026 — [Wikipedia: FNCS](https://en.wikipedia.org/wiki/Fortnite_Championship_Series); [Fortnite Tracker, 7 Sep 2025](https://fortnitetracker.com/article/2389/fortnite-2026-competitive-news)
- **Regions:** there were originally 7 (EU, NA East, NA West, Brazil, Asia, Middle East, Oceania). NA East and West merged into NA Central in 2023, and West was reinstated in 2025 — [Wikipedia: FNCS](https://en.wikipedia.org/wiki/Fortnite_Championship_Series)
- **Scoring and surge:** the 2025 Globals awarded 65 points for a win and 4 per elimination — [Wikipedia 2025 GC](https://en.wikipedia.org/wiki/2025_FNCS_Global_Championship). The 2026 Globals used a new "net surge" mechanic based on damage given and taken, which "doesn't encourage pushing as much as the old rules" — [Hotspawn](https://www.hotspawn.com/fortnite/news/fncs-global-championship-2026)
- **The 2026 roadmap** (announced 7 Sep 2025): duos FNCS, an FNCS Mid-Season LAN, a Reload Elite Series LAN, a $1M Mobile Series, Ranked 2.0, the return of Pro-Am and the return of LAN to Europe — [Fortnite Tracker](https://fortnitetracker.com/article/2389/fortnite-2026-competitive-news)
- **Mechanics:** Chapter 4 added mantling and other movement changes, and Chapter 5 Season 1 overhauled movement toward "smoother, more realistic" motion, which the community criticized — [Sportskeeda Ch4](https://sportskeeda.com/fortnite/news-fortnite-chapter-4-adds-new-movement-mechanic); [Sportskeeda Ch5](https://sportskeeda.com/fortnite/fortnite-chapter-5-movement-makes-things-worse-already)
- **Event-driven prize swings:** Bugha earned $3.08M in 2019, driven by the one-off World Cup, against about $96k in 2024 — [Wikipedia: Bugha](https://en.wikipedia.org/wiki/Bugha_(gamer)); [Liquipedia](https://liquipedia.net/fortnite/Bugha)

### Inferences
- Because team size changes (solo, duo, trio, squad), a player's results depend on teammate quality and fit. Pollo and Peterbot won together in 2024 but played on different rosters in 2025 — [esports.net](https://www.esports.net/news/fncs-global-championship-2025-peterbot-pollo/). Individual decline cannot be read from team placements without adjusting for teammates.
- Changes to movement and building reset part of the skill set each chapter. Younger players who enter during a new chapter do not have to unlearn old habits, which is a cohort effect that looks like an age effect.
- Earnings-based age curves, including Kang's and BetVictor's, are distorted by one-off events like the 2019 World Cup.

### Gaps
- No complete, sourced season-by-season log of FNCS scoring changes, mechanic nerfs (e.g., to building or editing) and Zero Build's competitive status was compiled. Liquipedia and the official rules library would be the sources, but they were not fetched successfully.

## 5. What is documented about survivorship and selection effects (retirement, switching titles, streaming)?

### Takeaway
Exits are frequent, voluntary and non-random. Burnout, streaming and switching titles remove players from the data regardless of their skill. That produces classic survivorship bias: observed age curves are drawn from those who stayed, and "decline" often means "stopped trying" or "stopped entering".

### Cited Findings
- Mongraal left in 2021 (burnout), came back in 2023 and split from his duo in 2026. This is a non-monotonic career that a naive curve would score as a decline and then a recovery — [Wikipedia: Mongraal](https://en.wikipedia.org/wiki/Mongraal)
- Benjyfishy left for Valorant in 2022 — [Esports News UK](https://esports-news.co.uk/2022/06/24/benjyfishy-retires-fortnite-valorant/). Matsoe left due to burnout, and multiple pros departed around 2022 — [esports.net](https://www.esports.net/news/benjyfishy-reitiring-from-fortnite-too-many-pros-leaving-the-game/)
- Mero had retired before returning to win the 2023 Globals — [Fortnite Tracker](https://tracker.gg/fortnite/articles/the-story-of-fncs-global-championship-winners-mero-cooper)
- In LoL, six "legends" retired in 2019 with an average age of about 25 — [search summary citing LoL retirement coverage](https://doi.org/10.1108/TPM-09-2024-0108) (the attribution is loose, so treat it as anecdotal)
- In SC2, older players played fewer hours per week — [PLOS ONE](https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0094215). Reduced practice partly confounds age-related slowing.
- HLTV's CS sample is conditioned on reaching the Top 20, and its sample size peaks at 24. That means older ages are represented only by survivors — [HLTV](https://www.hltv.org/news/33610/when-do-counter-strike-players-peak)
- Right-censoring: in the chess study, players born in 2000 or later show artificially early peaks because they are young — [PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC12485108/)

### Inferences
- In Fortnite, players who remain competitive into their 20s may be positively selected, meaning they are better than those who left, which would flatten the apparent decline. Alternatively, top veterans may shift effort toward streaming while still entering events, which would steepen the apparent decline even though skill is unchanged (Bugha and Mongraal as possible cases). The direction of the net bias is unclear without data on practice hours.
- A defensible forecasting model should treat exit as a competing risk (for example, a survival model) rather than dropping players who leave. It should also control for team size, teammates, format era and LAN versus online.

### Gaps
- There is no quantitative retirement or attrition rate for Fortnite pros (for example, the share of 2019 World Cup qualifiers still reaching FNCS Grand Finals in 2025–26). It could be built from Liquipedia but was not found published.
- There are no documented data on pros' practice hours by age.
