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
The first hurdle to this project was finding the right data. Since September I have been searching for data sources that could provide enough granularity (width) and instances (length) to be able to use in my dream project. 

When researching, I came across a couple of dead ends. At first, I thought free APIs might be enough. However, I quickly found that the free-tiers of well-known platforms (Ticketmaster Discovery API, SeatGeek's API) did not include ticket information and only included metadata for events. This was not going to work, and I realized that I would have to bite the bullet and pull out the credit card to complete this portfolio project.

Now, I'm a college student, so I wasn't trying to break the bank on a project, especially alongside paying tuition for Graduate School. That's when I came across TouringData's Patreon service for only $11/month. However, after gaining access to the past two years of touring information, the data would not be enough. CSVs were too generalized and aggregated for my liking, as I was only provided with total revenue and tickets sold statistics, as well as metadata on event and venue information.

Finally, I came across several platforms that seemed in the next tier, such as JamBase, TicketsData, and SeatData.io. These sites had plenty of tiers I could choose from to introduce granularity beyond what TouringData could afford, such as minimum prices, number of listings, and venue capacities. After weighing the different features and sampling data ingestions from each site, I eventually decided that SeatData.io would be my chosen platform. 

SeatData.io collects their data from StubHub listings, which is one of the top secondary ticket platforms for resale. I also ran this decision by Nathan, who confirmed that the platform had reliable data and recommended this site, considering the scope of my portfolio project. Specifically, I decided to subscribe to their Daily CSV ingestion service for a reasonable cost.

### 2.1 Data Source and Storage Decisions
I found this SeatData.io subscription to be a worthy sacrifice of my bank account. Every morning, a new CSV ranging from 50k to 60k events would land in my inbox for downloading. Data attributes for each event included `sales_totals` for 1/3/7/14/30/and 90 days, `get_in` minimum listing price, `venue_capacity`, `listings_active`, and `listings_median` to show a relative average ticket price for that event.

However, unlike many school projects and assignments that have tabular Excel, preprocessed and ready to model datasets, these CSVs were far from ready to model. In fact, each CSV weighed in at roughly 9MB and, after enough collection, would take up majority of my disk space on my laptop. I would need to find a way to prepare this data while keeping storage lean.

Enter: Google Cloud Services. I chose this cloud storage in order to simulate real-world querying and database management, skills I hadn't put into practice yet during my academic projects. So I thought, what better time to learn than now!

### 2.2 Raw Ingestion
To move from these CSV snapshots to a cloud-based data storage, I decided to build a Python script in Google Colab that handled these daily CSV exports. Using `google.colab.auth.authenticate.user()`, I was able to directly talk to Google Cloud Services from my Colab notebook. Then, with `files.upload()`, I could import one or many CSVs at a time into my local directory.

When reading these CSVs into Python, I came across some trouble 

Before pushing these CSVs directly into Google Cloud Services, I needed to create a BigQuery table that would catch my snapshot rows and store all of the data in its correct types. This resulted in an immutable fact table `event_ticket_snapshots`. This table would eventually hold every daily state for my nearly 100,000 events at roughly 4 million rows.

Next, I wanted to perform a bit of preprocessing on my CSVs before they landed in my BigQuery table. By building a `preprocess_csv` function, I was able to standardize these steps in my uploading script across all CSVs from SeatData.io. The function performed:

* **Type casting**: ensuring that data was transferred by its correct typing, such as
    * *Sales volume* in `INT64` because you cannot have a fraction of a ticket sale
    * *Prices* as `FLOAT64` to preserve decimal places in median listings or ticket price floors
    * *IDs, event and venue names, cities, and other descriptors* as `STRING` types, such as basic text
    * *Dates* as `DATE` in YYYY-MM-DD format
* **Date extraction**: feature engineering an `imported_date` directly from the filename (formatted 'eventlist_YYYYMMDD') to track these snapshots
* **Data integrity**: replacing newlines and dropping any rows that were missing `event_id_stubhub` or `event_name`
* **Deduplicating**: removing any duplicated rows sharing the same `event_id_stubhub`, `event_date`, and `venue_name` with duplicated ticket sale information in the same CSV

Next, since I had a difficult season of midterms and finals throughout the data collection process, I wanted to set up a gating function that prevented me from accidentally uploading a duplicated snapshot to BigQuery. So, I created a `check_snapshot_exists` function that checks the BigQuery table for that `imported_date` before finally pushing the prepped CSV to my table.

Before data landed in my table, these snapshots first landed in a Google Cloud Services staging layer as a data lake. This allowed me to have a durable backup source in case any transformations in the BigQuery table went wrong. That way, BigQuery could find this data via `LoadJobConfig`, which would make ingestion much faster and more stable for these large files than data streams like `to_gbq`. 

In this job configuration, I clarified the expecting schema of my BigQuery table, appended each new CSV to the table with `write_disposition='WRITE_APPEND'`, stopped the load when `max_bad_records=10`, and skipped the header row with `skip_leading_rows=1`. 

After pushing the data to my data lake, I told BigQuery to `load_table_from_uri` to insert the loaded data with the job configuration finally into my BigQuery table.

#### Extra Context
After a coffee chat conversation in November with Nathan, I only had about a month of snapshots to show for, so when I proposed my demand forecasting idea, he heavily recommended I backfill the previous month before starting, since I couldn't yet capture patterns. So, I was able to obtain data from October 1st to November 9th to give me the previous 40 days of snapshots to help before I started modeling.

Additionally, upon this backfill, the sales representative let me know that SeatData.io had technical issues that prevented any data collection on October 4th. This would be a challenge in future modeling but was important to note both for collection and data preparation.

Now, with my BigQuery table beefing up with every new day, I wanted to put my Information Management course to work by structuring my database in a star schema.

### 2.3 Dimensional Modeling
In a star schema, data is structured as fact and dimensional tables. Fact tables are where statistics and numbers live, while descriptors are sent to dimensional tables. This way, data is structured so that I could query information faster in EDA and feature engineering steps. I can reduce the number of JOINS, plus I wouldn't be searching the entire 4 million-row table when trying to answer specific questions in my analyses.

In order to determine the dimension tables I would need for this project, I had to decide the level of grain that one row would contain in each table. Below is the conclusion I landed on.

| Table | Grain | Key Columns | Purpose |
|-------|-------|-------------|---------|
| `dim_events` | 1 per `event_id_stubhub` | `event_name`, `event_date`, `event_time`, `venue_name`, `venue_capacity` | Latest snapshot metadata per event |
| `dim_venues` | 1 per venue | `venue_key` | Venue hexadecimal key faster for joins |
| `dim_events_categorized` | 1 per `event_id_stubhub` | `event_category` (38 labels), `event_id_stubhub`, `focus_bucket` (6 buckets) | Granular categories built via regex ladder |

#### Dimension Tables
- **`dim_events`**: This table served to simplify the unique events found in my database by using the ``ROW_NUMBER() OVER (`event_id_stubhub`)`` function. `WHERE rn = 1` allowed me to use only the latest information found among the snapshots for event names or venue names. I would need this table later for feature engineering statistics like lead time until the event.
- **`dim_venues`**: By using the function ``TO_HEX(SHA256(CONCAT(`venue_name`, `venue_city`, `venue_state`)))``, I created a surrogate key with the `TRIM` and `LOWER` functions. This lets my database join tables to speed up querying much faster than on long strings of text
- **`dim_events_categorized`**: This table required a lot of work on the front-end, since I wanted to explore the relationships of demand forecasting by different event types. Below I outline my methodology for creating these categories by using each `event_name` and `venue_name`:
    - I began with a `base` CTE before categorizing anything. This step allowed me to clean punctuation and standardize `event_name` similar to NLP steps. I used `REGEX_REPLACE` to remove punctuation entirely and `NORMALIZE_AND_CASEFOLD` to ensure that all-caps names would be treated the same as lowercased and the same as different letter accents, such as é and e.
    - Next, I built my `raw_categorization` CTE with the help of Gemini 3. This is a massive script that uses Regular Expressions (Regex) to sort events into detailed groupings. Building this CTE required parsing through the patterns of strings in `event_name` and editing `CASE` logic with more examples of artists until my Other Events category had diminishing returns. There is a specific priority order that I used to build this CTE that matters when categorizing these events:
        - First, non-event filters identified ticket listings for parking passes, shuttle access, or VIP upgrades. Removing these rows from modeling would be helpful in reducing the noise these would insert into my ticket price averages, for example
        - Next, a niche recognition logic for categories like Theater - Vegas/Cirque, Jam/Bluegrass, and Electronic/EDM based on artists that came up while investigating my Other Events missed bucket
        - Then, a team sports logic identified team names of every major league (NBA, NFL, MLB, NHL) and placed them in their respective buckets
        - Lastly, if the `event_name` didn't give it away, the script then evaluates the `venue_name` as a final push to categorize events, such as an event at a House of Blues would be sent to the Concerts - Other category
 
> `WHEN REGEXP_CONTAINS(language code, r'\b(justin bieber|dijon)\b')
> THEN 'Concert - Pop'`

    - Above shows a shell of code that summarizes how these `CASE` logics functioned. These statements were able to handle n_grams of `event_name` matches in the list provided while also being able to handle some language translation.
    - These categories were built with granularity in mind, separating by genre, major and minor sports leagues, and also niche events and special attractions.
    - Later, these categories would be aggregated to form the basis of `focus_bucket`s for my analysis

#### Fact Tables
- **`fact_event_snapshots`**: Cleaned copy of raw snapshots, partitioned by `imported_at`, clustered by `event_id_stubhub` for time-travel queries [file:7]

### 2.4 Data Mart
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
