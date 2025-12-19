---
layout: single
title: "Market-Segmented Demand Forecasting Secondary Ticket Sales"
date: 2025-12-17
description: "Using SeatData.io Secondary Ticket Sales and Machine Learning Models to Predict Total Sales for the Subsequent Week"
author_profile: true
toc: true
toc_sticky: true
tags:
  - machine learning
  - database management
  - demand forecasting
  - classification
  - tree-based learning
  - neural networks
  - tickets
  - python
  - sql
  - tensorflow
excerpt: "How market-specific models reduce RMSE from 93 to 19-43 tickets by learning within isolated focus buckets."
---

# Abstract

## Key Contributions

---

# 1. Introduction

## 1.1 Problem Statement

## 1.2 My Approach

---

# 2. Data Pipeline and Warehouse Design

## 2.1 Raw Ingestion

## 2.2 Dimensional Modeling

| Table | Grain | Key Columns | Purpose |
|-------|-------|-------------|---------|
| `dim_events` | 1 per `event_id_stubhub` | `event_name`, `event_date`, `venue_name`, `venue_capacity` | Latest snapshot metadata per event [file:7] |
| `dim_venues` | 1 per venue | `venue_key = HASH(name, city, state)` | Deterministic venue deduplication [file:7] |
| `dim_event_categories` | 1 per event | `event_category_detailed` (38 labels), `focus_bucket` (6 buckets) | Taxonomy built via regex ladder on normalized names [file:7] |

### Dimension Tables

### Fact Tables
- **`fact_event_snapshots`**: Cleaned copy of raw snapshots, partitioned by `imported_at`, clustered by `event_id_stubhub` for time-travel queries [file:7]

## 2.3 Data Mart
**`mart_event_snapshot_panel`**: grain = (event × snapshot-day) within ±65 days of event date [file:7]

**Key columns:**
- **Identifiers**: `event_id_stubhub`, `snapshot_date`, `days_to_event`
- **Demand features**: `get_in`, `listings_median`, `listings_active`, `sales_total_{1d,3d,7d,14d,30d,90d}`
- **Categories**: `focus_bucket`, `event_category_detailed`

**Design rationale:** Enables per-event time-series queries, bucket-level aggregations, and rolling window feature engineering without repeated joins or window functions at query time [file:7].

---

# 3. Feature Engineering

## 3.1 Imputation Strategy
| Feature Type | Imputation Rule | Justification |
|--------------|----------------|---------------|
| Price features (`get_in`, `listings_median`) | Event-level median → global median | Preserves relative pricing within event lifecycle [file:6] |
| Inventory (`listings_active`) | Event-level median → 0 | Zero indicates sold out or not listed [file:6] |
| Sales (`sales_total_7d`, etc.) | Fill with 0 | Zero-inflation is domain truth (most events have no sales on most days) [file:6] |

## 3.2 Transforming Features

## 3.3 Target Variables

---

# 4. Baseline Global Models

## 4.1 Model Selections

### Classification

### Regression

## 4.2 Naive

## 4.3 Tree-Based Models

### Hyperparameter Search

## 4.4 Neural Network

## 4.5 Performances

### Per-Bucket Error (in Tickets)

---

# 5. Market-Segmented Models

## 5.1 Focus Bucket Definition

## 5.2 Pipeline Per Bucket

## 5.3 Model Selection

## 5.4 Comparison to Global Models

---

# 6. Evaluation

## 6.1 Back Transformation

## 6.2 Performances

## 6.3 Error Distributions

## 6.4 RMSE by Bucket

---

# 7. Insights

## 7.1 Why Segmentation Works

## 7.2 Limits

## 7.3 Other Architectures to Try Next

--- 

# 8. Insights

---

# Appendix

# Inspiration
@nrankin0: https://medium.com/@nmrankin0/using-machine-learning-and-cloud-computing-to-forecast-the-resale-of-concert-tickets-293c2f15c13b
