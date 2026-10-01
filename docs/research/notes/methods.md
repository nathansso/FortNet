# Methods for Forecasting Pro Fortnite Player Decline and Tournament Rankings (Methods Survey)

Scope note: this file covers statistical/ML methodology (aging curves, decline-onset detection, multi-competitor rating systems, ranking forecasts, latent cognitive-motor constructs, pitfalls). Fortnite-specific data sources, scoring rules and player ages are assumed to be covered by other researchers. Sources marked "(standard reference, not fetched this session)" are canonical papers whose URLs are well known but whose contents were not re-verified in this session; the report writer should treat their specific claims with slightly more caution.

## 1. Sports aging-curve methods, published examples, and peak ages by sport

### Takeaway
The "aging wars" in baseball showed that method choice alone moves the estimated peak by ~3 years (26 vs 29-30): the delta method conflates survivors with average players, quadratic fixed-effects models force a symmetric curve that inflates peak age, and ignoring dropout (retired/demoted players) biases peaks later. Modern best practice is a semiparametric (spline/GAM or GP) mixed-effects model on all player-seasons, plus explicit handling of dropout (multiple imputation or survival-weighted), validated by leave-career-out CV. Peak age tracks the speed/reaction demands of the activity: ~21-25 in esports and sprint events, ~26-29 in baseball, ~30 for chess grandmasters.

