---
layout: single
title: "Demand Forecasting: Secondary Ticket Sales"
date: 2026-03-10
description: "How secondary ticket market velocity signals can inform dynamic primary pricing, and what a 12-part ML project revealed about demand in live events"
author_profile: true
toc: true
toc_sticky: true
classes: wide
tags:
  - machine learning
  - ticket market
  - forecasting
  - feature engineering
  - database engineering
  - business impact
excerpt: "Primary pricing teams at Ticketmaster and LiveNation set prices weeks in advance with limited demand visibility. The secondary market is a great proxy. This 12-part project built a system to read the secondary market for demand forecasting, reaching 13.37 RMSE and quantifying $1M+ annual value for a mid-size operator."
published: true
---

<style>
.streamlit-container { border: 1px solid #ddd; ... }
.dashboard-loading { text-align: center; ... }
</style>

<div class="streamlit-container">
  <div class="dashboard-loading">Loading interactive dashboard...</div>
  <iframe src="https://event-explorer.streamlit.app/?embed=true"
          height="800"
          style="width:100%;border:none;">
  </iframe>
</div>

## The Problem With Primary Pricing

When Ticketmaster or LiveNation price a concert, they are making a decision weeks or months before the show with limited real-time demand data. Price too low and they leave revenue on the table. Price too high and tickets stall, the show looks empty, and the artist's team gets unhappy.

StubHub already has a cleaner read on demand.

Secondary market listings and sales velocity update daily. If floor prices are holding firm ten days out and tickets are moving, demand is strong and the primary market likely underpriced the show. If floor prices are compressing at day five with little buyer activity, demand is soft and the primary market overpriced. Secondary market behavior is **a leading indicator** that most primary pricing teams monitor manually, if at all.

This project built a forecasting system that reads those signals at scale: **predicting 7-day secondary ticket sales for any event, using only the daily market snapshot data that StubHub reports**. The secondary forecast serves as the demand proxy. A primary pricing team using it can ask whether a show is gaining momentum or losing it, and whether they need to act before the final week.

---

## What I Built

I built a forecasting pipeline on 132 days of daily StubHub snapshot data covering **7.5 million rows, 138,000 events, and 14,600 venues**. The model predicts how many tickets will sell in the next seven days for any given event on any given day, with a point estimate and a 95% confidence interval.

**Results at a glance:**

| Metric | Value |
|--------|-------|
| Champion RMSE (3-week window) | **13.37 tickets** |
| Full test set RMSE | 18.53 tickets |
| Classifier precision | 76.3% |
| Training data | 7.5M+ daily snapshots |
| Test data | 389,230 |

The final model in Part 11 was evaluated on a 3-week business-relevant test window: the final three weeks before each event, where pricing decisions are most actionable. The Part 7 result (18.53) was evaluated on the full test set including earlier, lower-activity snapshots. Both are honest numbers on different evaluation windows.

**Progression across the project:**

| Part | Key change | RMSE |
|------|-----------|------|
| 4 | Two-stage pipeline | 19.15 |
| 6 | Hyperparameter tuning | 18.98 |
| 7 | Bayesian optimization | 18.53 |
| 9 | Embeddings | 19.09 |
| 11 | Lifecycle + external signals | 13.37* |

*\*3-week window; others are full test set*

The largest single improvement came not from algorithm changes but from architectural decisions: the two-stage pipeline (Part 4) and lifecycle interaction features (Part 11). Together these account for **more RMSE reduction than all hyperparameter tuning combined**.

---

## What the Market Data Shows

Before building any model, I looked at what secondary market data actually reveals. Three findings shaped the rest of the project.

### Floor prices drop about 10% as events approach

Secondary sellers reprice constantly based on real buyer activity. Aggregated across all event types, **floor prices drop roughly 10% in the final week before showtime**. This is sellers responding to weak demand before any official pricing action happens on the primary side.

[![Chart showing floor price declining as days to event approach zero](https://github.com/user-attachments/assets/bd32f380-278b-4d95-a28d-e5e5c4c25e6d)](https://github.com/user-attachments/assets/bd32f380-278b-4d95-a28d-e5e5c4c25e6d)*Floor price falls predictably as the event date approaches*

For a primary pricing team, a stable secondary floor at day ten is a sign that the original price held up. A falling floor at day fourteen is a signal that demand is softer than expected, and a promotional push might be needed before the window closes.

### Sales volume accelerates in the final week

Sales activity picks up significantly in the last seven days before an event. This is the window where the model is most useful: predictions are still actionable, but time to intervene is limited.

[![Market-wide average daily sales accelerating as events approach](/portfolio/image.png)](/portfolio/image.png)*Sales velocity increases 15x from 60+ days out to day-of*

### External shocks hit every category at once

On November 4th, Election Day, secondary sales dropped significantly across every event category with meaningful inventory. I confirmed this with seasonal z-scores, which compare each day to the distribution for that same day of the week. **The drop was statistically anomalous for a Tuesday,** as were several other days in my snapshots.

[![Seasonal anomaly detection showing actual vs expected daily sales](/portfolio/image-1.png)](/portfolio/image-1.png)*Election Day (Nov 4) produced the largest anomaly in the dataset, with a z-score of -2.6*

This is a real limitation of any model trained on historical patterns. Macro shocks from elections, major news events, or unexpected cancellations are **not predictable from market signals alone**. A production deployment would need override triggers for days where context clearly breaks the normal pattern.

---

## Business Impact

The model's value comes from two levers: dynamic primary pricing (adjusting face-value prices based on secondary velocity) and strategic inventory timing (holding back supply and releasing as demand confirms). The full analysis is in [Part 13](/seatdata.io-business-impact/).

[![Revenue impact vs operator scale, from mid-size to Live Nation](/portfolio/image-5.png)](/portfolio/image-5.png)*$42M to $323M annual revenue impact at Live Nation scale (20k events), depending on scenario assumptions*

The conservative case assumes 50% event signal rate (below the classifier's 67.6% recall), 8% premium inventory, 15% capture rate (well below LN Platinum's 70%+), and a $35 secondary premium (below the research average of 2x face value). The $42M conservative estimate at Live Nation scale represents about **14% of Ticketmaster's 2024 operating profit** ($311M).

The classifier reliably separates actionable events from dead inventory. For example, BLACKPINK showed a median classifier probability of 0.98, with 91.6% of snapshots flagged active and 60-90 secondary sales per week. Matilda the Musical showed a median probability of 0.016, with 0% flagged and zero sales at every tracked time point.

**Super Bowl LX** illustrates inventory timing. Secondary velocity surged from 89 tickets per week at D-21 to **717 tickets per week at D-7**, an 8x increase. The classifier stayed above 0.93 throughout. A hold-back strategy releasing inventory in tranches as velocity confirmed would have captured three weeks of price appreciation.

[![Super Bowl LX actual vs predicted velocity over the event lifecycle](/portfolio/image-2.png)](/portfolio/image-2.png)*Super Bowl LX: secondary velocity surged from 89 to 717 tickets per week in the final two weeks*

---

## How the Forecasting System Works

### Part 1: Structuring the Data

Four months of daily StubHub CSV snapshots were loaded into BigQuery and organized into a star schema connecting events, venues, and daily market readings. I also built an automated classification system that labeled the nearly **140,000 events into 38 categories** using regex patterns, distinguishing "Concert-Pop/A-List" from "Concert-Legacy/Tribute" from "NBA" without manual tagging after the rules were written.

These 38 categories were consolidated into seven modeling buckets: Broadway and Theater, Comedy, Concert, Festivals, Major Sports, Minor/Other Sports, and Other.

[![Entity relationship diagram showing the BigQuery star schema](https://github.com/user-attachments/assets/f8e86cd8-4023-48e2-9ee1-2cea7c3d71fd)](https://github.com/user-attachments/assets/f8e86cd8-4023-48e2-9ee1-2cea7c3d71fd)*The database schema connecting events, venues, and daily snapshots*

[Read the full post](/seatdata-io-database-engineering/)

### Part 2: Understanding What Drives Demand

The most useful EDA finding was the pricing tier structure across categories. Three distinct tiers emerged:

-   **Premium tier** (Festivals, Theater/Broadway): floor prices around $80
-   **Mid tier** (Concerts, Comedy, Other): $50-65
-   **Volume tier** (Major and Minor Sports): $30-40

This tier structure matters for primary pricing because a concert is not priced like an NBA game, and the signals that indicate healthy demand look different across tiers.

[![Median get-in price by event category showing three pricing tiers](/portfolio/image-4.png)](/portfolio/image-4.png)*Three distinct pricing tiers: Premium ($80+), Mid ($50-65), Volume ($30-40)*

I also found strong day-of-week seasonality. **Saturdays had the highest secondary sales volume, Tuesdays had the most variance**. Any model ignoring this structure would misread the market on off-peak days. Also, just a good-to-know if you want to go see a concert next weekend!

[Read the full post](/seatdata.io-eda/)

### Part 3: Preparing the Data

The raw sales distribution was heavily skewed. A small number of high-demand events drove thousands of weekly sales while most had zero. I applied a log transformation that **reduced skewness from 12.28 to 1.25**, making the model's errors more consistent across typical events.

Venue capacity was missing for **42% of events**, and it turned out to matter for predictions. I filled the gaps through a four-step pipeline: fuzzy name matching against a reference spreadsheet, Ticketmaster API lookups, Wikidata SPARQL queries, and finally category-level medians.

[![Side-by-side histogram showing raw vs log-transformed sales distributions](https://github.com/user-attachments/assets/9b506158-f066-46cb-a24f-8123fa640dfd)](https://github.com/user-attachments/assets/9b506158-f066-46cb-a24f-8123fa640dfd)*Skewness drops from 12.28 to 1.25 after log transformation*

[Read the full post](/seatdata.io-feature-engineering/)

### Part 4: Two-Stage Pipeline

In fact, sales were so sparse that **72% of daily snapshots had zero sales.** A standard regression model predicting into that structure spends most of its capacity learning to predict near zero, and fails on the events that actually matter.

My solution was a two-stage design. A classifier first decides whether any sales will happen at all. Then a separate regressor estimates how many, but only on the events the classifier flagged. This split alone cut prediction error by **40%** compared to single-stage regression. The gain came entirely from architecture, not from tuning.

[Read the full post](/seatdata.io-modeling-1/)

### Part 5: Neural Networks vs. Tree Models

I tested three deep learning architectures against tree-based models. The best neural network pipeline matched tree model accuracy (MAE 3.96 vs 3.89) but required **100x the training time**. For structured tabular data with engineered features, neural networks did not justify the extra cost. Tree-based models became the standard going forward.

[Read the full post](/seatdata.io-modeling-2/)

### Part 6: Hyperparameter Tuning

Random search over 30 hyperparameter combinations captured **95% of the available tuning gain**. The two most important parameters were learning rate and tree depth. Full-test RMSE dropped from 19.15 to 18.98, a 0.9% improvement.

The residual analysis showed something important: **the model consistently underestimates very high-demand events**. Pricing teams should treat a strong positive signal from the model as a minimum estimate, not a ceiling.

[![Actual vs predicted scatter plot and residual distribution](https://github.com/user-attachments/assets/5fa10364-4746-4e55-85d3-0ad63363e09f)](https://github.com/user-attachments/assets/5fa10364-4746-4e55-85d3-0ad63363e09f)*The model underestimates extreme events*

[Read the full post](/seatdata.io-modeling-3/)

### Part 7: Bayesian Optimization and Threshold Tuning

I replaced random search with 200-trial Bayesian optimization using Optuna. That moved RMSE from 18.98 to 18.78. But the **largest single gain in the project up to this point** came from a non-model change: raising the classifier's confidence threshold from 0.50 to 0.90.

At 0.50, the classifier activates the regressor whenever it is at least 50% confident of a sale. At 0.90, the regressor only runs when confidence is at least 90%. Moving to 0.90 pushed RMSE to 18.53. High-confidence predictions were substantially more accurate, and false positives on quiet events were driving disproportionate error.

[![Search strategy comparison across grid, random, and Bayesian optimization runs](https://github.com/user-attachments/assets/696d7d1d-dcf1-4aef-b29e-183d564c05c6)](https://github.com/user-attachments/assets/696d7d1d-dcf1-4aef-b29e-183d564c05c6)*Bayesian optimization converges faster than random search*

[Read the full post](/seatdata.io-modeling-4/)

### Part 8: One Model vs. Segment-Specific Models

Training a dedicated model per event category outperformed the unified model on one held-out test set. But cross-validation across three time windows showed a different result: **the unified model won or tied everywhere**. The test-set gains were specific to that time period. One model trained on all 7.5 million rows generalized better than seven models trained on subsets.

[![Bar chart comparing segment model results vs unified model across categories](https://github.com/user-attachments/assets/4a35a3ad-0d67-4dd7-9e22-eeab31c8c295)](https://github.com/user-attachments/assets/4a35a3ad-0d67-4dd7-9e22-eeab31c8c295)*Segment models appear better on one test window but do not hold up across time folds*

[Read the full post](/seatdata.io-segmentation/)

### Part 9: Testing Semantic Embeddings

I tested whether the model could benefit from knowing something about the identity of each event. I built a pipeline that fetches Wikipedia summaries for 18,000 artists, venues, teams, and events, converts them into 384-dimensional vectors using the `all-MiniLM-L6-v2` sentence transformer, and compresses them to 102 dimensions with PCA. For artists without a Wikipedia page, I used Last.fm bios and genre tags as a fallback.

**The result: embeddings do not improve overall accuracy.** All embedding configs were slightly worse than the baseline on the full test set. The tabular market features already encode identity at prediction time. A $300 get-in price and 15 active listings in a 20,000-seat venue tells you more about likely demand than a Wikipedia biography.

Sports were a partial exception: team embeddings produced small but consistent improvement, because team identity (market size, standings, rivalry context) is harder to encode through price and listing signals alone. This pointed toward the structured external features that would drive the gain in Part 11.

[Read the full post](/seatdata.io-embeddings-nlp/)

### Part 10: Social Signals

I tested whether social media and web traffic data could improve predictions. The pipeline collected Google Trends interest scores, Spotify monthly listeners, and social media follower counts for artists, then joined these onto training data via the slug system built in Part 9.

Social signals showed a small positive effect for concerts but added noise for other categories. The features were too static: an artist's Spotify listener count does not change meaningfully between ticket snapshots. What worked better was the momentum signal from Part 11's lifecycle features, which captured the same demand energy through time-varying market data rather than fixed identity metrics.

[Read the full post](/seatdata.io-social-features/)

### Part 11: Lifecycle Interactions and External Enrichment

This was the breakthrough. Two changes drove RMSE from 18.53 to **13.37**: fixing a subtle data leakage issue in how temporal features were computed, and adding lifecycle interaction features that combine "days to event" with market state variables.

The lifecycle interactions capture something the model previously missed: the same floor price means different things at different points in an event's sales cycle. A $50 floor at T-30 is neutral. A $50 floor at T-3 signals strong residual demand. The interaction terms let the model read this context.

Eight external enrichment sources were also added (weather, holiday flags, local event density, venue history), but SHAP analysis showed that lifecycle interactions accounted for **nearly half of total feature importance**. The external signals helped at the margins; the lifecycle architecture was the main driver.

The prediction window was expanded from 7 to 21 days, and the test set was restricted to the final 3 weeks before each event, where pricing decisions are most actionable. This produced the final result: **13.37 RMSE on 389,230 test observations**.

[Read the full post](/seatdata.io-improving-predictions/)

### Part 12: Segmentation Revisited

With the feature set now doubled from Part 11, I re-ran the Part 8 experiment: do category-specific models outperform the unified model? The answer was the same. The unified model won or tied across all seven categories in cross-validation, even with the richer feature set.

The result was stronger than Part 8's. With more features, the segment models had more room to overfit, and they did. Broadway segment models showed particular instability, with RMSE swinging by 30% between time folds. The unified model's ability to share patterns across categories remained its advantage.

[Read the full post](/seatdata.io-segmenting-2/)

### Part 13: Business Impact

The first 12 parts built the model. Part 13 quantifies what acting on it is worth. Two revenue mechanisms have the clearest path: dynamic primary pricing based on secondary velocity (the unpopular choice), and strategic inventory release timed to demand curves.

The scenario analysis, grounded in published research from MLB variable pricing (3% revenue lift), Live Nation Platinum (70% premium seat revenue increase), and airline ML pricing ($72.2M revenue increase), produces a conservative estimate of **$1.05M per year** for a 500-event operator and **$42M at Live Nation scale**. The Super Bowl LX case study shows the signal in action: secondary velocity surged 8x from D-21 to D-7, with the classifier holding above 0.93 throughout.

[![Scenario analysis: $1.05M conservative, $3.38M moderate, $8.08M optimistic for a 500-event operator](/portfolio/image-6.png)](/portfolio/image-6.png)*Dynamic pricing revenue uplift for a 500-event, 10K-capacity operator across three scenarios*

[Read the full post](/seatdata.io-business-impact/)

---

## Where the Model Works Best

The model's error varies substantially by event type. These are Part 11 champion model results on the 3-week test window.

| Category | RMSE (tickets) |
|----------|---------------|
| Broadway & Theater | 6.46 |
| Comedy | 7.08 |
| Festivals | 7.58 |
| Concerts | 7.99 |
| Minor/Other Sports | 10.74 |
| Other | 18.15 |
| Major Sports | 31.69 |

Broadway is now the **most predictable category** (it was second to Comedy in Part 7). The lifecycle interaction features particularly helped here: Broadway shows have long, stable sales curves that the model can read clearly.

Major Sports improved dramatically, from **48.44 RMSE in Part 7 to 31.69 in Part 11**. The external enrichment features (local event density, day-of-week interactions, venue history) captured some of the game-context signal that was missing earlier. But it remains the hardest category. Without matchup-level data (opponent quality, standings, broadcast schedule), the model still cannot distinguish a regular-season Tuesday game from a must-win playoff game.

For primary pricing teams: Broadway, Comedy, and Concerts are reliable enough for automated signals. Major Sports needs human review and would benefit most from additional data enrichment.

---

## Key Lessons

**1. Data preparation mattered more than algorithm selection.** Log-transforming the sales target and imputing missing venue sizes improved every model tested. The choice between XGBoost, LightGBM, and CatBoost had smaller effects than getting the inputs right.

**2. The biggest gains were architectural, not algorithmic.** The two-stage pipeline (Part 4) cut error by 40%. Lifecycle interaction features (Part 11) drove the next major improvement. Hyperparameter tuning, by contrast, contributed **less than 1%** per round. Framing the problem correctly was worth more than optimizing within a fixed frame.

**3. Lifecycle interactions dominated feature importance.** The same market signal means different things at different points in an event's sales cycle. Once the model could read "days to event" in combination with price and listing levels, nearly half of total feature importance concentrated in these interaction terms. This was the single most impactful feature engineering decision in the project.

**4. One model on all data beats segment-specific models, even with rich features.** This was tested twice: once with the base feature set (Part 8) and again after doubling the feature count (Part 12). Both times, the unified model generalized better. With more features, the segment models had more room to overfit, and they did.

**5. Static identity signals hurt; time-varying momentum helps.** Semantic embeddings from Wikipedia text did not improve predictions (Part 9). Static social media metrics added noise (Part 10). But time-varying market features, velocity trends, price momentum, listing dynamics, consistently helped. For this domain, **what an event is doing right now matters more than what it is**.

---

## What Would Come Next

The forecasting system works. The [business impact analysis](/seatdata.io-business-impact/) quantifies the revenue case. The path from here is toward deployment.

Matchup-level data for sports (opponent quality, standings, broadcast schedule) would address the largest remaining accuracy gap. A real-time ingestion pipeline replacing daily CSV snapshots with streaming StubHub data would enable intraday pricing decisions. A dynamic pricing engine consuming the velocity forecasts would translate signal into action. And A/B validation with a venue or promoter partner would close the loop between predicted impact and measured revenue.

---

Try the live prediction interface at [event-explorer.streamlit.app](https://event-explorer.streamlit.app).
