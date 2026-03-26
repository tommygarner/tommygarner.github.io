---
layout: single
title: "UT Project: Ecommerce Analytics"
date: 2026-03-25
description: "A six-phase analytics framework exploring how ecommerce businesses can use data to make better decisions about pricing, inventory, and customer retention"
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
excerpt: "Most ecommerce companies make pricing and inventory decisions based on intuition. This project builds a connected analytics framework across six phases to show what those decisions look like when grounded in data."
published: true
---

## TL;DR

- **Goal:** Explore ecommerce analytics end-to-end, from pricing strategy to customer retention to inventory planning
- **Data:** Synthetic apparel store — 15 SKUs, 800 customers, ~10,000 order line items, 7 discount campaigns with known depth
- **Methods:** Price elasticity (log-log OLS), revenue optimization (SciPy), time-series forecasting (Prophet), survival analysis (Kaplan-Meier, Cox PH), safety stock modeling
- **Key finding:** Elasticity varies sharply by category. Hats (-1.77) and Accessories (-1.72) benefit from discounts; Jackets (-0.76) and Bags (-0.40) do not. Treating them the same leaves revenue on the table either way.

---

## Why This Project

Ecommerce is a domain where intuition often substitutes for analysis. Merchants mark things down because it feels like it drives sales. They reorder when shelves look empty. They offer the same discount to every customer segment.

The goal of this project was to work through each of those decisions analytically — not to prescribe a single strategy, but to understand the mechanics well enough to know when the intuition holds and when it doesn't. Each of the six phases approaches a different part of the business.

---

## The Data

The dataset simulates a direct-to-consumer apparel store: t-shirts, hoodies, hats, jackets, sweatpants, and totes across multiple size and color variants. Each product has a known price elasticity baked into how demand responds to price changes — this is what makes the synthetic approach useful here. You can check whether the models recover the right answer.

Seven promotional campaigns are embedded in the data with known discount depths, ranging from a 10% New Year sale to a 30% Black Friday event. These are treated as controlled experiments for the elasticity and forecasting models.

![Monthly revenue trend with promotional periods highlighted](/images/shopify-revenue-trend.png)
*Orange bands mark active discount campaigns. Revenue spikes align with the two deepest promotions (BFCM at 30%, Holiday at 25%).*

Total revenue across the dataset: **$582K** across ~10,000 line items. Discount penetration sits at **18.1%** of orders.

---

## Phase 2: Price Elasticity

The central question in pricing is: if I raise (or lower) my price by 1%, how much does my sales volume change? The ratio of those two percentages is the price elasticity of demand.

A simple calculation won't get you there. Prices and discounts move together with seasonality, product lifecycle, and customer mix — all of which also affect demand. The solution is a log-log OLS regression that controls for time and isolates price as the causal variable.

**Model:** `ln(Units Sold) = α + ε · ln(Price) + β · time + error`

The coefficient ε is the elasticity estimate. A value of -1.5 means a 10% price increase reduces volume by 15%.

![Price elasticity by product category](/images/shopify-elasticity-by-category.png)
*Red bars are elastic categories (|ε| > 1): discounts pay for themselves in volume. Blue bars are inelastic: volume barely moves with price, so discounts just give away margin.*

The range is wide. **Hats (-1.77) and Accessories (-1.72)** are highly elastic — a discount generates enough incremental volume to grow total revenue. **Jackets (-0.76) and Bags (-0.40)** are inelastic — customers who want them will buy regardless of a 15% discount, and customers who don't want them won't be moved. Discounting inelastic categories is just margin erosion.

The practical implication: a flat 20%-off sitewide sale is a bad deal. It overpays for volume in categories that don't need it.

---

## Phase 3: Revenue Optimization

With elasticity estimates in hand, the optimization question is: what price maximizes total revenue for each category?

This is a one-dimensional optimization problem per category. Given the elasticity and current average price, find the price where the marginal revenue from an additional unit equals zero. SciPy's `minimize_scalar` handles it directly.

![Revenue uplift from optimal vs. current pricing by category](/images/shopify-revenue-uplift.png)
*Green annotations show projected revenue gain at the optimal price. Elastic categories show the largest upside because volume response is strong enough to more than offset price reductions.*

