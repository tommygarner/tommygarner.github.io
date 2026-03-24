---
layout: single
title: "Demand Forecasting: Secondary Ticket Sales"
date: 2026-03-10
description: "How secondary ticket market velocity signals can inform dynamic primary pricing, and what a 13-part ML project revealed about demand in live events"
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
.streamlit-container { border: 1px solid #ddd; border-radius: 4px; overflow: hidden; margin-bottom: 2rem; }
.dashboard-loading { text-align: center; padding: 20px; color: #666; }
</style>

<div class="streamlit-container">
  <div class="dashboard-loading">Loading interactive dashboard...</div>
  <iframe src="https://event-explorer.streamlit.app/?embed=true"
          height="800"
          style="width:100%;border:none;">
  </iframe>
</div>

## TL;DR

- **Goal:** Forecast 7-day secondary ticket sales velocity to inform primary pricing decisions
- **Data:** 132 days of daily StubHub snapshots, 7.5M rows, 138,000 events, 14,600 venues
- **Model:** Two-stage XGBoost classifier + MLP regressor; RMSE 13.37 tickets on the final 3-week window
- **Key finding:** Lifecycle interaction features drove more accuracy improvement than all algorithm and hyperparameter changes combined

---

## Better Information Needed

Making the best pricing decisions comes from knowing your demand.

Primary ticket pricing teams at promoters and venues suggest prices weeks or months before tickets go on sale. The best information they typically have is a comparable show from a prior season. A similar artist, a similar venue, a similar time of year. It's an educated guess at the end of the day.

These guesses are rarely far off from optimal, but a correction sometimes happens in the resale market. If an event isn't selling, it seems like a natural response to drop the price. But if those discounted tickets move quickly soon after, that speed could be evidence that demand was there all along. The primary seller just undervalued the ticket, and the margin went to resellers who bought at face value and flipped at what the market would actually spend. If the seller holds the price instead and inventory stalls, they missed the window altogether.

The secondary market doesn't work this way. Platforms like StubHub reflect the willingness to pay of buyers, updated daily. Listing prices adjust based on real purchase activity. Floor prices hold when demand is strong and fall with slowed demand. This is like a demand discovery in real time, but can the information flow back to the primary market?

This project builds that bridge. Using 4 months of daily StubHub snapshots covering 138,000 events across 14,600 venues, it forecasts 7-day secondary sales velocity as this proxy for underlying demand. A primary pricing team using it can ask a concrete question: is an event gaining momentum or losing it, and should we act before the window closes?

---

## Investigating the Data

Before building any model, I needed to confirm that secondary market data actually contained usable signal for demand.

### Searching for Signal 

Secondary sellers reprice constantly based on real buyer activity. Across all event types, floor prices drop roughly 10% in the final week before showtime. This isn't random, but it reflects how sellers are responding to weakening demand before any official action happens on the primary side.

[![Chart showing floor price declining as days to event approach zero](https://github.com/user-attachments/assets/bd32f380-278b-4d95-a28d-e5e5c4c25e6d)](https://github.com/user-attachments/assets/bd32f380-278b-4d95-a28d-e5e5c4c25e6d)*Floor price falls predictably as the event date approaches*

This is the demand signal that primary pricing teams would love to have. A stable secondary floor two weeks out hints that the original price is holding, while a falling floor might mean that demand is weak. A pricing team could then respond before inventory goes unsold and the event passes.

### Sales Happen Quick

That signal gets louder as the event draws near. Sales activity picks up quickly in the last week, roughly 15x the daily volume seen 2 months out from the event. This is the window where a forecast is most valuable. Demand is growing but the time for price adjustments is running out.

[![Market-wide average daily sales accelerating as events approach](/portfolio/image.png)](/portfolio/image.png)*Sales velocity increases roughly 15x from 60+ days out to day-of*

So the closer you get to an event, the more information you know about its demand, but the less time you have to do anything about it. A useful forecast has to find the signal early enough for the decision to still matter.

### Some Things are Hard to Predict 

On November 4th, Election Day, secondary sales dropped across every event category with meaningful inventory. Seasonal z-scores, which compare each day against the distribution for that same day of the week, confirmed the anomaly at -2.6 standard deviations below the expected value for a Tuesday.

[![Seasonal anomaly detection showing actual vs expected daily sales](/portfolio/image-1.png)](/portfolio/image-1.png)*Election Day produced the largest anomaly in the dataset*

No market signal predicted this. Elections, major news events, unexpected cancellations all hit demand with information a model likely doesn't account for. A production deployment would consider override triggers for days where context clearly breaks a normal pattern.

[Read the full EDA post](/seatdata.io-eda/)

---

## Reading the Signal

The floor price trends and sales acceleration from my EDA confirmed that the signal is there. Next, I needed to find if a model could read it reliably across 138K different events without manual intervention.

### Building the Dataset

The demand signals shown above, floor prices, sales velocity, and listing counts came from raw daily StubHub CSV snapshots with no structure connecting one day to the next. Before a model could read anything, I had to organize these files and create the dataset.

Four months of daily files were loaded into BigQuery and organized into a star schema linking events, venues, and daily market readings. A regex classification system labeled the 138,000 events into 38 categories without manual tagging. Those 38 were then consolidated into 7 modeling buckets: Broadway and Theater, Comedy, Concert, Festivals, Major Sports, Minor Sports, and Other.

[![Entity relationship diagram showing the BigQuery star schema](https://github.com/user-attachments/assets/f8e86cd8-4023-48e2-9ee1-2cea7c3d71fd)](https://github.com/user-attachments/assets/f8e86cd8-4023-48e2-9ee1-2cea7c3d71fd)*The database schema connecting events, venues, and daily snapshots*

[Read the database engineering post](/seatdata-io-database-engineering/)

### Two-Stage Design

With the dataset structured, EDA also revealed how sparse my distribution of sales was. 72% of daily snapshots had zero sales. A standard regression model trained on this distribution would just memorize to predict zero, and fail on the events where the signal actually matters.

The solution was to split the problem into two. A classifier first decided whether any sales will happen for a given event. A regressor then estimates how many tickets will sell, but only for the events that the classifier flags.

This split alone cut prediction error by 40% compared to a single-stage regression. The gain came entirely from this decision to split up the problem as opposed to jumping into feature engineering or tuning.

[Read the modeling post](/seatdata.io-modeling-1/)

### Timing Changes Everything

The two-stage model worked, but it still treated every market signal the same regardless of timing. EDA had already shown that sales accelerate in the final weeks of an event. So I wanted the model to learn this too, and the earlier, the better.

To be able to read timing alongside price, I added interaction features that combined days-to-event with market state variables for plenty of context. Once it could read this feature combination, modeling performance improved greatly.

> A $50 floor price at 30 days out is fine. But a $50 floor price 3 days away with inventory still on the digital shelf signals a strong residual demand!

Nearly half of total feature importance concentrated in these lifecycle interaction terms. The RMSE gain from this change was larger than any algorithm and hyperparameter work combined.

[![Top 20 features by combined classifier and regressor importance](/portfolio/feature_importance.png)](/portfolio/feature_importance.png)*Lifecycle interactions dominate the top 20 features; "Final 3W x Major Sports" alone outweighs any single market signal*

8 external sources were also tested including weather, holiday flags, local event density, and venue history. SHAP analysis confirmed that the lifecycle interactions drove the gains. The external signals seemed to help at the margins.

[Read the full Part 11 post](/seatdata.io-improving-predictions/)

### Diminishing Returns

3 experiments confirmed that the daily market snapshot was already data-rich. Wikipedia and Last.fm summary embeddings did not improve RMSE. Static social signals like Spotify listener counts and Reddit sentiment added noise because they didn't change meaningfully between daily snapshots. And training separate models per event category overfit on individual test windows, losing to a unified model both times.

Therefore, the daily market snapshot is already dense with information about the event. The wins in modeling accuracy were the features that helped the model read the data it already had, not new data added from outside sources.

---

## Model Results

The model is evaluated on the final 3-week window before each event, a period where pricing decisions are most actionable, across 389,230 daily snapshots in the test set. 

For Broadway, Comedy, Festivals and Concerts, predictions land within 6-8 tickets of actual sales. That's reliable enough to power automated alerts flagging events gaining (or losing) momentum, letting the pricing team focus on exceptions.

Minor Sports and Other events are noisier at 10-18 tickets RMSE, but still useful for directional signals. The model can still tell a pricing team whether demand is trending up or down, even if the exact number is rough.

Major Sports is the clear gap, at nearly 32 tickets RMSE. The reason ties back to what the model can and can't see. Secondary market signals capture price and volume. But for Major Sports, the demand drivers that matter most live outside of this data in the form of playoff standings, opponent quality, and maybe the broadcast schedule. The model also can't distinguish a regular season Tuesday from a must-win playoff clincher.

The residual analysis also shows a consistent pattern across all events: the model underestimates the highest-demand events. A pricing team should treat a strong positive prediction as a floor, then!

---

## What It's Worth

The opening question was whether secondary market signals can inform primary pricing. The model can read the signal. The business question is whether it reads early enough to matter.

### Earlier Detection

A pricing team watching StubHub and other secondary platforms starts to notice floor price sink around a week before the show. By then, most pricing decisions are already locked. The model sees this sooner. 

Running the classifier across all lifecycle stages, detection of active events holds above 91% from 6 weeks out, and above 97% inside two weeks. For the highest-demand events (100+ tickets per week), the classifier is pretty much perfect from 8 weeks out.

Detection rates by window:

This early read is the whole value prop. A pricing team that knows demand is strong at 4 weeks out can hold a price or move premium inventory up. Another team that seeks decaying demand 4 weeks out can run a targeted promotion before being forced into a fire sale. Both of those decisions are invisible when it comes to the week of show!

### Revenue Capture

This earlier detection translates to the problem introduced at the very start. When a primary seller underprices a ticket, the margin goes to resellers. A forecast that identifies strong demand before the window closes lets the primary side, such as the artist, capture some of that gap for their performance.

A conservative scenario for a single mid-tier venue (10K seater) running about 100 events per year lives below:

| Assumption | Value | Benchmark |
|---|---|---|
| Events with actionable signal | 50% (50 events) | Below measured classifier recall of 98.8% on high-demand events; accounts for human review |
| Premium inventory per event | 8% of capacity (800 seats) | Typical premium tier at mid-size venues |
| Capture rate | 15% | Conservative vs. Live Nation Platinum's reported 70%+ |
| Secondary price gap | $35 per ticket | Below the ~2x face value average in published research |

$$100 \times 0.50 \times 800 \times 0.15 \times \$35 = \$210{,}000 \text{ per year}$$

At Live Nation's scale of 20K annual events, the same math gives $42M, about 14% of Ticketmaster's reported 2024 operating profit.

These are scenario projections, not observed revenue, and I'm assuming dynamic pricing infrastructure is already in place. But, the mechanics are still logical: better demand information earlier means fewer tickets resold at a premium that the primary seller could've captured.

---

## What's Next

Three gaps remain. 

Major Sports accuracy lags because the model can't see what drives demand for those events in the form of opponent quality, standings, and playoff implications. Adding matchup-level data might address the largest segment gap.

The daily CSV snapshots that feed the model introduce a 24-hour delay. A real-time ingestion pipeline would let a pricing team act quickly instead of the following morning.

Lastly, the revenue projections above are still built on assumptions. A/B testing with a venue or promoter partner would connect the dots between predicted demand and actual pricing decisions.

Try the live prediction interface at [event-explorer.streamlit.app](https://event-explorer.streamlit.app).
