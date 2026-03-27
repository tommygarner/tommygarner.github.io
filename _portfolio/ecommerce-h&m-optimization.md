---
layout: single
title: "UT Project: Ecommerce Analytics"
date: 2026-03-25
description: "Seven decisions every ecommerce operator makes, and what the data says about each one. From price elasticity to supply chain routing."
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

<div style="border: 1px solid #E5E7EB; border-radius: 12px; overflow: hidden; margin: 0 0 32px;">
<iframe src="/pipeline-demo.html" width="100%" height="920" frameborder="0" scrolling="yes" style="display: block;"></iframe>
</div>

## TL;DR

- **Goal:** Seven decisions every ecommerce operator makes, analyzed end-to-end from pricing strategy to supply chain routing
- **Data:** Synthetic apparel store: 15 SKUs, 800 customers, ~10,000 order line items, 7 discount campaigns with known depth
- **Methods:** Price elasticity (log-log OLS), revenue optimization (SciPy), time-series forecasting (Prophet), survival analysis (Kaplan-Meier, Cox PH), safety stock modeling, Gurobi MIP (transportation LP, TSP, newsvendor, zone skipping)
- **Key finding:** Only Tote Bags clear the elastic threshold. A discount there generates enough volume to grow revenue. For everything else, discounts reduce revenue per unit without enough volume recovery to compensate.

---

Most ecommerce companies run a 20%-off sitewide sale and call it a strategy. This project asks what happens when you replace that with data.

The answer is different for every product category. That gap is where the revenue is hiding.

Six more decisions follow the same pattern. The intuitive approach has a cost that only becomes visible when you measure it. Reordering when shelves look empty isn't inventory management. Offering the same promotion to every customer segment isn't retention strategy. Getting the math right on any one of these is useful. Understanding how they connect is where it gets interesting: pricing affects demand, demand drives the forecast, the forecast sizes safety stock, inventory positions constrain the distribution network, and fulfillment determines whether customers come back.

---

## The Data

The dataset simulates a direct-to-consumer apparel store: t-shirts, hoodies, hats, jackets, sweatpants, and totes across multiple size and color variants. Each product has a known price elasticity baked into how demand responds to price changes, which is what makes the synthetic approach valuable. You can verify whether the models recover the right answer.

Seven promotional campaigns are embedded in the data with known discount depths, ranging from a 10% New Year sale to a 30% Black Friday event. These function as controlled experiments for the elasticity and forecasting models.

![Monthly revenue trend with promotional periods highlighted](/images/shopify-revenue-trend.png)
*Revenue spikes align with the two deepest promos: BFCM (30%) and Holiday (25%).*

Total revenue: **$582K** across ~10,000 line items. Discount penetration: **18.1%** of orders.

---

## A discount generates revenue for tote bags. For everything else, it just gives away margin.

The problem with a flat discount is that it treats elastic and inelastic categories the same. For a price-elastic product, a 15% cut generates enough incremental volume to grow total revenue. For an inelastic one, volume barely moves and you've simply lowered your margin.

Separating these effects requires isolating price from everything else that moves demand: seasonality, product lifecycle, promotional timing. A log-log OLS regression does this by modeling the relationship between log price and log units sold while controlling for time. The coefficient on price is the elasticity estimate, free of confounding.

**Model:** `ln(Units Sold) = α + ε · ln(Price) + β · time + error`

A coefficient of -1.5 means a 10% price increase reduces volume by 15%.

![Price elasticity by product category](/images/shopify-elasticity-by-category.png)
*Only Tote Bag crosses the unit-elastic threshold. All other categories are inelastic: volume barely responds to price.*

Only **Tote Bag (~-1.5)** is elastic: a discount generates enough incremental volume to grow total revenue. **Hats, Hoodies, and T-Shirts** are moderately inelastic (-0.65 to -0.75). **Jackets and Sweatpants** show near-zero price sensitivity, meaning demand barely responds to price at all. A 20%-off sitewide sale gives away margin on categories where price doesn't matter and underinvests where it does.

---

## So what should each price actually be?

Knowing the elasticity answers the directional question. The optimization question is more precise: at exactly what price does each category maximize revenue?

For a constant-elasticity demand curve this is a one-dimensional problem per category. SciPy's `minimize_scalar` finds the price where marginal revenue reaches zero, given the elasticity estimate and current average price.

![Revenue uplift from optimal vs. current pricing by category](/images/shopify-revenue-uplift.png)
*Projected revenue gain at the optimal price per category.*

The projected aggregate uplift at optimal prices is **32.9%**. These numbers are model-dependent and assume elasticity estimates generalize out of sample, but the direction is clear. The biggest gains come from categories where current prices are furthest from the revenue-maximizing point.

---

## Promotional activity predicts demand better than price or seasonality

Pricing decisions don't operate in isolation. They shift when demand will spike and by how much. A forecast that ignores promotions systematically underestimates demand during sale periods and overestimates it afterward.

Prophet handles this by accepting promotional periods as explicit binary regressors rather than treating them as noise in the residuals. Trained on weekly aggregated units sold, the model learns that BFCM weeks follow a different pattern than ordinary ones.

