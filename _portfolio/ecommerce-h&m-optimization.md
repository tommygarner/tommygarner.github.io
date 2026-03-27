---
layout: single
title: "UT Project: Ecommerce Analytics"
date: 2026-03-25
description: "Seven decisions every ecommerce operator makes — and what the data says about each one. From price elasticity to supply chain routing."
author_profile: true
toc: true
toc_sticky: true
classes: wide
tags:
  - ecommerce
  - price elasticity
  - demand forecasting
  - revenue optimization
  - customer analytics
  - inventory planning
  - supply chain
  - operations research
excerpt: "Most ecommerce companies run a 20%-off sitewide sale and call it a strategy. This project asks what happens when you replace that with data."
published: true
---

## TL;DR

- **Goal:** Seven decisions every ecommerce operator makes — analyzed end-to-end, from pricing strategy to supply chain routing
- **Data:** Synthetic apparel store — 15 SKUs, 800 customers, ~10,000 order line items, 7 discount campaigns with known depth
- **Methods:** Price elasticity (log-log OLS), revenue optimization (SciPy), time-series forecasting (Prophet), survival analysis (Kaplan-Meier, Cox PH), safety stock modeling, Gurobi MIP (transportation LP, TSP, newsvendor, zone skipping)
- **Key finding:** A flat 20%-off sitewide sale is simultaneously too generous and not generous enough. Hats (-1.77 elasticity) leave revenue on the table at full price. Jackets (-0.76) are just giving away margin.

---

Most ecommerce companies run a 20%-off sitewide sale and call it a strategy. This project asks what happens when you replace that with data.

The answer is different for every product category — and that gap is where the revenue is hiding.

Six more decisions follow the same pattern. The intuitive approach has a cost that only becomes visible when you measure it. Reordering when shelves look empty isn't inventory management. Offering the same promotion to every customer segment isn't retention strategy. Getting the math right on any one of these is useful. Understanding how they connect is where it gets interesting: pricing affects demand, demand drives the forecast, the forecast sizes safety stock, inventory positions constrain the distribution network, and fulfillment determines whether customers come back.

---

## The Data

The dataset simulates a direct-to-consumer apparel store: t-shirts, hoodies, hats, jackets, sweatpants, and totes across multiple size and color variants. Each product has a known price elasticity baked into how demand responds to price changes — which is what makes the synthetic approach valuable. You can verify whether the models recover the right answer.

Seven promotional campaigns are embedded in the data with known discount depths, ranging from a 10% New Year sale to a 30% Black Friday event. These function as controlled experiments for the elasticity and forecasting models.

![Monthly revenue trend with promotional periods highlighted](/images/shopify-revenue-trend.png)
*Orange bands mark active discount campaigns. Revenue spikes align with the two deepest promotions (BFCM at 30%, Holiday at 25%).*

Total revenue: **$582K** across ~10,000 line items. Discount penetration: **18.1%** of orders.

---

## A 20% discount works for hats. It costs money on jackets.

The problem with a flat discount is that it treats elastic and inelastic categories the same. A hat buyer responds to a 15% price cut by buying more — enough more to grow total revenue. A jacket buyer will buy the jacket regardless. A customer who wouldn't buy it at full price won't buy it at a discount either.

Separating these effects requires isolating price from everything else that moves demand: seasonality, product lifecycle, promotional timing. A log-log OLS regression does this by modeling the relationship between log price and log units sold while controlling for time. The coefficient on price is the elasticity estimate, free of confounding.

**Model:** `ln(Units Sold) = α + ε · ln(Price) + β · time + error`

A coefficient of -1.5 means a 10% price increase reduces volume by 15%.

![Price elasticity by product category](/images/shopify-elasticity-by-category.png)
*Red bars are elastic categories (|ε| > 1): discounts pay for themselves in volume. Blue bars are inelastic: volume barely moves with price, so discounts just give away margin.*

The range is wide. **Hats (-1.77) and Accessories (-1.72)** are highly elastic — a discount generates enough incremental volume to grow total revenue. **Jackets (-0.76) and Bags (-0.40)** are inelastic — customers who want them buy regardless of the price, and customers who don't want them won't be moved. The 20%-off sitewide sale overinvests in categories where price barely matters and underinvests in the ones where it moves the needle most.

