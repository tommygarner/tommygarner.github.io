---
layout: single
title: "SeatData.io Part 3: Feature Engineering for Demand Forecasting"
date: 2026-01-15
description: "Transforming raw ticket data into model-ready features through scaling, encoding, and domain-driven interaction terms"
author_profile: true
toc: true
toc_sticky: true
tags:
  - feature engineering
  - data transformation
  - machine learning
  - python
  - pandas
excerpt: "From raw snapshots to prediction-ready features: the critical transformations that set up successful modeling."
---

<img width="421" height="278" alt="image" src="https://github.com/user-attachments/assets/6d70d229-4242-46f3-8d6c-9e5fae2ce4ed" />

## Abstract

After validating data quality in Part 2's EDA, I faced a critical question: how do I transform 5.7 million raw snapshots into features that models can actually learn from? Feature engineering bridges the gap between raw data and predictive models. Through log transformations, cyclical encoding, and domain-driven interaction terms, I engineered 29 features that capture the temporal dynamics, pricing psychology, and segment-specific behaviors of the secondary ticket market.

## Key Insights

- **Log Transformations for Skewed Distributions** - Sales and prices follow power-law distributions requiring mathematical normalization
- **Cyclical Encoding for Temporal Patterns** - Days of the week are circular, not linear; sine/cosine encoding preserves this structure
- **Interaction Terms for Segment-Specific Behavior** - Sports fans buy differently than concert-goers as events approach

---

## 1. Target Variable Engineering

Before building features, I needed to define what I was actually predicting. My target: **ticket sales in the next 7 days**. But there was a problem.

### 1.1 The Zero-Sales Problem

Looking at my `sales_total_7d_next` distribution, I discovered that **73% of snapshots had zero sales** in the following week. This created a classic machine learning challenge: predicting a zero-inflated distribution.

*Figure 1: Target distribution showing extreme right-skew with 73% zeros*

I initially tried predicting raw sales directly, but models struggled with this distribution. A prediction of "30 tickets" when the actual was "200 tickets" has the same squared error as predicting "30" when actual was "0" - but these errors have very different business implications.

### 1.2 The Two-Stage Solution

I split the problem:

**Stage 1 (Binary Classification):** Will there be ANY sales?
- Target: `target_sales_binary` (1 if sales > 0, else 0)
- Purpose: Filter out the 73% of events with zero sales
- Not covered in this series, but critical for production

**Stage 2 (Regression):** For events WITH sales, how many tickets?
- Target: `target_sales_log` = log(sales_total_7d_next + 1)
- Purpose: Predict sales volume on meaningful events
- This is what I focused on for modeling

### 1.3 Why Log Transformation?

Raw sales ranged from 1 to 2,803 tickets - a distribution dominated by outliers. Taking the logarithm:
- Compressed the scale: 2,803 becomes 7.94
- Normalized the distribution: Created a more Gaussian shape
- Penalized errors proportionally: Being off by 10 tickets matters more for low-volume than high-volume events
```python
# Target transformation
train_with_sales = train_df[train_df['target_sales_binary'] == 1].copy()
train_with_sales['target_sales_log'] = np.log1p(train_with_sales['sales_total_7d_next'])
```

The `log1p()` function (log(1 + x)) handles the edge case where sales = 0 without creating undefined values.

*Figure 2: Comparison of raw vs log-transformed target distribution - log version is approximately normal*

---

## 2. Temporal Feature Engineering

Ticket buying behavior is fundamentally temporal. Fans don't buy randomly - they buy based on **how close the event is** and **what day of the week it is**. I needed to encode these patterns mathematically.

### 2.1 Days-to-Event Scaling

The `days_to_event` feature (snapshot_date - event_date) ranged from 0 to 338 days. Neural networks perform poorly with features on vastly different scales, so I standardized:
```python
from sklearn.preprocessing import StandardScaler

scaler = StandardScaler()
train_df['days_to_event_scaled'] = scaler.fit_transform(
    train_df[['days_to_event']]
)
```

This transformation centers the feature at mean = 0 and scales to standard deviation = 1. Tree-based models (XGBoost, LightGBM) don't care about scaling, but neural networks need it for gradient descent to converge properly.

