# ChessKE Data Story Audit

## Scope

This audit reviews:

- The master dataset in `cleaned_master_chess_players.csv`
- The legacy Streamlit dashboard in `chess_dashboard.py`
- The newer API-driven frontend surfaces in `frontend/src`

The goal is not just to ask "what can be charted?" but "what story does a normal user understand after seeing the product?"

## Executive Take

The project already has enough data to feel far more analytical than it currently does. The main gap is not raw chart count. The main gap is story design.

Right now, most surfaces answer:

- how many players are there
- who is top-ranked
- what do ratings look like

They do not yet answer the more useful user questions:

- how active is the ecosystem really
- who carries the platform's activity
- what kind of players make up the player base
- how quickly do new players disappear or stay
- which formats define Kenyan online chess
- what separates casual users from committed competitors
- where does skill concentration sit
- what patterns are surprising or counterintuitive

This is the difference between a dashboard and a data product.

## What Already Exists

### Legacy Streamlit coverage

Current Streamlit visuals and summaries in `chess_dashboard.py` focus on:

- total players
- total games
- average ratings
- join trend
- Africa heatmap
- games by format
- rating histograms
- leaderboards
- player search and player-level stats

This is good baseline coverage, but it is mostly descriptive and light on explanation.

### Frontend/API coverage

The newer frontend already goes further than the Streamlit app. It includes surfaces for:

- join trend
- discovery trend
- format composition
- activity buckets
- rating scatter
- correlation matrix
- percentile bands
- cohort retention

Relevant files:

- `frontend/src/app/page.tsx`
- `frontend/src/components/data-marvel.tsx`
- `frontend/src/components/deep-analytics.tsx`
- `frontend/src/components/trend-charts.tsx`

This means the current missed opportunity is only partly about missing charts. A large part of it is that many of the best analytical angles are not translated into plain-language insight.

## Dataset Reality Check

The current master CSV supports strong storytelling, but it also contains data-quality signals that should be surfaced transparently.

### Core facts from the current dataset

- Players tracked: 143,238
- Total games tracked: 75,699,844
- Median total games per player: 10
- Mean total games per player: 528.5
- 90th percentile total games: 1,018
- 99th percentile total games: 9,695.9

This is a highly skewed ecosystem. Averages alone are misleading.

### Rating coverage

- Rapid rating present: 80.7%
- Blitz rating present: 30.2%
- Bullet rating present: 22.4%
- Daily rating present: 21.6%
- Puzzle rating present: 94.9%

This is already a story:

- rapid is the dominant competitive format
- puzzle participation is far broader than board-play participation
- blitz and bullet are meaningful but secondary
- daily is niche

### Activity recency

Using `Last Online` as a recency proxy:

- active in last 7 days: 3,196
- active in last 30 days: 3,214
- active in last 90 days: 3,215
- inactive for more than 365 days: 27,660

This distribution is unusually concentrated and should be treated as both:

- a user-facing story opportunity
- a methodology note

Whether this reflects true activity or a snapshot/coverage artifact, users should not be left to infer it from raw numbers alone.

### Cohort and age structure

Join-year counts show the player base exploded recently:

- 2023: 15,769
- 2024: 28,903
- 2025: 77,395
- 2026: 2,654 so far

But newer players have much lower median game counts:

- 2023 join cohort median games: 83
- 2024 join cohort median games: 20
- 2025 join cohort median games: 3
- 2026 join cohort median games: 25

This suggests growth is broad, but shallow. That is a major storyline currently underexplained.

## Highest-Value Missed Opportunities

## 1. The ecosystem is top-heavy, but that story is not being told

### Why it matters

Users need to understand whether the chess ecosystem is broad-based or driven by a small committed core.

### Evidence

- top 1% of players generate 35.2% of all games
- top 5% generate 71.3%
- top 10% generate 86.8%

### What to add

- Lorenz curve for game volume
- cumulative share chart for players vs games
- power-user concentration explainer card

### Suggested plain-language interpretation

"Kenya's online chess activity is heavily concentrated. A small minority of highly committed players account for most recorded games, while the typical tracked player has played only 10 games."