---

## So what should each price actually be?

Knowing the elasticity answers the directional question. The optimization question is more precise: at exactly what price does each category maximize revenue?

For a constant-elasticity demand curve this is a one-dimensional problem per category. SciPy's `minimize_scalar` finds the price where marginal revenue reaches zero, given the elasticity estimate and current average price.

![Revenue uplift from optimal vs. current pricing by category](/images/shopify-revenue-uplift.png)
*Green annotations show projected revenue gain at the optimal price. Elastic categories show the largest upside because volume response is strong enough to more than offset the price reduction.*

The projected aggregate uplift at optimal prices is **32.9%**, driven mostly by Hats (+71%) and Accessories (+65%). These numbers are model-dependent — they assume elasticity estimates generalize out of sample — but the directional signal is clear. The biggest opportunity is in the categories where price cuts are being withheld because a flat pricing strategy doesn't distinguish between them.

---

## Promotional activity predicts demand better than price or seasonality

Pricing decisions don't operate in isolation — they shift when demand will spike and by how much. A forecast that ignores promotions systematically underestimates demand during sale periods and overestimates it afterward.

Prophet handles this by accepting promotional periods as explicit binary regressors rather than treating them as noise in the residuals. Trained on weekly aggregated units sold, the model learns that BFCM weeks follow a different pattern than ordinary ones.

![Weekly demand forecast with 95% confidence interval](/images/shopify-forecast-plot.png)
*The red dashed line is the train/test split. Orange bands are active promo periods. The shaded region is the 95% confidence interval on the forecast.*

Holdout accuracy: **7.7% MAPE** on a 12-week test set. A separate feature importance analysis found that total discount depth was the single strongest demand predictor at **39.7% importance** — ahead of price, seasonality, or trend. Promotional activity is the primary lever, not price level alone. That's consistent with the elasticity findings.

---

## The first 30 days determine who stays

Pricing drives who buys. Retention is about whether they buy again. A customer who churns after two purchases is worth a fraction of one who stays active for two years — and the difference in lifetime value between membership tiers is large enough that where you direct retention investment matters.

Survival analysis treats customer retention the way actuarial models treat mortality: each customer has a survival time (how long until they stop buying), and the goal is to model that distribution. Kaplan-Meier curves estimate median retention by tier. Cox Proportional Hazards regression identifies which variables shift the hazard of churning.

![Kaplan-Meier survival curves by membership tier](/images/shopify-survival-curves.png)
*The y-axis is retention rate. The dotted line marks 50% retention — where it crosses each curve is that tier's median survival. Premium members (blue) retain significantly longer than Basic (green).*

![LTV and churn rate by membership tier](/images/shopify-ltv-by-tier.png)
*Left: average lifetime value split between subscription revenue and merchandise spend. Right: churn rate by tier. Premium members churn at roughly half the rate of Basic and generate 3x the LTV.*

The Cox model identified **merchandise purchase frequency in the first 30 days** as the strongest churn predictor. A member who buys three times in the first month is dramatically less likely to churn than one who buys once and goes quiet. This creates a specific window: the first 30 days after signup are when retention campaigns have the most leverage, before disengagement becomes a pattern.

LTV by tier: **$1,247 for Premium, $731 for active Standard, $382 for Basic.**

---

## The stockout problem is mostly a vendor problem

Demand forecasts only matter if inventory is in place to fulfill them. Safety stock is the buffer sized to absorb two sources of uncertainty: demand variability (will we sell more or less than expected?) and lead time variability (will the supplier deliver on schedule?). The model computes both, combines them into a reorder point, and flags which SKUs are at risk of stocking out before the next order arrives.

Across the catalog, **319 SKU-location combinations** were flagged as stockout risks. The more interesting finding: lead time variability was the larger driver, not demand uncertainty. Demand was more predictable than supplier delivery schedules. In practice, that means vendor reliability improvements often reduce stockout exposure faster than tightening the demand forecast — which is the less obvious place to invest.