### 2.2 Cyclical Encoding for Day-of-Week

Here's where it gets interesting. My EDA in Part 2 showed that **Saturdays have 5,000 more daily sales than Sundays**. Day-of-week matters.

But there's a trap: If I encoded Monday=1, Tuesday=2...Sunday=7, the model thinks Sunday (7) is "far" from Monday (1). In reality, Sunday and Monday are adjacent! The week is a **circle**, not a line.

The solution: **sine and cosine encoding**.

Think of the week as a clock face. Each day occupies a position on the circle:
- Monday: 0° (or 0 radians)
- Tuesday: 51.4° (or 2π/7 radians)
- Wednesday: 102.8°
- ...
- Sunday: 308.6°

Then I project this onto two axes:
```python
train_df['dow_sin'] = np.sin(2 * np.pi * train_df['day_of_week'] / 7)
train_df['dow_cos'] = np.cos(2 * np.pi * train_df['day_of_week'] / 7)
```

Now Sunday (day 6) and Monday (day 0) have similar sine/cosine values, preserving their adjacency. This encoding allows the model to learn patterns like "weekend behavior" without artificially inflating the distance between Sunday and Monday.

*Figure 3: Cyclical encoding visualization - days of week mapped to circle, then projected to sin/cos*

### 2.3 Binary Temporal Flags

Sometimes simplicity wins. I created binary indicators for known behavioral patterns:

- **`is_weekend`**: 1 if Saturday or Sunday, else 0
  - Captures the Part 2 finding that weekend sales spike
  
- **`is_final_week`**: 1 if days_to_event ≤ 7, else 0
  - Urgency increases dramatically in the final week
  
- **`is_anomaly_day`**: 1 if snapshot_date is Election Day, else 0
  - Remember that November 4th sales dip from Part 2? I encoded it explicitly

These flags give models an easy way to learn "if weekend, expect higher sales" without requiring complex non-linear relationships.

---

## 3. Price Feature Engineering