### Why current visuals miss it

Total games and leaderboards show scale and top names, but they do not explain concentration.

## 2. Median vs average is a missing trust layer

### Why it matters

Current summary cards use averages. In a skewed dataset, averages flatter the ecosystem and hide what a normal player looks like.

### Evidence

- mean total games: 528.5
- median total games: 10

The gap is massive.

### What to add

- "Typical player vs power player" comparison card
- median and percentile ribbons beside averages
- distribution narrative with p50, p90, p99 markers

### Suggested interpretation

"The average player looks far more active than the typical player because the ecosystem has a long tail of extreme grinders."

## 3. Rapid dominates the ecosystem, but format identity is still underdeveloped

### Why it matters

Format preference is one of the clearest user-friendly stories in chess data.

### Evidence

- rapid rating coverage: 80.7%
- players with rapid games: 115,587
- players with blitz games: 43,244
- players with bullet games: 32,102
- players with daily games: 30,921
- among players with any format games, 96,041 are at least 80% concentrated in one format
- of those single-format-dominant players, 89,365 are rapid-dominant

### What to add

- "Kenya is a rapid-first ecosystem" hero insight
- specialization treemap or stacked bar
- specialist vs multi-format player segmentation

### Suggested interpretation

"Rapid is not just the largest format. It is the ecosystem's center of gravity. Most specialized players specialize in rapid, not blitz or bullet."

### Current gap

There is a format composition chart, but not a format identity story.

## 4. Casual, committed, and elite behavior tiers are missing

### Why it matters

Regular users understand people better than raw distributions. Segments are easier to remember than histograms.

### Evidence

Volume tiers:

- 0 games: 24,536
- 1 to 9 games: 45,750
- 10 to 49 games: 26,122
- 50 to 199 games: 17,208
- 200 to 999 games: 15,154
- 1k to 4.9k games: 10,892
- 5k+ games: 3,576

### What to add

- player pyramid or funnel
- tier cards: dormant, casual, active, committed, elite-volume
- segment narratives with counts and share of ecosystem

### Suggested interpretation

"Most tracked accounts are light-touch participants, while the visible competitive scene is carried by a much smaller committed core."

## 5. Growth without retention is a major story, but it is not framed explicitly

### Why it matters

User growth alone can create a false sense of health if newer cohorts do not sustain play.

### Evidence

Recent join cohorts are large, but play depth is thin:

- 2025 cohort size: 77,395
- 2025 median total games: 3
- 2024 cohort median total games: 20
- 2023 cohort median total games: 83

### What to add

- cohort maturation chart: cohort size vs median games vs recent activity
- retention funnel using recency buckets
- "new players acquired" vs "players still active after X days" copy

### Suggested interpretation

"The ecosystem has expanded dramatically, but most recent accounts are still shallow in activity. The next question is not only growth, but conversion into sustained play."

### Current gap

There is a cohort chart in the modern frontend, but it needs narration and stronger comparative metrics.

## 6. The current activity view should distinguish active universe from all-time universe

### Why it matters

Users need a clear separation between:

- all tracked players ever seen
- recently active players
- dormant legacy accounts

### Evidence

- 143,238 total tracked players
- only about 3.2k active within 90 days based on `Last Online`
- 27,660 inactive for more than a year

### What to add

- three-number "ecosystem state" card row
- active share gauge
- dormancy waterfall
- methodology warning when recency may be affected by collection constraints

### Suggested interpretation

"The all-time registry is large, but the current active ecosystem is much smaller. Both numbers matter, and they should never be conflated."

## 7. Multi-format versatility is a missing player-quality lens

### Why it matters

Users do not only care about who is strongest in one format. They care about who is adaptable.

### Evidence

Format-count distribution:

- 1 format played: 63,552
- 2 formats played: 22,755
- 3 formats played: 16,788
- 4 formats played: 15,607

Among active-within-90-days players:

- 1 format played: 1,462
- 2 formats played: 672
- 3 formats played: 481
- 4 formats played: 309

