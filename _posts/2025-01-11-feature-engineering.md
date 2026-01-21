---
layout: single
title: "SeatData.io Part 4: Feature Engineering"
date: 2026-01-11
description: "Feature Engineering my SeatData.io Snapshots to Prepare for Modeling"
author_profile: true
toc: true
toc_sticky: true
tags:
  - feature engineering
  - log transformations
  - imputations
  - dummy coding
  - interaction terms
  - time-series train/test split
  - scaling
excerpt: "How I transformed raw ticketing snapshots into a training and testing set ready for modeling by addressing EDA findings, clipping outliers, and engineering interaction terms."
---

## Abstract

After building the data warehouse in Part 1, I moved to the modeling phase only to realize my raw data wasn't ready for algorithms. The secondary ticket market is noisy, zero-inflated, and riddled with outliers. This article details the **Gap Analysis** I conducted on my initial dataset and the resulting feature engineering pipeline I built. By implementing 99th-percentile clipping, cyclical time encoding, and a two-stage target strategy, I created a dataset capable of supporting high-fidelity demand forecasting.

## Key Contributions

-   **Gap Analysis Implementation**: Translating EDA findings into pipeline code
-   **Robust Outlier Clipping**: Handling extreme variance in ticket prices
-   **Two-Stage Target Engineering**: Solving for zero-inflated sales data
-   **Cyclical Feature Encoding**: Using Trigonometry for temporal features

---

## 1. The Strategy: Gap Analysis
Before writing a single line of code for the new pipeline, I had to audit my initial Exploratory Data Analysis (EDA). I found that standard scaling and linear assumptions would fail because of the specific nature of ticket data.

I created a **Gap Analysis** table to guide my engineering script. This ensured every line of code solved a specific problem identified in the data.

| Gap Identified | Implementation |
|----------------|----------------|
| **Extreme Outliers** | `get_in` clipped at $900, `listings_median` at $1,760 (99th percentile) |
| **Skewed Distribution** | Applied `RobustScaler` (handles outliers better than Standard) |
| **No Interaction Terms** | Created `days_to_event` × `focus_bucket` features |
| **Temporal Leakage** | Strict time-based split (Train < 2025-01-01, Test >= 2025-01-01) |
| **Integer DOW encoding** | Converted Day-of-Week to cyclical Sin/Cos features |
| **Zero-inflated target** | Split targets: `target_sales_binary` (LogReg) and `target_sales_log` (XGBoost) |

---

## 2. Data Loading and Initial Filters
The first step was pulling the data from the Data Mart I built in BigQuery. I used `google.cloud.bigquery` to pull the panel data, applying initial sanity filters directly in the SQL to save memory.

I specifically filtered out "ghost events" (placeholder dates in 2028) and rows where `days_to_event` exceeded 1000, as these were confirmed to be platform errors during the EDA.

```python
query = """
WITH base AS (
  SELECT
    snapshot_date, event_date, days_to_event, event_id_stubhub,
    get_in, listings_median, listings_active,
    sales_total_7d, main_category AS focus_bucket,
    EXTRACT(DAYOFWEEK FROM event_date) AS event_dow
  FROM `secondary-tickets.seatdata.mart_event_snapshot_panel`
  WHERE days_to_event < 1000 AND event_date < '2028-01-01'
),
with_lags AS (
  SELECT *,
    LAG(sales_total_7d) OVER (PARTITION BY event_id_stubhub ORDER BY snapshot_date) AS sales_total_7d_prev
  FROM base
)
SELECT *, (sales_total_7d - sales_total_7d_prev) AS sales_total_change_7d
FROM with_lags
"""
df = client.query(query).to_dataframe()
