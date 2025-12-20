---
layout: single
title: "Market-Segmented Demand Forecasting Secondary Ticket Sales"
date: 2025-12-21
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
excerpt: "How segmentation can outperform generalization in prediction machine learning while understanding price-elasticity differences and market-specific secondary ticket transaction patterns."
---

## Abstract

## Key Contributions

---

## 1. Introduction
I love live entertainment, and I enjoy statistics and modeling. I want to see the two intersect and, after a couple of coffee chats with analysts in the industry, they suggested that I tackle demand forecasting ticket sales.

I wanted to take this challenge on not only to use for recruiting in the Spring upon graduation, but also to become more familiar with the ticketing industry. I wanted to understand how ticket sales move as different time features change. So, I decided to dive headfirst into this project and learn along the way. It also helps to use the new ML preprocessing and modeling techniques I'm learning in my classes towards an industry I truly enjoy.

### 1.1 Problem Statement
However, demand modeling is not so simple. Data sources in this industry are closely guarded. Public information about ticket sales, prices, and other demand signals are also very difficult to find.

The reasoning behind this is likely due to the BOTS Act (and it's recent enforcement) in the secondary ticket market to prevent people from automating scraping and scalping ticket inventory. So, the industry doesn't want this information in the hands of just anyone.

### 1.2 My Approach
While artist teams set primary ticket prices for a concert, for example, the secondary market is where you really see the true ticket price converge when it comes to decentralized economics. Every individual seller sets their own price, often guided by pricing recommendations from their secondary ticketing platform.

With accurate modeling, the potential impact is huge:
* Marketing can decide when to drop ad spend to push a show
* Business Insights can forecast expected sales in the primary market by watching secondary proxy demand
* Finance can have confidence intervals on expected revenue with better known demand signals

You get the picture! My goal was to build a system that can accurately forecast demand in a way that isn't well documented online and that wows recruiters (hopefully)!

---

## 2. Data Pipeline and Warehouse Design

### 2.1 Raw Ingestion

### 2.2 Dimensional Modeling

| Table | Grain | Key Columns | Purpose |
|-------|-------|-------------|---------|
| `dim_events` | 1 per `event_id_stubhub` | `event_name`, `event_date`, `venue_name`, `venue_capacity` | Latest snapshot metadata per event [file:7] |
| `dim_venues` | 1 per venue | `venue_key = HASH(name, city, state)` | Deterministic venue deduplication [file:7] |
| `dim_event_categories` | 1 per event | `event_category_detailed` (38 labels), `focus_bucket` (6 buckets) | Taxonomy built via regex ladder on normalized names [file:7] |

#### Dimension Tables

#### Fact Tables
- **`fact_event_snapshots`**: Cleaned copy of raw snapshots, partitioned by `imported_at`, clustered by `event_id_stubhub` for time-travel queries [file:7]

### 2.3 Data Mart
**`mart_event_snapshot_panel`**: grain = (event × snapshot-day) within ±65 days of event date [file:7]

**Key columns:**
- **Identifiers**: `event_id_stubhub`, `snapshot_date`, `days_to_event`
- **Demand features**: `get_in`, `listings_median`, `listings_active`, `sales_total_{1d,3d,7d,14d,30d,90d}`
- **Categories**: `focus_bucket`, `event_category_detailed`

**Design rationale:** Enables per-event time-series queries, bucket-level aggregations, and rolling window feature engineering without repeated joins or window functions at query time [file:7].

---

## 3. Feature Engineering

### 3.1 Imputation Strategy

| Feature Type | Imputation Rule | Justification |
|--------------|----------------|---------------|
| Price features (`get_in`, `listings_median`) | Event-level median → global median | Preserves relative pricing within event lifecycle [file:6] |
| Inventory (`listings_active`) | Event-level median → 0 | Zero indicates sold out or not listed [file:6] |
| Sales (`sales_total_7d`, etc.) | Fill with 0 | Zero-inflation is domain truth (most events have no sales on most days) [file:6] |

### 3.2 Transforming Features

### 3.3 Target Variables

---

## 4. Baseline Global Models

### 4.1 Model Selections

#### Classification

#### Regression

### 4.2 Naive

### 4.3 Tree-Based Models

#### Hyperparameter Search

### 4.4 Neural Network

### 4.5 Performances

#### Per-Bucket Error (in Tickets)

---

## 5. Market-Segmented Models

### 5.1 Focus Bucket Definition

### 5.2 Pipeline Per Bucket

### 5.3 Model Selection

### 5.4 Comparison to Global Models

---

## 6. Evaluation

### 6.1 Back Transformation

### 6.2 Performances

### 6.3 Error Distributions

### 6.4 RMSE by Bucket

---

## 7. Insights

### 7.1 Why Segmentation Works

### 7.2 Limits

### 7.3 Other Architectures to Try Next

--- 

## 8. Insights

segmenting works really well
---

## Appendix

## Inspiration
@nrankin0: https://medium.com/@nmrankin0/using-machine-learning-and-cloud-computing-to-forecast-the-resale-of-concert-tickets-293c2f15c13b