### What to add

- versatility index
- specialist vs all-rounder leaderboard
- spider/radar comparison for top versatile players

### Suggested interpretation

"Most players stay in one lane. The truly rounded players, who compete meaningfully across several formats, are a distinct minority."

## 8. Rating-volume quadrants are a stronger story than raw leaderboards

### Why it matters

Leaderboards reward top scores but ignore whether those scores are well-established or lightly tested.

### Evidence

Rating-to-log-volume correlations are positive but moderate:

- rapid: 0.347
- blitz: 0.391
- bullet: 0.315
- daily: 0.181

This means more games help, but volume alone does not explain strength.

### What to add

- four-quadrant view:
  - high volume, high rating
  - high volume, low rating
  - low volume, high rating
  - low volume, low rating
- "tested strength" score combining rating and game minimums
- outlier callouts

### Suggested interpretation

"Some players are strong because they are deeply battle-tested. Others look strong but on thin samples. That distinction matters."

## 9. Rapid vs blitz mismatch is a strong skill-profile story

### Why it matters

Cross-format gaps help explain playing style and temperament.

### Evidence

For players with at least 20 rapid and 20 blitz games:

- median blitz minus rapid gap: -222
- players with blitz 200+ above rapid: 491
- players with rapid 200+ above blitz: 9,805

### What to add

- rapid-vs-blitz delta distribution
- "calm thinker vs speed specialist" segmentation
- player profile badges based on format gap

### Suggested interpretation

"Most dual-format players perform substantially better in rapid than blitz, suggesting Kenya's online population is more comfortable with thinking time than pure speed pressure."

## 10. Puzzle strength vs actual play is underused

### Why it matters

Puzzle data is available for almost everyone. That makes it one of the best narrative tools in the dataset.

### Evidence

- puzzle rating coverage: 94.9%
- 64,349 players have a puzzle rating but fewer than 10 recorded games
- 1,245 players are in the top 10% of puzzle rating but have fewer than 50 total games

Puzzle correlations:

- with rapid rating: 0.55
- with blitz rating: 0.43
- with bullet rating: 0.40
- with daily rating: 0.36

### What to add

- "solvers vs competitors" segmentation
- puzzle-to-board gap chart
- hidden tactical talent leaderboard

### Suggested interpretation

"A large share of the ecosystem engages tactically through puzzles without deeply participating in rated games. Puzzle culture appears much broader than competitive play."

## 11. Dormant elite players are a missing emotional hook

### Why it matters

Users connect strongly with stories like "strong but inactive," "returning veterans," and "forgotten top players."

### Evidence

Among the top 1% in each skill domain, dormant for 180+ days:

- rapid: 59.9%
- blitz: 60.3%
- bullet: 60.4%
- puzzle: 86.0%

### What to add

- dormant elite spotlight
- active vs dormant top-tier comparison
- "if all top players returned" hypothetical share cards

### Suggested interpretation

"A surprising portion of the strongest players are not recently active. The talent base is broader than the currently visible competitive surface."

## 12. Win-rate storytelling is available, but not contextualized

### Why it matters

Win rate without format context can mislead. Draw culture differs by format, and so does game volatility.

### Evidence

For players with at least 20 games in the format:

- daily median win rate: 50.0%, median draw rate: 1.5%
- rapid median win rate: 47.9%, median draw rate: 4.4%
- blitz median win rate: 48.4%, median draw rate: 3.1%
- bullet median win rate: 48.6%, median draw rate: 1.2%

### What to add

- stacked outcome composition by format
- win-rate percentiles with minimum game thresholds
- "most decisive format" and "most draw-heavy format" insights

### Suggested interpretation

"Rapid produces the most draw-heavy outcome profile in this dataset, while bullet remains the most decisive and least draw-prone."

## 13. The Africa map lacks narrative context

### Why it matters

Maps are visually strong but analytically weak if they are left alone.

### What to add

- Kenya rank among African countries
- Kenya share of visible African player base
- benchmark against a few peer countries
- note whether map reflects active players, discovered players, or all tracked players