The projected aggregate uplift across the catalog is **32.9%**, driven mostly by Hats (+71%) and Accessories (+65%). These numbers are model-dependent — they assume elasticity estimates generalize — but the directional signal is clear: the biggest opportunity is in categories where price reductions are being withheld.

---

## Phase 4: Demand Forecasting

Pricing decisions made today affect demand next week and next quarter. A forecast model makes that connection explicit and gives a pricing calendar something to anchor to.

The model uses Prophet, Facebook's open-source time-series library, trained on weekly aggregated units sold. Promotional periods are passed as explicit binary regressors so the model learns that BFCM weeks look different from normal ones — rather than treating them as noise.

![Weekly demand forecast with 95% confidence interval](/images/shopify-forecast-plot.png)
*The red dashed line is the train/test split. Orange bands are active promo periods. The shaded region is the 95% confidence interval on the forecast.*

Holdout accuracy: **7.7% MAPE** (mean absolute percentage error) on a 12-week test set. A feature importance analysis run separately found that **total discount depth** was the single strongest predictor of weekly demand at 39.7% importance — more than price, seasonality, or any other variable. That's consistent with the elasticity findings: promotional activity is the primary lever driving volume.

---

## Phase 5: Customer Retention and LTV

Retention is where the long-run revenue math lives. A customer who churns after two purchases is worth a fraction of one who buys for two years. The question is which customers are at risk and when.

Survival analysis treats customer retention the same way actuarial science treats mortality: each customer has a "survival time" (how long until they stop buying), and the goal is to model that distribution. Kaplan-Meier curves describe median survival by segment. Cox Proportional Hazards regression identifies which variables predict churn.

![Kaplan-Meier survival curves by membership tier](/images/shopify-survival-curves.png)
*The y-axis is retention rate. The dotted horizontal line marks 50% retention — where it crosses each curve is that tier's median survival. Premium members (blue) retain significantly longer than Basic (green).*

![LTV and churn rate by membership tier](/images/shopify-ltv-by-tier.png)
*Left: average lifetime value split between subscription revenue and merchandise spend. Right: churn rate by tier. Premium members churn at roughly half the rate of Basic members and generate 3x the LTV.*

The Cox model identified **merchandise purchase frequency in the first 30 days** as the strongest predictor of long-term retention. A member who buys three times in the first month is dramatically less likely to churn than one who buys once and goes quiet. This creates a concrete intervention window: the first 30 days after signup are when retention campaigns have the most leverage.

LTV by tier: **$1,247 for Premium, $731 for active Standard, $382 for Basic.**

---

## Phase 6: Inventory Planning

Demand forecasts only matter if inventory is there to fulfill them. The final phase translates the weekly forecast into safety stock and reorder recommendations for each SKU.

Safety stock is a buffer against two sources of uncertainty: demand variability (will we sell more or less than expected?) and lead time variability (will the supplier deliver on schedule?). The model computes both, combines them into a reorder point, and flags which SKUs are at risk of stocking out before the next order arrives.

Across the catalog, **319 SKU-location combinations** were flagged as stockout risks. Lead time variability turned out to be the larger driver — demand uncertainty was more predictable than supplier schedule uncertainty. This is a common pattern in practice and suggests that vendor reliability is often a higher-leverage investment than forecast accuracy.

---

## What the Project Covers

Each phase of this project corresponds to a real decision a DTC operator makes:

| Phase | Decision | Method |
|---|---|---|
| EDA | What's actually driving revenue? | Descriptive analytics |
| Elasticity | Which products are price-sensitive? | Log-log OLS regression |
| Optimization | What should prices be? | SciPy numerical optimization |
| Forecasting | What will demand look like? | Prophet + ML ensembles |
| Churn | Which customers are at risk? | Kaplan-Meier, Cox PH |
| Inventory | How much stock do we need? | Safety stock modeling |

The goal wasn't to build a production system — it was to understand how these decisions connect. Pricing affects demand, which affects inventory, which affects fulfillment, which affects retention. Treating any one of them in isolation misses the feedback loops that determine whether the business grows.