Prices in the secondary market ranged from $0.90 to $929,999 (yes, really - see Part 2's outlier analysis). Raw prices were useless for modeling.

### 3.1 Log-Scaling Prices

Just like sales, prices followed a power-law distribution. I log-transformed:
```python
train_df['get_in_log_scaled'] = scaler.fit_transform(
    np.log1p(train_df[['get_in']])
)
train_df['listings_median_log_scaled'] = scaler.fit_transform(
    np.log1p(train_df[['listings_median']])
)
```

This compressed the $0.90-$900 range into a manageable scale and standardized it for neural networks.

### 3.2 Relative Pricing Matters

Absolute price alone doesn't tell the full story. A $100 get-in price means different things depending on the median listing price. If the median is $120, the floor is relatively high (premium event). If the median is $500, the floor is a bargain.

I created the **price spread ratio**:
```python
train_df['price_spread_ratio'] = train_df['get_in'] / train_df['listings_median']
train_df['price_spread_ratio_scaled'] = scaler.fit_transform(
    train_df[['price_spread_ratio']]
)
```

This ratio captures **relative market positioning**:
- Ratio near 1.0: Tight spread, uniform pricing
- Ratio near 0.0: Wide spread, cheap floor relative to average

Models can learn "when spread is tight, sales are more predictable" without calculating this relationship from raw prices.

*Figure 4: Price spread ratio distribution by focus_bucket - Sports has tighter spreads than Concerts*

---

## 4. Inventory Feature Engineering

Inventory tells a story about demand. High inventory with slow sales? Event might be struggling. Low inventory with steady sales? Hot ticket.

### 4.1 Log-Scaled Inventory

Active listings ranged from 0 to 18,267 - another skewed distribution requiring log transformation:
```python
train_df['listings_active_log_scaled'] = scaler.fit_transform(
    np.log1p(train_df[['listings_active']])
)
```

### 4.2 Inventory Burn Rate

Static inventory counts miss the temporal dynamic. I created **inventory per day** - how much inventory remains relative to time until event:
```python
train_df['inv_per_day'] = (
    train_df['listings_active'] / 
    (train_df['days_to_event'] + 1)  # +1 to avoid division by zero
)
train_df['inv_per_day_scaled'] = scaler.fit_transform(
    np.log1p(train_df[['inv_per_day']])
)
```

This captures urgency: 100 listings with 50 days to go is different from 100 listings with 2 days to go.

### 4.3 Inventory Change Features

Inventory doesn't change randomly - sellers add and remove listings based on market signals. I calculated 7-day changes:
```python
train_df['listings_active_change_7d'] = (
    train_df.groupby('event_id_stubhub')['listings_active']
    .diff(7)  # Change from 7 days ago
)
train_df['listings_active_change_7d_scaled'] = scaler.fit_transform(
    train_df[['listings_active_change_7d']].fillna(0)
)
```

Increasing inventory suggests weak demand. Decreasing inventory suggests strong demand.

*Figure 5: Inventory dynamics over time showing November 1st spike from Part 2*

---

## 5. Historical Features: Learning from the Past

The best predictor of future sales? Past sales. I engineered lag features to capture momentum.

### 5.1 Sales Lag Features
```python
train_df['sales_total_7d_log_scaled'] = scaler.fit_transform(
    np.log1p(train_df[['sales_total_7d']])
)
```

This feature says: "This event sold X tickets in the past 7 days." Events with strong historical sales tend to continue selling.

### 5.2 Sales Change Features

But momentum matters too. Is the event accelerating or decelerating?
```python
train_df['sales_total_change_7d'] = (
    train_df.groupby('event_id_stubhub')['sales_total_7d']
    .diff(7)
)
train_df['sales_total_change_7d_scaled'] = scaler.fit_transform(
    train_df[['sales_total_change_7d']].fillna(0)
)
```

Positive change = accelerating sales. Negative change = slowing sales.

### 5.3 The 7-Day Window

Why 7 days specifically? I tested multiple windows (3, 7, 14, 30 days). Seven-day windows captured weekly patterns without introducing too much noise from rare one-time events.

### 5.4 Avoiding Data Leakage

Critical detail: These features are calculated **as of the snapshot date**, not retrospectively. Each row sees only data available at that moment in time. This prevents leakage where the model "cheats" by seeing the future.

---

## 6. Handling Missing Values: The Venue Capacity Problem

From Part 2's EDA, I knew that **42% of venue_capacity values were missing**. I couldn't just drop these rows - that would eliminate nearly half my training data.

### 6.1 Imputation Strategy

I initially considered:
1. **Drop rows**: Too much data loss
2. **Global median**: Ignores venue size differences across categories
3. **Predictive imputation**: Overly complex, risk of leakage

I chose **median imputation by focus_bucket**:
```python
venue_medians = train_df.groupby('focus_bucket')['venue_capacity'].median()

train_df['venue_capacity_filled'] = train_df.apply(
    lambda row: (
        row['venue_capacity'] 
        if pd.notna(row['venue_capacity']) 
        else venue_medians[row['focus_bucket']]
    ),
    axis=1
)
```

Why this works:
- Major Sports venues (stadiums) have ~30,000 capacity
- Broadway theaters have ~1,500 capacity  
- Concerts vary but average ~8,000

Using bucket-specific medians preserves these segment differences while filling gaps.

*Figure 6: Venue capacity distributions by bucket showing distinct patterns*

Then I log-scaled and standardized:
```python
train_df['venue_capacity_log_scaled'] = scaler.fit_transform(
    np.log1p(train_df[['venue_capacity_filled']])
)
```

---

## 7. Categorical Feature Engineering

Not all features are continuous. Some patterns are discrete.

### 7.1 Price Tier Binning

While I had continuous price features, I also wanted to capture non-linear price psychology. Buyers think in tiers: "under $50", "$50-$100", "over $100".

I binned `get_in` prices:
```python
train_df['price_tier'] = pd.cut(
    train_df['get_in'],
    bins=[0, 50, 100, np.inf],
    labels=['Low', 'Medium', 'High']
)
```

Then one-hot encoded for modeling:
```python
price_tier_dummies = pd.get_dummies(
    train_df['price_tier'], 
    prefix='price_tier',
    drop_first=True  # Avoid multicollinearity
)
```

This gives models an easy way to learn "High price tier events behave differently" without requiring complex non-linear transformations of continuous price.

### 7.2 Focus Bucket Dummies

My NLP categorization from Part 1 created `focus_bucket`. I one-hot encoded it:
```python
bucket_dummies = pd.get_dummies(
    train_df['focus_bucket'],
    prefix='bucket',
    drop_first=True
)
```

This creates binary indicators: `bucket_Concert`, `bucket_Broadway`, etc.

---

## 8. Interaction Features: Where Domain Knowledge Shines

This is where feature engineering gets powerful. My EDA revealed that **different segments exhibit different temporal patterns**. Sports fans buy on predictable schedules. Concert-goers buy based on price and artist popularity.

A unified model struggles to learn "for Sports, days_to_event matters MORE, but for Concerts, price matters MORE."

### 8.1 Days-to-Event × Bucket Interactions

I created interaction terms:
```python
for bucket in ['Major_Sports', 'Concert', 'Broadway', 'Minor_Sports', 'Comedy']:
    train_df[f'dte_X_bucket_{bucket}'] = (
        train_df['days_to_event_scaled'] * 
        train_df[f'bucket_{bucket}']
    )
```

What this does:
- For a Major Sports event, `dte_X_bucket_Major_Sports` = days_to_event value
- For a Concert event, `dte_X_bucket_Major_Sports` = 0

This allows models to learn **segment-specific time sensitivity**. The model can assign different weights to time depending on event type.

These features will prove critical in Part 8 when I test segment-specific models!

*Figure 7: Interaction term coefficients preview showing Major Sports has higher temporal sensitivity than Concerts*

---

## 9. Feature Validation

Before modeling, I validated my engineered features.

### 9.1 Correlation Analysis

I checked for multicollinearity - highly correlated features that provide redundant information:
```python
correlation_matrix = train_df[feature_cols].corr()
high_corr_pairs = [
    (i, j, correlation_matrix.loc[i, j]) 
    for i in correlation_matrix.columns 
    for j in correlation_matrix.columns 
    if i < j and abs(correlation_matrix.loc[i, j]) > 0.9
]
```

Found: `get_in_log_scaled` and `listings_median_log_scaled` correlated at 0.87. Not unexpected (floors and ceilings move together), but not redundant enough to drop.

### 9.2 Distribution Checks

I plotted distributions of all scaled features to ensure no extreme outliers survived transformation. All features now had reasonable ranges (typically -3 to +3 after standardization).

### 9.3 Leakage Checks

Most critical: I verified no features contained future information. Each snapshot's features used only data available **as of that snapshot_date**. Lag features looked backward, never forward.

### 9.4 Final Feature Count

**29 features ready for modeling:**
- 7 temporal features
- 6 price features  
- 5 inventory features
- 3 historical features
- 1 venue feature
- 2 price tier dummies
- 5 bucket dummies
- 5 interaction terms

---

## 10. Lessons Learned

### What Worked

**Log transformations covered 80% of needs.** Sales, prices, inventory - all power-law distributed, all fixed with `np.log1p()` and scaling.

**Domain knowledge beat automation.** Hand-crafted interaction terms (days_to_event × bucket) will outperform automated feature crosses in later models.

**Cyclical encoding mattered.** Sine/cosine for day-of-week captured weekend effects that linear encoding would miss.

**Imputation strategy preserved signal.** Bucket-specific median imputation for venue_capacity retained segment differences.

### What I'd Do Differently

**I should have created price percentile features earlier.** In Part 9's error analysis, I'll discover the model struggles with extreme prices. Price percentiles within each bucket would have helped.

**More temporal interactions.** I created bucket × days_to_event, but bucket × is_weekend might have captured additional patterns.

**Validation was critical.** The correlation and leakage checks caught issues before they became model bugs.

---

## What's Next

With 29 engineered features, my data was finally ready for modeling. But which algorithm would work best for ticket sales prediction?

In **Part 4: Foundation Models**, I put five different approaches head-to-head:
- Ridge Regression (linear baseline)
- Gradient Boosting (sequential trees)
- XGBoost (optimized gradient boosting)
- LightGBM (fast gradient boosting)
- CatBoost (categorical-aware boosting)

The winner? Tree-based models dominated. But the gap between them was surprisingly small, setting up the ensemble methods in Part 7...

---

*Code and notebooks available on [GitHub](#). Next article in the series coming soon.*