![Weekly demand forecast with 95% confidence interval](/images/shopify-forecast-plot.png)
*Orange bands mark promo periods. Shaded region is the 95% confidence interval.*

Holdout accuracy: **7.7% MAPE** on a 12-week test set. A separate feature importance analysis found that total discount depth was the single strongest demand predictor at **39.7% importance**, ahead of price, seasonality, or trend. Promotional activity is the primary lever, not price level alone. That's consistent with the elasticity findings.

---

## The first 30 days determine who stays

Pricing drives who buys. Retention is about whether they buy again. A customer who churns after two purchases is worth a fraction of one who stays active for two years. The difference in lifetime value between membership tiers is large enough that where you direct retention investment matters.

Survival analysis treats customer retention the way actuarial models treat mortality: each customer has a survival time (how long until they stop buying). The goal is to model that distribution. Kaplan-Meier curves estimate median retention by tier. Cox Proportional Hazards regression identifies which variables shift the hazard of churning.

![Kaplan-Meier survival curves by membership tier](/images/shopify-survival-curves.png)
*Premium members retain significantly longer. The dotted line marks 50% retention.*

![LTV and churn rate by membership tier](/images/shopify-ltv-by-tier.png)
*Merchandise spend and churn rate by membership tier. Premium members churn at roughly half the rate of Basic.*

The Cox model identified **merchandise purchase frequency in the first 30 days** as the strongest churn predictor. A member who buys three times in the first month is dramatically less likely to churn than one who buys once and goes quiet. This creates a specific window: the first 30 days after signup are when retention campaigns have the most leverage, before disengagement becomes a pattern.

LTV by tier: **$1,247 for Premium, $731 for active Standard, $382 for Basic.**

---

## The stockout problem is mostly a vendor problem

Demand forecasts only matter if inventory is in place to fulfill them. Safety stock is the buffer sized to absorb two sources of uncertainty: demand variability (will we sell more or less than expected?) and lead time variability (will the supplier deliver on schedule?). The model computes both, combines them into a reorder point, and flags which SKUs are at risk of stocking out before the next order arrives.

Across the catalog, **319 SKU-location combinations** were flagged as stockout risks. The more interesting finding: lead time variability was the larger driver, not demand uncertainty. Demand was more predictable than supplier delivery schedules. In practice, that means vendor reliability improvements often reduce stockout exposure faster than tightening the demand forecast, which is the less obvious place to invest.

---

## Five ways to optimize a distribution network

Knowing how much to stock leaves the question of how to move it. Five connected optimization problems, each with a different mathematical structure.

**Which DC serves which region?** The transportation LP minimizes total shipping cost weighted by distance and product weight, subject to DC capacity constraints. The LP ensures no DC gets overloaded, which a simple nearest-DC rule can't guarantee.

![Transportation LP: states assigned per DC](/images/shopify-transportation-lp.png)
*States assigned to each DC under the optimal LP assignment.*

**What order should deliveries happen in?** Once each DC's territory is fixed, the TSP finds the minimum-distance delivery route. The Miller-Tucker-Zemlin formulation eliminates subtours: routes that visit disconnected clusters rather than covering a contiguous region before returning to the depot.

![Optimal TSP routes per DC](/images/shopify-tsp-routes.png)
*Optimal delivery routes per DC. Stars are DC depots; dots are demand region centroids.*

**How much should each DC order given uncertain demand?** The stochastic newsvendor generates 200 demand scenarios per SKU and finds the order quantity that maximizes expected profit across all of them. Ordering too little pays a shortage penalty; ordering too much pays holding cost. The optimal quantity shifts the balance between those two risks.

**Can the business promise 3-day delivery to every customer?** A chance-constrained MIP simulates 1,000 delivery scenarios per region and computes T95, the delivery time guaranteed for 95% of orders. A second optimization reassigns DCs to minimize worst-case T95 across all states. The tradeoff is explicit: the min-cost LP assignment leaves distant states above the SLA; the min-max assignment compresses worst-case delivery at a shipping cost premium.

![Delivery guarantee: shipping vs. goodwill cost by policy](/images/shopify-delivery-guarantee.png)
*Shipping vs. goodwill cost under each delivery policy.*

**Where does air freight pay?** For regions beyond ground reach within the delivery window, zone skipping ships bulk freight by air to a regional carrier hub, then uses regional last-mile from there. A binary MIP decides which regions zone-skip, constrained by hub throughput. The solver rations zone-skip slots across competing regions based on where they produce the greatest combined savings in shipping cost and delivery goodwill.

Ground distance uses Manhattan geometry rather than straight-line to avoid routing over water. A coastal state like Florida has a longer effective ground distance than its crow-flies position suggests.

![Zone skipping vs. ground transit time by region](/images/shopify-zone-skip.png)
*Ground vs. zone-skip transit days per region. Navy dots took ground; purple dots zone-skipped.*

---

These seven phases don't exist independently. Pricing affects demand, which drives the forecast. The forecast sizes safety stock. Inventory positions constrain the transportation LP. The LP assignment determines whether the delivery SLA is achievable without air freight. Treating ecommerce operations as a linked system rather than a set of separate decisions is what the project is actually about.