### Cited Findings
**Delta method and its survivorship bias**
- The delta method restructures data into back-to-back "seasonal pairs," computes weighted average change by age, and chains the deltas into a curve; >20% of data is discarded because single-season players and final career years drop out. It gives MLB OPS peak at 26 and ~300 OPS points of decline from peak to age 41 — [Judge, Baseball Prospectus, "The Delta Method, Revisited" (July 2020)](https://www.baseballprospectus.com/news/article/59972/the-delta-method-revisited/)
- Lichtman's (2016) survivor-bias correction rests on the argument that players who are randomly unlucky in their final season do not return, while lucky ones do return and regress, which inflates measured decline. The correction yields a gentler post-peak decline with peak still at 26-27. Judge considers its theoretical basis questionable and says it works mainly as a shrinkage mechanism — [Baseball Prospectus](https://www.baseballprospectus.com/news/article/59972/the-delta-method-revisited/); see also [BP, "An Approach to Survivor Bias in Baseball"](https://www.baseballprospectus.com/news/article/59491/an-approach-to-survivor-bias-in-baseball/)
- Judge argues the delta method is biased toward early MLB arrivals who perform above average, so it underestimates the peak age of the average player — [Baseball Prospectus](https://www.baseballprospectus.com/news/article/59972/the-delta-method-revisited/)

**Parametric fixed-effects (Fair, Bradbury) and the "aging wars"**
- Fair (2008) used a nonlinear fixed-effects model with separate up-slope and decline segments constrained to meet at the peak, and put the peak at ~28. Bradbury (2009) used multiple regression with a quadratic age term and career-average performance as a covariate, and put the peak at ~29 for hitters and pitchers. A cited drawback of Bradbury is that it uses only players with long careers (selection) — [Nguyen & Matthews, arXiv 2210.02383 / J. Sports Analytics 2024](https://arxiv.org/pdf/2210.02383); [Fair, "Estimated Age Effects in Baseball" (updated 2025)](https://fairmodel.econ.yale.edu/rayfair/pdf/2005d.PDF); [Bradbury 2009, J. Sports Sciences](https://pubmed.ncbi.nlm.nih.gov/19308873/)
- According to Judge, "Team Bradbury" (quadratic, peak 29) and "Team Delta" (Tango/Lichtman, earlier peaks) were each partly wrong. The symmetric parabola pushed the peak up to 29, and the delta method mixed early-arriving high performers in with average trajectories — [Baseball Prospectus](https://www.baseballprospectus.com/news/article/59972/the-delta-method-revisited/)
- Judge's alternative, "GAM Across," is a GAM with thin-plate regression splines that controls for career-average performance and uses all seasons. It puts the peak at 27, matching the median individual peak, and it beat both delta variants on 2017-2019 out-of-sample data and in 5,000 leave-career-out resamples (training data MLB 1977-2016, ages 21-41, OPS relative to league average) — [Baseball Prospectus](https://www.baseballprospectus.com/news/article/59972/the-delta-method-revisited/)

**Selection-bias corrections via imputation**
- Nguyen & Matthews apply multilevel MICE (a two-level normal linear mixed model with heterogeneous within-group variance, R `mice`, m=5 imputations × 30 iterations, pooled with Rubin's rules) to fill in unobserved seasons of dropped or retired players. They simulate MAR dropout (removal after low performance), MCAR dropout (random retirement at 30) and MNAR dropout (low performers not promoted until 25). On MLB data the peak moves from 30 without imputation to 26 with it, and imputed curves have much lower MAE in simulation — [arXiv 2210.02383](https://arxiv.org/html/2210.02383v3); [J. Sports Analytics 2024](https://journals.sagepub.com/doi/10.3233/JSA-240744)
- The same regression-plus-imputation idea was applied to the NHL by Schuckers et al. (2023, Annals of Operations Research) and to Swedish football by Säfvenberg (2022) — [arXiv 2210.02383](https://arxiv.org/html/2210.02383v3); [Schuckers et al., Annals of OR](https://link.springer.com/article/10.1007/s10479-022-05127-y); [arXiv 2110.14017](https://arxiv.org/pdf/2110.14017)
- Schall & Smith (2000) and Lichtman (2009) are the key earlier references on survival bias in aging curves — [arXiv 2210.02383](https://arxiv.org/html/2210.02383v3)

**Hierarchical Bayesian, GP and FDA approaches**
- Berry, Reese & Larkey (1999, JASA) fit a flexible hierarchical aging model to compare players across eras in hockey, golf and baseball, estimating aging and era effects jointly — [search summary of the literature, arXiv 2210.02383](https://arxiv.org/pdf/2210.02383)
- Page, Barney & McGuire (2013) used Gaussian-process regression inside a hierarchical Bayesian model to estimate NBA age effects — [arXiv 2210.02383 lit review](https://arxiv.org/html/2210.02383v3)
- Vaci et al. (2019) used Bayesian cognitive latent-variable modeling of NBA aging and career performance, accounting for position and activity level — [arXiv 2210.02383 lit review](https://arxiv.org/html/2210.02383v3)
- Wakim & Jin (2014) applied functional data analysis (functional PCA) to NBA and MLB aging curves, describing it as more general and flexible than parametric curves — [arXiv 1403.7548](https://arxiv.org/abs/1403.7548)
- Dae-Jin Lee (arXiv, Aug 2026), "Modelling Athletic Ageing Relative to an Estimated Performance Envelope," targets sparse, irregular career data explicitly. RACE first estimates a population high-centile performance envelope by age, then models each athlete as a shape-translation-and-rotation (STAR) nonlinear mixed-effects transform of that envelope, with level, timing and tempo parameters. The application is MLB Statcast sprint speed and bolt rate. Envelope curvature governs identifiability: timing can be recovered for bolt rate but not for sprint speed — [arXiv 2608.06635](https://arxiv.org/abs/2608.06635)

**Chess (Elo-based aging)**
- Vaci, Gula & Bilalić (2015) found that chess Elo trajectories follow Simonton's three phases (rise, post-peak decline, stabilization) and fit a cubic rather than quadratic function. Pre-peak increase is proportional to post-peak decrease, but experts' decline stabilizes earlier, and players who played more tournaments declined less. They also warn that the FIDE database has serious methodological problems (range restriction) — [ChessBase summary](https://en.chessbase.com/post/the-age-related-decline-in-chess); [PMC "Restricting range restricts conclusions"](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC4053764/)
- Erilli & Dalar (Scientific Reports, 2025) studied 1,814 GMs from the Jan 2024 FIDE list with 11 ML regressors, 5-fold CV and 1,000-iteration bootstrap CIs. Mean peak-Elo age is 30.65 (SD 7.61). Players who became GM before 20 peaked at 24.61, and those who became GM before 15 peaked at 22.11. Only 1,814 of 440,386 rated players are GMs, which is itself strong survivor selection — [PMC12485108](https://pmc.ncbi.nlm.nih.gov/articles/PMC12485108/)

**Peak age by sport and speed demands**
- Allen & Hopkins (2015, Sports Medicine) systematically reviewed elite peak ages. Sprints, jumps and throws peak around 25 for both sexes. Sprint swimming peaks around 24 for men and 22 for women, and endurance swimmers peak about a year earlier — [Springer](https://link.springer.com/article/10.1007/s40279-015-0354-3); [RealClearScience summary](https://www.realclearscience.com/journal_club/2015/06/25/this_is_when_athletes_hit_their_peak_109280.html)
- Thompson, Blair, Chen & Henrey (2014, PLOS ONE) used piecewise regression on 3,305 StarCraft 2 players aged 16-44 and found that in-game self-initiated response times start slowing at age 24. Expertise did not attenuate the decline. Dual-task performance showed no age decline, and older players appeared to compensate with game mechanics that lower cognitive load — [PLOS ONE](https://journals.plos.org/plosone/article?id=10.1371%2Fjournal.pone.0094215)
- A study of 4,159 League of Legends pros found performance peaks near age 21 and then declines quickly, with burnout, role inflexibility and limited mental-health support as qualitative contributors — [Team Performance Management (Emerald), doi 10.1108/TPM-09-2024-0108](https://doi.org/10.1108/TPM-09-2024-0108)
- The average CS:GO pro age is reported at 22.7, and HLTV has an analysis of when Counter-Strike players peak — [HLTV](https://www.hltv.org/news/33610/when-do-counter-strike-players-peak); [Nerdly (secondary, lower quality)](https://www.nerdly.co.uk/2025/03/14/the-age-factor-in-esports-how-long-can-a-pro-gamer-stay-on-top/)
- Kang (2026, Simulation & Gaming) studies esports player ages, prize distributions and competitive lifespans from 1997-2023 — [SAGE](https://journals.sagepub.com/doi/10.1177/10468781251371070) (abstract not fetched; findings unverified)

### Inferences
- Across these sources there is an ordering: esports/twitch-reflex (~21-24) < sprint/power (~25) < baseball (~26-29) < chess (~30+). This fits the hypothesis that the more a task depends on raw processing speed relative to accumulated knowledge, the earlier the peak. Fortnite, which demands fast building/editing mechanics plus strategic rotation, should sit at or below the SC2/LoL range (roughly 18-24), though that is an extrapolation.
- For Fortnite, a "GAM Across"-style model (player random intercept, or career-mean covariate, plus a smooth age term) or a hierarchical GP is the recommended baseline, not the delta method. Esports careers are short and dropout is heavy, so delta-method survivor bias will be severe.
- With irregular tournament sampling, model at the event level with continuous age (days), not age-in-years bins. GPs, penalized splines and FDA all handle this naturally.
- RACE (envelope plus individual transforms) suits sparse elite data well: it estimates the frontier from the top centile and gives each player level/timing/tempo parameters that can be shrunk hierarchically.
- The chess finding that earlier achievers peak earlier implies age-at-entry should enter the model as a covariate or interaction, not be ignored.

### Gaps
- No peer-reviewed Fortnite-specific aging-curve study was found.
- I did not locate the full text of Page et al. (2013), Berry et al. (1999) or Schuckers et al. (2023) in this session. Their method descriptions come from the lit review in Nguyen & Matthews.
- Tennis, hockey and track-and-field specific aging-curve papers (beyond Allen & Hopkins) were not fetched.
- FiveThirtyEight and FanGraphs aging methodology posts were not retrieved.

## 2. Decline-onset forecasting: changepoints, survival, state-space, HMMs

### Takeaway
There is little sports-specific literature applying changepoint or survival models to decline onset, but the standard tools transfer directly. Piecewise/segmented regression is how the SC2 decline onset at 24 was identified. BOCPD gives an online probability that a player's performance regime has changed. State-space/Kalman models (Glickman-Stern, and Glicko as an EKF) track latent skill with time-varying uncertainty. Retirement is best treated as a competing or informative dropout event, not ignored.

### Cited Findings
- Adams & MacKay (2007) BOCPD computes online the posterior over "run length" (time since the last changepoint) by message passing, assuming parameters before and after a change are independent. The output is a probabilistic stream of change beliefs, not a retrospective segmentation — [arXiv 0710.3742](https://arxiv.org/pdf/0710.3742); [Gundersen explainer](https://gregorygundersen.com/blog/2019/08/13/bocd/); [Python impl.](https://github.com/hildensia/bayesian_changepoint_detection)
- No sports or athlete-career application of BOCPD turned up in search results; documented applications are finance, biometrics and robotics — [search results summary for BOCPD](https://www.alphaxiv.org/abs/0710.3742)
- Piecewise regression was the method Thompson et al. used to locate the age-24 onset of cognitive-motor slowing — [PLOS ONE](https://journals.plos.org/plosone/article?id=10.1371%2Fjournal.pone.0094215)
- Glickman & Stern (2005) developed a Bayesian state-space paired-comparison model for NFL team strength, with week-to-week and season-to-season variance components — [arXiv 2308.02414 (Duffield et al.) review](https://arxiv.org/pdf/2308.02414)
- Duffield, Power & Rimella (JRSS-C 2024), "A state-space perspective on modelling and inference for online skill rating," unify Elo, Glicko and TrueSkill as filtering and smoothing approximations in a state-space model. Elo corresponds to steady-state Kalman filtering, and Glicko's propagate/assimilate steps match an Extended Kalman filter (formalized by Ingram 2021 and by Szczecinski & Tihon 2023) — [JRSS-C](https://academic.oup.com/jrsssc/article/73/5/1262/7734616); [arXiv 2308.02414](https://arxiv.org/html/2308.02414); [Szczecinski, arXiv 2104.14012](https://arxiv.org/pdf/2104.14012)
- A state-space degradation model has been applied to F1 tire wear (Cappello & Hoegh 2026), showing the framework used for decline or degradation in sport — [SAGE](https://journals.sagepub.com/doi/10.1177/22150218261446170)
- PELT (Killick, Fearnhead & Eckley 2012, JASA) gives exact offline multiple-changepoint segmentation in linear expected time under penalized cost — [arXiv 1101.1438](https://arxiv.org/abs/1101.1438) (standard reference, not fetched this session)
- In mixture-cure survival modeling, when survival curves plateau the population is modeled as "cured" plus "not cured," and hierarchical versions borrow strength across datasets. Informative priors on the uncured component reduce bias — [Bayesian hierarchical mixture cure model, arXiv 2401.13820](https://arxiv.org/html/2401.13820)

### Inferences
- Recommended pipeline: (a) a latent-skill state-space model (a Glicko/TrueSkill-through-time style smoother) produces a per-event skill estimate with uncertainty; (b) run BOCPD (online) or PELT (retrospective labeling) on that smoothed skill series, not raw placements, which are extremely noisy with 100 players; (c) define "decline onset" as a changepoint whose post-change mean slope is negative and exceeds a threshold, and validate on retired players.
- For time-to-decline or time-to-retirement, use a Cox or AFT model with time-varying covariates (current skill level, recent slope, age, tenure, earnings) and treat retirement or inactivity versus measured decline as competing risks (Fine-Gray or cause-specific hazards). A mixture-cure component can capture the plateau of players who never "decline" within the observation window (young, recently active).
- HMMs with ordered states (rising, peak, declining, inactive) are a discrete alternative to BOCPD. They are interpretable but need care with non-stationary transition probabilities that depend on age; making the transitions depend on age via a logistic link is a natural extension.
- Esports sampling is irregular (tournament clusters, off-seasons), so continuous-time state-space models are preferable: diffusion variance proportional to elapsed time, as in Glicko's RD growth.

### Gaps
- No published example was found of changepoint detection or competing-risks survival applied to esports player decline. This would be novel.
- Specific HMM-for-athlete-form papers were not retrieved.

## 3. Latent skill rating systems for 100-player free-for-all and team formats

### Takeaway
For battle royale placements, the candidates are TrueSkill (factor graph, handles teams and multi-way rankings), TrueSkill 2 (adds per-player stats such as kills, experience and squad effects), Weng-Lin / OpenSkill (closed-form Plackett-Luce or Thurstone-Mosteller updates, much simpler and comparably accurate), and Elo-MMR (built for massive contests: linear runtime, monotone/incentive-compatible, robust bounded updates). Elo-MMR and Weng-Lin Plackett-Luce are the most natural fits for 100-player results. TrueSkill 2's approach of feeding eliminations into skill inference maps directly onto Fortnite's placement + elimination scoring.

### Cited Findings
- TrueSkill 2 (Minka, Cleven & Zaykov, MSR-TR-2018-8) adds player experience, squad membership, individual kill counts, quit tendency, and skill in other game modes. It predicted historical Halo/Gears match outcomes with 68% accuracy vs 52% for TrueSkill, and it changes the squad-skill aggregation assumption — [MSR PDF](https://www.microsoft.com/en-us/research/wp-content/uploads/2018/03/trueskill2.pdf); [MSR page](https://www.microsoft.com/en-us/research/publication/trueskill-2-improved-bayesian-skill-rating-system/)
- Letting TrueSkill skills drift over time is covered in Bishop et al.'s Model-Based Machine Learning ch. 3 — [MBML book](https://mbmlbook.com/TrueSkill_Allowing_the_skills_to_vary.html)
- Weng & Lin (JMLR 2011) treat a k-team game as several two-team games and approximate expected performance to get closed-form updates, avoiding numerical integration. Supported models include Bradley-Terry, Thurstone-Mosteller and Plackett-Luce (the multi-player generalization of Bradley-Terry). Accuracy is competitive with TrueSkill with shorter runtime and code — [JMLR](https://jmlr.org/papers/v12/weng11a.html); [PDF](https://jmlr.csail.mit.edu/papers/volume12/weng11a/weng11a.pdf)
- An independent rating-system comparison on Halite AI competition data (multi-player FFA) compared TrueSkill, Weng-Lin variants and others — [Janzert rating report](https://janzert.com/halite/rating-report/)
- Elo-MMR (Ebtekar & Liu, The Web Conference 2021) is a Bayesian rating system for contests with many participants. It is "Massive" (linear runtime in players), "Monotonic" (incentive-compatible: a rating-maximizing player always wants to do well) and "Robust" (bounded rating changes, with a smaller bound for more consistent players). It processes all of Codeforces (300K+ users, 1,000 contests) in under a minute, an order of magnitude faster than Codeforces' own system, with better accuracy. It is explicitly aimed at discrete ranked matches such as programming contests, obstacle-course races and video games — [ACM](https://dl.acm.org/doi/fullHtml/10.1145/3442381.3450091); [arXiv 2101.00400](https://arxiv.org/abs/2101.00400); [PDF](https://cs.stanford.edu/people/paulliu/files/www-2021-elor.pdf); [code](https://github.com/EbTech/Elo-MMR)
- Dehpanah, Ghori, Gemmell & Mobasher (ICAI'21) evaluated three popular rating systems on 25,000+ team battle royale matches. Evaluation metrics disagreed considerably, some metrics were heavily affected by new players, and many could not distinguish certain player groups. NDCG was most reliable and flexible, since it can focus evaluation on chosen player groups — [arXiv 2105.14069](https://arxiv.org/abs/2105.14069); companion FFA study [arXiv 2008.06787](https://arxiv.org/pdf/2008.06787); team-skill aggregation study [arXiv 2106.11397](https://arxiv.org/pdf/2106.11397)
- A Tilburg thesis rates battle royale players (van Riel), and Kaggle PUBG placement-prediction work predicts `winPlacePerc` from in-match stats with tree models — [van Riel thesis](http://arno.uvt.nl/show.cgi?fid=149149); [Rank Prediction in PUBG, Springer](https://link.springer.com/chapter/10.1007/978-981-33-4367-2_82); [PUBG survival analysis arXiv 1905.06052](https://arxiv.org/pdf/1905.06052)
- PandaSkill (arXiv 2501.10049) builds player performance and skill ratings for League of Legends esports by combining per-player performance scores with rating updates — [arXiv 2501.10049](https://arxiv.org/pdf/2501.10049)
- Glicko adds time-varying uncertainty (RD) to Elo, tracking both the location and spread of skill — [Duffield et al.](https://arxiv.org/html/2308.02414); Glicko-2 spec: [glicko.net](http://www.glicko.net/glicko/glicko2.pdf) (standard reference, not fetched this session)
- Original TrueSkill: Herbrich, Minka & Graepel, NIPS 2006 — [MSR](https://www.microsoft.com/en-us/research/publication/trueskilltm-a-bayesian-skill-rating-system/) (standard reference, not fetched this session)

### Inferences
- Solo cash cups and FNCS heats are 100-player FFA or team-FFA rankings. Plackett-Luce (via Weng-Lin/OpenSkill) and Elo-MMR model the full ordering natively. Pairwise-decomposition methods (Elo applied to all 4,950 pairs) over-weight one match and should be avoided.
- Duos and trios: TrueSkill/Weng-Lin assume team performance is the sum of member skills. TrueSkill 2 found this assumption needed revising. The Dehpanah et al. aggregation study is directly relevant, and max/mean aggregation alternatives should be tested. Individual-level signals (eliminations, damage) help separate teammates.
- Fortnite points = placement points + elimination points. A two-channel model is advisable: (a) a placement-ranking channel (Plackett-Luce/Elo-MMR) and (b) an elimination-count channel (Poisson/negative-binomial with player random effects and a latent aggression/mechanics factor), combined by simulation to forecast total points. This mirrors TrueSkill 2's use of kill counts.
- Late-game placement is much noisier than top-heavy scoring implies (storm RNG, third-parties). Plackett-Luce with player-specific variance (Elo-MMR's robustness to volatile players) handles heteroscedastic performers better than homoscedastic TrueSkill.
- Tuning the skill-drift (dynamics) variance is the lever that connects rating systems to aging. Rather than a constant drift, use an age-dependent mean drift (a prior aging curve from Section 1) so the rating filter "expects" decline past the estimated peak.

### Gaps
- Could not verify from the fetched abstract which three systems Dehpanah et al. compared (likely Elo, Glicko, TrueSkill, unconfirmed) or their numeric results.
- Elo-MMR's full experimental comparison tables (vs TrueSkill/Glicko on specific datasets) were not extracted.
- No published benchmark of OpenSkill/Elo-MMR on Fortnite competitive data was found.

## 4. Forecasting tournament rankings: losses, metrics, CV, regime shifts

### Takeaway
Evaluate with a mix of ranking metrics (NDCG@k, Spearman/Kendall) and probabilistic metrics (log-loss/Brier on top-k or qualification events). Use rolling-origin (expanding-window) time-series CV split by event date, never random splits. Model patch/season regime shifts explicitly with extra skill-variance inflation at patch boundaries, season fixed effects, or down-weighting older data.

### Cited Findings
- On battle royale data, NDCG was the most reliable evaluation metric. Other metrics were distorted by new players or failed to separate player groups, and NDCG's discount can focus evaluation on the top of the leaderboard — [Dehpanah et al., arXiv 2105.14069](https://arxiv.org/abs/2105.14069)
- Judge's aging comparison used both forward-in-time testing (train 1977-2016, test 2017-2019) and leave-career-out resampling (5,000 iterations) — [Baseball Prospectus](https://www.baseballprospectus.com/news/article/59972/the-delta-method-revisited/)
- Erilli & Dalar used 5-fold CV plus percentile bootstrap for peak-age CIs. That design is appropriate for cross-sectional peak estimation but is not a time-series forecast design — [PMC12485108](https://pmc.ncbi.nlm.nih.gov/articles/PMC12485108/)
- Glickman-Stern style state-space models separate short-term (week) and long-term (season) variance, a direct template for patch-level vs season-level shocks — [Duffield et al., arXiv 2308.02414](https://arxiv.org/pdf/2308.02414)
- The TrueSkill "skills allowed to vary" formulation adds a per-time-step dynamics variance to skill — [MBML book ch. 3](https://mbmlbook.com/TrueSkill_Allowing_the_skills_to_vary.html)

### Inferences
- Suggested metrics: (1) NDCG@10/@50 on the final leaderboard; (2) Spearman ρ between predicted and actual ranks among players who played both; (3) log-loss or Brier for binary events such as top-10, qualification or top-100 heat advancement; (4) CRPS or pinball loss if predicting point totals; (5) calibration plots of top-k probabilities. Report all against baselines: last-event rank, rolling-mean points, and prior-season earnings.
- Ranking-loss training options if an ML model is used: pairwise (RankNet/LambdaRank), listwise (ListNet, which is Plackett-Luce likelihood), or LambdaMART in LightGBM/XGBoost with `rank:ndcg`. A listwise Plackett-Luce loss is the same likelihood as the rating model, so the two can share structure.
- CV: rolling-origin by event (train on events before t, predict event t), grouped so all heats of one tournament land in the same fold. For decline models, also use leave-player-out CV to test generalization to unseen careers.
- Regime shifts: (a) inflate skill variance at each major patch or chapter start (Glicko RD reset analog); (b) add chapter/season random effects on the performance scale; (c) exponential time-decay weighting; (d) optionally run BOCPD on league-wide aggregates to detect meta shifts. Patch-invariant "mechanics" skill vs patch-sensitive "meta adaptation" skill is a natural two-factor split (see Section 5).

### Gaps
- No peer-reviewed paper specifically on patch/meta regime handling in esports rating was found in this session.
- FiveThirtyEight methodology posts (e.g., Elo with K and mean-reversion between seasons) were not fetched.

## 5. Incorporating a latent "cognitive-motor capacity" construct

### Takeaway
There is direct esports evidence (StarCraft 2) that in-game response latency declines from about 24 regardless of skill, while strategic and dual-task components do not decline and older players compensate strategically. That supports a two-factor latent model: mechanical speed, age-sensitive with an early peak, and strategic/game-knowledge, experience-sensitive with a late or no peak. Hierarchical Bayesian latent-variable aging curves (Vaci et al. 2019, NBA) are the closest published sports template.

### Cited Findings
- SC2 (Thompson et al. 2014): self-initiated response times begin slowing at 24. Expertise does not attenuate this domain-specific decline. Dual-task performance shows no age decline, and older players use game mechanics that reduce cognitive load to compensate — [PLOS ONE](https://journals.plos.org/plosone/article?id=10.1371%2Fjournal.pone.0094215); [APS summary](https://www.psychologicalscience.org/news/minds-business/cognitive-motor-skills-start-to-fall-before-age-25.html)
- Vaci et al. (2019) used a Bayesian cognitive latent-variable model of NBA aging with position and activity-level moderators — [arXiv 2210.02383 lit review](https://arxiv.org/html/2210.02383v3)
- Chess: more tournament activity is associated with less decline and earlier stabilization (a practice/"use it" moderator) — [ChessBase summary of Vaci, Gula & Bilalić](https://en.chessbase.com/post/the-age-related-decline-in-chess)
- Lee's RACE framework decomposes each athlete into level, timing and tempo of aging relative to a frontier, and studies the correlation between ability level and aging rate in a "Functional Ageing Space" — [arXiv 2608.06635](https://arxiv.org/abs/2608.06635)
- TrueSkill 2 shows that auxiliary per-player statistics (kills, experience) improve latent-skill inference — [MSR](https://www.microsoft.com/en-us/research/wp-content/uploads/2018/03/trueskill2.pdf)

### Inferences
- Model sketch: for player i at time t, latent M_it (mechanical/cognitive-motor) and S_it (strategic). M_it = a_i + f_M(age_it) with f_M a GP or spline peaking early. S_it = b_i + f_S(experience_it) monotone or saturating. Observed outcomes load on both factors with different weights: eliminations/fight win rate lean on M, and placement/survival without elims leans on S. Telemetry (edit speed, build latency, APM-like measures, aim metrics if available) serves as direct indicators of M in a measurement model (SEM / multi-output GP / multi-task hierarchical model).
- This is identifiable only with multiple outcome channels. With placement alone, M and S collapse into one skill. Elims vs placement points per match give a minimal second channel.
- Include activity (matches played per month) as a moderator of decline, following chess.
- Fit in Stan/PyMC/NumPyro as a hierarchical model with partial pooling. Small elite samples make priors from the SC2/LoL literature valuable (e.g., informative prior on the M-peak age centered ~21-24).

### Gaps
- No published physiology- or cognition-informed aging curve for esports that links telemetry (reaction/edit speed) to competitive outcomes longitudinally was found. The SC2 study is cross-sectional ladder data, not pros followed over time.
- Did not find SEM applications to esports aging specifically.

## 6. Known pitfalls

### Takeaway
The dominant bias for esports decline is selective dropout (survivorship/MNAR retirement), followed by regression to the mean in noisy placements, cohort/era effects (game changes, prize structure), selection at entry (early-achievers peak earlier), and small elite samples. Each has a known mitigation.

### Cited Findings
- Survivorship: the delta method drops >20% of seasons and conflates early high performers with average players. Lichtman's correction exists because unlucky final seasons cause dropout — [Baseball Prospectus](https://www.baseballprospectus.com/news/article/59972/the-delta-method-revisited/)
- Ignoring dropout shifted the estimated MLB peak from 26 (imputed) to 30 (observed-only). Dropout can be MAR (performance-based removal), MCAR or MNAR (late promotion of low performers) — [Nguyen & Matthews](https://arxiv.org/html/2210.02383v3)
- Restricting to long careers (Bradbury 2009) is a selection drawback — [arXiv 2210.02383](https://arxiv.org/pdf/2210.02383)
- Functional-form bias: a symmetric quadratic pushed peak age up to 29 — [Baseball Prospectus](https://www.baseballprospectus.com/news/article/59972/the-delta-method-revisited/); chess curves are better fit by a cubic than a quadratic — [ChessBase](https://en.chessbase.com/post/the-age-related-decline-in-chess)
- Range restriction / database problems in chess aging studies — [PMC4053764](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC4053764/)
- Age-at-entry: GMs who earned the title before 15 peaked at 22.1, compared with an overall mean of 30.65 — [PMC12485108](https://pmc.ncbi.nlm.nih.gov/articles/PMC12485108/)
- Era effects: Berry, Reese & Larkey's hierarchical model estimates aging and era jointly across hockey, golf and baseball — [arXiv 2210.02383](https://arxiv.org/pdf/2210.02383)
- New or unrated players distort rating-system evaluation metrics in battle royale — [Dehpanah et al.](https://arxiv.org/abs/2105.14069)
- In esports, burnout, role inflexibility and limited mental-health support drive early exits (LoL), so dropout depends on non-skill factors as well as performance — [TPM 2025](https://doi.org/10.1108/TPM-09-2024-0108)

### Inferences
- Mitigations mapped to pitfalls:
  - Survivorship → mixed-effects/GAM on all player-events, plus multiple imputation (multilevel MICE) or joint modeling of dropout (shared-parameter model linking the retirement hazard to latent skill), plus sensitivity analysis under MNAR.
  - Regression to the mean → hierarchical shrinkage and state-space smoothing; never flag decline from a single bad cup.
  - Cohort/era/meta → season/chapter random effects, cohort (debut-year) terms, and relative-to-field metrics (percentile within event rather than raw points).
  - Small samples → partial pooling, informative priors from other esports, and reporting posterior intervals.
  - Age-at-entry → debut age as covariate and interaction with the age curve.
  - Non-performance exits (burnout, content creation, streaming) → competing-risks formulation rather than treating all exits as skill-driven.
- Age data quality (self-reported or missing birthdates for pros) is itself a likely pitfall. Consider measurement-error models or restricting to verified ages.

### Gaps
- No quantitative estimate of dropout rates or dropout mechanisms among pro Fortnite players was found in this methods-focused search.
- Cohort effects specific to esports titles (e.g., players who started on newer controls or builds) are not documented in the literature found.