### Suggested interpretation

"The map should answer Kenya's regional position, not just show color."

## 14. The product needs benchmark language, not just raw ranks

### Why it matters

Users understand percentile and category labels better than isolated values.

### What to add

- rating bands like beginner, developing, competitive, advanced, elite-local
- percentile-backed player badges
- "better than X% of rated players in rapid"

### Current gap

The player search already computes rankings, but the product does not consistently translate those into user-friendly category language.

## 15. The methodology story should be more integrated into the main experience

### Why it matters

This dataset has real collection constraints:

- rolling discovery logic
- uneven refresh timing
- possible recency artifacts
- uneven field completeness

These should not live only on a methodology page.

### What to add

- inline "how to read this metric" text
- data freshness badges per chart
- "all-time vs recent-active" labels
- minimum sample disclaimers on leaderboards and win rates

## What Is Already Present But Underexplained

These analyses are already partly in the app, but they are not yet doing enough user-facing narrative work:

- correlation matrix
- percentile bands
- cohort retention
- activity buckets
- rating scatter

Each one needs one or two sentence takeaways directly above or below the chart.

Examples:

- "Rapid and puzzle strength move together more than bullet and puzzle strength."
- "The median player is far below the mean, showing strong right-skew."
- "Recent cohorts are large, but shallow in activity."
- "Only a thin layer of the total registry appears recently active."

## Recommended Story Modules

If the goal is "data marvel," these are the highest-value additions.

### Tier 1: Must-have

- Ecosystem state: all-time, recently active, dormant
- Player concentration: share of games by top 1%, 5%, 10%
- Typical vs elite player: median, p90, p99 activity and ratings
- Rapid-first identity: format dominance and specialization
- Cohort depth: join growth vs sustained activity
- Puzzle culture vs competitive play

### Tier 2: Strong differentiators

- Specialist vs all-rounder index
- Rating-volume quadrant maps
- Rapid vs blitz gap archetypes
- Dormant elite spotlight
- Format outcome style comparison

### Tier 3: Prestige features

- Narrative player archetype engine
- Benchmark badges for every player profile
- Dynamic chart annotations that explain anomalies
- "What changed since last update" summaries

## Recommended Explanation Style

Every major chart should have three layers:

### 1. What the user is seeing

One sentence describing the visual honestly.

### 2. Why it matters

One sentence translating the chart into ecosystem meaning.

### 3. What to be careful about

One sentence about sample size, coverage, or freshness when relevant.

Example:

"This chart shows how game volume is distributed across the player base. It reveals that a small minority of players generate most recorded activity, so averages overstate how active the typical player is. Because the dataset is a tracked registry rather than a census of every Kenyan chess account ever created, use these numbers as observed ecosystem structure, not a national total."

## Suggested New Metrics

Useful derived metrics the current project should consider adding:

- activity status: active_7d, active_30d, active_90d, dormant_365d
- format_count
- dominant_format
- dominant_format_share
- mean_board_rating
- rating_spread across formats
- puzzle_minus_board_rating
- player_volume_tier
- player_skill_tier
- versatility_index
- tested_strength_score using rating plus game threshold
- cohort_depth_score for join cohorts

## Product-Level Recommendation

The project should stop thinking in terms of "pages with charts" and start thinking in terms of "stories with evidence."

The strongest homepage sequence would be:

1. Ecosystem size vs real active core
2. Rapid-first identity
3. Concentration of play
4. Growth vs retention tension
5. Puzzle culture vs competitive culture
6. Specialist vs versatile player types

That sequence tells a coherent story. The current experience is richer than the old dashboard, but still too chart-led and not insight-led.

## Final Assessment

The data is already strong enough for a standout public-facing analytics product.

What is missing is not raw volume of charts. What is missing is:

- segmentation
- interpretation
- benchmark language
- honest treatment of skew
- clearer separation of all-time vs active population
- stronger player archetypes
- more narrative framing around the analyses that already exist

If these changes are made, the project stops being "a dashboard about Kenyan chess" and becomes "an intelligence product about how Kenyan online chess actually works."
