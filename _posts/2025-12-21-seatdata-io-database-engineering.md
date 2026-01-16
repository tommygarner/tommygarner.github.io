---
layout: single
title: "SeatData.io Part 1: Database Engineering and Warehouse"
date: 2025-12-21
description: "Designing a Star Schema and ETL Pipeline in BigQuery for High-Frequency Secondary Market Snapshots"
author_profile: true
toc: true
toc_sticky: true
tags:
  - database management
  - sql
  - google cloud services
  - bigquery
  - python
excerpt: "How I built a scalable infrastructure to ingest and structure 6 million rows of ticketing data using GCS and dimensional modeling"
---

<img width="1920" height="1080" alt="image" src="https://github.com/user-attachments/assets/55483715-24f4-4d15-bf99-26edee664138" />

## Abstract

In the secondary ticketing industry, data is often hard to find and behind paywalls. To conduct any meaningful analysis, I first had to solve a significant engineering hurdle: high-frequency data ingestion and storage. This article details how I built a cloud data warehouse for my SeatData.io project. By leveraging Google Cloud Services (GCS) for raw staging and BigQuery for dimensional modeling, I transformed daily 9MB CSV snapshots into a structured star schema containing over 6 million records.

## Key Contributions

-  Automated Python-based ETL pipeline
-  Star Schema dimensional modeling
-  Regex classification engine (NLP)

---

## 1. Introduction
I love live entertainment, and I enjoy statistics and modeling. I want to see the two intersect and, after a couple of coffee chats with analysts in the industry, they suggested that I tackle **demand forecasting** ticket sales to learn more about the ticketing industry and learn quickly.

So, I wanted to take this challenge on not only to use for **recruiting in the Spring upon graduation**, but also to integrate the tools I'm learning in graduate school into industry projects. I decided to dive in headfirst not just to build a model, but to build the entire data lifecycle. I wanted to move beyond the static, cleaned classroom datasets and into the **messier, high-frequency** reality of data in the secondary market.

### 1.1 The Challenge
However, demand modeling is not so simple. **Data sources in this industry are closely guarded**. Public information about ticket sales, prices, and other demand signals are also very difficult to find.