---

## Five ways to optimize a distribution network

Knowing how much to stock leaves the question of how to move it. Five connected optimization problems, each with a different mathematical structure.

**Which DC serves which region?** The transportation LP minimizes total shipping cost weighted by distance and product weight, subject to DC capacity constraints from the inventory phase. The optimal assignment beats a nearest-DC heuristic because it avoids overloading a geographically close DC that happens to be capacity-constrained.

![Transportation LP results: optimal vs. nearest-DC cost and states per DC](/images/shopify-transportation-lp.png)
*Left: weekly shipping cost under the LP vs. the naive nearest-DC rule. Right: how many states each DC serves under the optimal assignment.*

**What order should deliveries happen in?** Once each DC's territory is fixed, the TSP finds the minimum-distance delivery route. The Miller-Tucker-Zemlin formulation eliminates subtours — routes that visit disconnected clusters rather than covering a contiguous region before returning to the depot.

![Optimal TSP routes per DC](/images/shopify-tsp-routes.png)
*One optimal route per DC. Stars are DC depots; dots are demand region centroids. Arrows show travel direction.*

**How much should each DC order given uncertain demand?** The stochastic newsvendor generates 200 demand scenarios per SKU and finds the order quantity that maximizes expected profit across all of them. Ordering too little pays a shortage penalty (lost margin plus goodwill cost); ordering too much pays holding cost. The optimal quantity shifts the balance between those two risks.

![Newsvendor optimal vs. Phase 6 recommended quantities](/images/shopify-newsvendor.png)
*Left: scatter of optimal order quantity vs. deterministic recommendation. Points above the diagonal mean the stochastic model says order more. Right: percentage adjustment by DC and product type.*

**Can the business promise 3-day delivery to every customer?** A chance-constrained MIP simulates 1,000 delivery scenarios per region and computes T95 — the delivery time guaranteed for 95% of orders. A second optimization reassigns DCs to minimize worst-case T95 across all states. The tradeoff is explicit: the min-cost LP assignment leaves distant states above the SLA; the min-max assignment compresses worst-case delivery at a shipping cost premium.

![Delivery guarantee results: T95 distribution and cost tradeoff](/images/shopify-delivery-guarantee.png)
*Left: distribution of T95 under each policy. Middle: shipping vs. goodwill cost by policy. Right: per-region T95 sorted by current value.*

**Where does air freight pay?** For regions beyond ground reach within the delivery window, zone skipping ships bulk freight by air to a regional carrier hub, then uses regional last-mile from there. A binary MIP decides which regions zone-skip, constrained by hub throughput. The solver rations zone-skip slots across competing regions based on where they produce the greatest combined savings in shipping cost and delivery goodwill.

Ground distance uses Manhattan geometry rather than straight-line to avoid routing over water — a coastal state like Florida has a longer effective ground distance than its crow-flies position suggests.

![Zone skipping results: cost by policy, transit comparison, hub utilization](/images/shopify-zone-skip.png)
*Left: total weekly cost (shipping + goodwill) under all-ground, unconstrained zone-skip, and the MIP solution. Middle: transit days by region, colored by the MIP's mode choice. Right: throughput at each regional hub.*

---

## What the project covers

These seven phases don't exist independently. Pricing affects demand, which drives the forecast. The forecast sizes safety stock. Inventory positions constrain the transportation LP. The LP assignment determines whether the delivery SLA is achievable without air freight. That connection — treating ecommerce operations as a linked system rather than a set of separate decisions — is what the project is actually about.

| Phase | Decision | Method |
|---|---|---|
| EDA | What's driving revenue? | Descriptive analytics |
| Elasticity | Which products are price-sensitive? | Log-log OLS regression |
| Optimization | What should each price be? | SciPy numerical optimization |
| Forecasting | What will demand look like? | Prophet time-series |
| Churn | Which customers are at risk? | Kaplan-Meier, Cox PH |
| Inventory | How much stock do we need? | Safety stock modeling |
| Supply chain | How do we move it efficiently? | Gurobi LP, MIP, stochastic MIP |