The reasoning behind this is likely due to the **BOTS Act** (and it's recent enforcement) in the secondary ticket market to prevent people from **automating scraping and scalping** ticket inventory. So, the industry doesn't want this information in the hands of just anyone. Also, there's a form of **competition** amongst different ticketing platforms that use analytics to make recommendations to customers selling their tickets, for example.

### 1.2 My Approach
While the ultimate goal is to forecast how secondary market prices and sales volume moves, I couldn't model what I couldn't store. Secondary market listings change by the hour and sales are sparse, with many events having zero-day sales. I needed a system that had:

-  **History**: Capturing daily snapshots so that to evaluate that point in time
-  **Data Integrity**: Standardizing messy CSV inputs into a schema
-  **Opportunity to Scale**: Allowing for fast querying across millions of rows

In this post, I detail the first phase of this SeatData.io project: moving **from raw email attachments** to a fully modeled **BigQuery Star Schema**. This foundation gives me reassurance when I get to later steps down the line, such as feature engineering or machine learning, that my data is clean and ready for work.

---

## 2. Data Pipeline and Warehouse Design
The first hurdle to this project was **finding the right data**. Since September 2025, I have been searching for data sources that could provide enough granularity (width) and instances (length) to be able to use in my dream project. 

When researching, I came across a couple of dead ends. At first, I thought free **APIs** might be enough. However, I quickly found that the free-tiers of well-known platforms (Ticketmaster Discovery API, SeatGeek's API) did not include ticket information and only included metadata for events. This was not going to work, and I realized that I would have to bite the bullet and pull out the credit card to complete this portfolio project.

Now, I'm a college student, so I wasn't trying to break the bank on a project, especially alongside paying tuition for Graduate School. That's when I came across **TouringData's Patreon** service for only $11/month. However, after gaining access to the past two years of touring information, the data would not be enough. CSVs were too *generalized and aggregated* for my liking, as I was only provided with total revenue and tickets sold statistics, as well as metadata on event and venue information.

Finally, I came across several platforms that seemed in that next tier, such as JamBase, TicketsData, and SeatData.io. These sites had plenty of tiers I could choose from to introduce granularity beyond what TouringData could afford, such as minimum prices, number of listings, and venue capacities. After weighing the different features and sampling data ingestions from each site, I eventually decided that **SeatData.io** would be my chosen platform. 

SeatData.io collects their data from **StubHub listings**, which is one of the top secondary ticket platforms for resale. I also **validated** this data source with an industry mentor to ensure the granularity met industry standards, considering the scope of my portfolio project. Specifically, I decided to subscribe to their **Daily CSV ingestion** tier for a reasonable cost.

### 2.1 Data Source and Storage Decisions
I found this SeatData.io subscription to be a worthy sacrifice of my bank account. Every morning, a new CSV ranging from **50k to 60k events** would land in my inbox for downloading. Data attributes for each event included **`sales_totals`** for 1/3/7/14/30/and 90 days, **`get_in`** minimum listing price, **`venue_capacity`**, **`listings_active`**, and **`listings_median`** to show a relative average ticket price for that event.

However, unlike many school projects and assignments that have tabular Excel, preprocessed and ready to model datasets, these CSVs were far from ready to model. In fact, each CSV weighed in at roughly 9MB and, after enough collection, would take up majority of my disk space on my laptop. I would need to find a way to prepare this data while keeping storage lean.

Enter: **Google Cloud Services**. I chose this cloud storage in order to simulate **real-world querying and database management**, skills I hadn't put into practice yet during my academic projects. So I thought, what better time to learn than now!

### 2.2 Raw Ingestion
To move from these CSV snapshots to a cloud-based data storage, I decided to build a **Python script** in Google Colab that handled these daily CSV exports. Using `google.colab.auth.authenticate.user()`, I was able to directly talk to Google Cloud Services from my Colab notebook. Then, with `files.upload()`, I could import one or many CSVs at a time into my local directory.

Before pushing these CSVs directly into Google Cloud Services, I needed to create a **BigQuery table** that would catch my snapshot rows and store all of the data in its correct types. This resulted in an immutable **fact table `event_ticket_snapshots`**. This table would eventually hold every daily state for my nearly 100,000 events at roughly 6 million rows.

Next, I wanted to perform a bit of **preprocessing** on my CSVs before they landed in my BigQuery table. By building a `preprocess_csv` function, I was able to standardize these steps in my uploading script across all CSVs from SeatData.io. The function performed:

* **Type casting**: ensuring that data was transferred by its correct typing, such as
    * *Sales volume* in `INT64` because you cannot have a fraction of a ticket sale
    * *Prices* as `FLOAT64` to preserve decimal places in median listings or ticket price floors
    * *IDs, event and venue names, cities, and other descriptors* as `STRING` types, such as basic text
    * *Dates* as `DATE` in YYYY-MM-DD format
* **Date extraction**: feature engineering an `imported_date` directly from the filename (formatted 'eventlist_YYYYMMDD') to track these snapshots
* **Data integrity**: replacing newlines and dropping any rows that were missing `event_id_stubhub` or `event_name`
* **Deduplicating**: removing any duplicated rows sharing the same `event_id_stubhub`, `event_date`, and `venue_name` with duplicated ticket sale information in the same CSV, using `.drop_duplicates()`

Next, since I had a difficult season of midterms and finals throughout the data collection process and accrued many snapshots in my inbox, I wanted to set up a gating function that prevented me from accidentally uploading a duplicated CSV to BigQuery. So, I created a `check_snapshot_exists` function that checks the BigQuery table for that `imported_date` before finally pushing the prepped CSV to my table.

Before data landed in my table, these snapshots first landed in a Google Cloud Services **staging layer** as a **data lake**. This allowed me to have a durable backup source in case any transformations in the BigQuery table went wrong. That way, BigQuery could find this data via `LoadJobConfig`, which would make ingestion much faster and more stable for these large files than **data streams** like `to_gbq`. 

In this job configuration, I clarified the expecting schema of my BigQuery table, **appended each new CSV to the table** with `write_disposition='WRITE_APPEND'`, stopped the load when `max_bad_records=10`, and skipped the header row with `skip_leading_rows=1`. 

After pushing the data to my **data lake**, I told BigQuery to `load_table_from_uri` to insert the loaded data with the job configuration finally into my **BigQuery table**.

#### Extra Context
After a coffee chat conversation in November with an industry mentor, I only had about a month of snapshots to show for, so when I proposed my demand forecasting idea, he heavily recommended I **backfill** the previous month before starting, since I couldn't yet capture patterns. So, I was able to obtain data from *October 1st to November 9th* to give me the previous 40 days of snapshots to help before I started modeling.

Additionally, upon this backfill, the sales representative let me know that SeatData.io had technical issues that prevented any data collection on **October 4th**. This would be a challenge in future modeling but was important to note both for collection and data preparation.

Now, with my BigQuery table beefing up with every new day, I wanted to put my Information Management course to work by structuring my database in a **star schema**.

### 2.3 Dimensional Modeling
In a star schema, data is structured as **fact and dimensional tables**. Fact tables are where **statistics and numbers** live, while **descriptors** are sent to dimensional tables. This way, data is structured so that I could **query information faster** in EDA and feature engineering steps. I can **reduce the number of JOINS**, plus I wouldn't be searching the entire 6 million-row table when trying to answer specific questions in my analyses.

<img width="747" height="389" alt="image" src="https://github.com/user-attachments/assets/f8e86cd8-4023-48e2-9ee1-2cea7c3d71fd" />

*Figure 1: Entity relationship diagram for my SeatData.io Warehouse*

In order to determine the dimension tables I would need for this project, I had to decide the **level of grain** that one row would contain in each table. Below is the conclusion I landed on.

| Table | Grain | Key Columns | Purpose |
|-------|-------|-------------|---------|
| **`dim_events`** | 1 per `event_id_stubhub` | `event_name`, `event_date`, `event_time`, `venue_name`, `venue_capacity` | Latest snapshot metadata per event |
| **`dim_venues`** | 1 per venue | `venue_key` | Venue hexadecimal key faster for joins |
| **`dim_events_categorized`** | 1 per `event_id_stubhub` | `event_category` (38 labels), `event_id_stubhub`, `focus_bucket` (6 buckets) | Granular categories built via **regex ladder** |
| **`fact_event_snapshots`** | 1 per event per day | 'event_id_stubhub`, `imported_at` | Storage for time-series metrics like price and inventory |
| **`mart_event_snapshot_panel`** | 1 row per event per day | `event_id_stubhub`, `days_to_event`, `price_spread_ratio` | Includes engineered and joined metrics to pull straight into Python notebooks |

### 2.4 Dimension Tables
- **`dim_events`**: This table served to simplify the unique events found in my database by using the ``ROW_NUMBER() OVER (`event_id_stubhub`)`` function. `WHERE rn = 1` allowed me to use only the latest information found among the snapshots for event names or venue names. I would need this table later for feature engineering statistics like lead time until the event.
- **`dim_venues`**: By using the function ``TO_HEX(SHA256(CONCAT(`venue_name`, `venue_city`, `venue_state`)))``, I created a **surrogate key** with the `TRIM` and `LOWER` functions. This lets my database join tables to speed up querying much faster than on long strings of text
- **`dim_events_categorized`**: This table required a lot of work on the front-end, since I wanted to explore the relationships of demand forecasting by different **event types**. Below I outline my methodology for creating these categories by using each `event_name` and `venue_name`:
    - I began with a `base` **CTE** before categorizing anything. This step allowed me to **clean punctuation and standardize `event_name`** similar to NLP steps. I used `REGEX_REPLACE` to remove punctuation entirely and `NORMALIZE_AND_CASEFOLD` to ensure that all-caps names would be treated the same as lowercased and the same as different letter accents, such as é and e.
    - Next, I built my `raw_categorization` **CTE** with the help of *Gemini 3*. This is a massive script that uses **Regular Expressions (Regex)** to sort events into detailed groupings. Building this CTE required parsing through the patterns of strings in `event_name` and editing `CASE` logic with more examples of artists until my Other Events category had diminishing returns. There is a specific priority order that I used to build this CTE that matters when categorizing these events:
        - First, **non-event filters** identified ticket listings for parking passes, shuttle access, or VIP upgrades. Removing these rows from modeling would be helpful in reducing the noise these would insert into my ticket price averages, for example
        - Next, a **niche recognition logic** for categories like Theater - Vegas/Cirque, Jam/Bluegrass, and Electronic/EDM based on artists that came up while investigating my Other Events missed bucket
        - Then, a **team sports logic identified team names of every major league** (NBA, NFL, MLB, NHL, MLS) and placed them in their respective buckets
        - Lastly, if the `event_name` didn't give it away, the script then **evaluates the `venue_name`** as a final push to categorize events, such as an event at a House of Blues would be sent to the Concerts - Other category
 
> `WHEN REGEXP_CONTAINS(language code, r'\b(justin bieber|dijon)\b') THEN 'Concert - Pop'`

Above shows a shell of code that summarizes how these `CASE` logics functioned. These statements were able to handle n_grams of `event_name` matches in the list provided while also being able to handle some **language translation**.

These categories were built with granularity in mind, separating by genre, major and minor sports leagues, and also niche events and special attractions. After the LLM-generated logic was built, I **manually audited the top 50 Other events** to refine these Regex patterns for high-volume events.

Later, these categories would be aggregated to form the basis of **`focus_buckets`** for my analysis. I would combine these into seven buckets:

| Main Category      | Examples                         | Event Count | Percentage |
|--------------------|-------------------------------------|-------------|------------|
| **Concert**            | Rock, Pop, Electronic               | 38,223      | 38%        |
| **Broadway & Theater** | Hamilton, Lion King, MJ The Musical | 24,439      | 24%        |
| **Other**              | Museums, Meow Wolf                  | 16,851      | 17%        |
| **Comedy**             | Stand-up, Improv, Comedy Specials   | 9,021       | 9%         |
| **Major Sports**       | NBA, NFL, MLB, NHL, MLS             | 7,814       | 8%         |
| **Minor/Other Sports** | Tennis, UFC, Rodeo, NCAA            | 3,515       | 3%         |
| **Festivals**          | Coachella, Lollapalooza, ACL        | 516         | 1%         |

I landed on these major categories because I thought there was enough differentiation between them and their target consumers/fans that would be telling for my project. For example, I'm expecting to see professional sports tickets move very differently than concert tickets, and will explore this later!

### 2.5 Fact Table
The **`fact_event_snapshots` table** acts as the central storage table for all quantitative data. Unlike dimension tables which store descriptive elements, this table is designed to **grow** alongside the influx of new data as I append more CSV snapshots.

This table is **partitioned by `imported_at`** to help me query specific time ranges easily from this fact table. Additionally, the table is **clustered by `event_id_stubhub`**, organizing events within their own **time-series**. The table is also a cleaned copy of the raw `event_ticket_snapshots` source but is organized in a way that can be easily joined to my dimensional tables for creating a data mart for my specific project use.

### 2.6 Data Mart
Speaking of which, I then created a data mart within BigQuery to pull from when I begin looking at the data more closely and feature engineering and modeling. **`mart_event_snapshot_panel`** joins the **`dim_event_categories`** with the **central fact table** as well as event and venue **metadata**. 

I also decided to introduce engineered features such as **`price_spread_ratio`** using `SAFE_DIVIDE(get_in, listings_median)` to capture the **relationship between the lowest and median listing price** on StubHub. I thought this feature might help future models understand the relationship of demand to price for the related event, where a *low ratio* suggests that resellers might be trying to get rid of inventory for dirt cheap instead of taking the $0 salvage value of missing the event entirely. If the `price_spread_ratio` was close to *1.0*, that might suggest the secondary market has a competitive and relatively stable price to actual demand.

I also feature engineered the **`days_to_event`** variable, which calculates the amount of days between the `event_date` and `imported_at` date. Later on I will take a stab and understanding particular events in this dataset, the distribution of this variable, and more in feature engineering.

Below is the Data Flow Diagram of my database:

<img width="1024" height="559" alt="image" src="https://github.com/user-attachments/assets/1c3819c3-9f63-494b-ae75-b2224497f38c" />

*Figure 2: Data flow diagram behind my database engineering*

---

## Tech Stack

- Data ingestion: SeatData.io CSV, Python
- Data warehouse: BigQuery (star schema)
- Transformation: SQL
- Natural Language Processing: SQL Regex

## Appendix

## Inspiration
Special thanks to @nrankin0 for the foundational work on [Using Machine Learning and Cloud Computing to Forecast Resale Tickets](https://medium.com/@nmrankin0/using-machine-learning-and-cloud-computing-to-forecast-the-resale-of-concert-tickets-293c2f15c13b)! The project was a significant spark for my own undertaking and is a great read as well.
