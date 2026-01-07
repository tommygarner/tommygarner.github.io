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

Next, since I had a difficult season of midterms and finals throughout the data collection process and accrued many snapshots in my inbox, I wanted to set up a gating function that prevented me from accidentally uploading a duplicated CSV to BigQuery. So, I created a `check_snapshot_exists` function that checks the BigQuery table for that `imported_date` before finally pushing the prepped CSV to my table.

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
| `fact_event_snapshots` | 1 per event per day | 'event_id_stubhub`, `imported_at` | Storage for time-series metrics like price and inventory |
| `mart_event_snapshot_panel` | 1 row per event per day | `event_id_stubhub`, `days_to_event`, `price_spread_ratio` | Includes engineered and joined metrics to pull straight into Python notebooks |

### 2.4 Dimension Tables
- **`dim_events`**: This table served to simplify the unique events found in my database by using the ``ROW_NUMBER() OVER (`event_id_stubhub`)`` function. `WHERE rn = 1` allowed me to use only the latest information found among the snapshots for event names or venue names. I would need this table later for feature engineering statistics like lead time until the event.
- **`dim_venues`**: By using the function ``TO_HEX(SHA256(CONCAT(`venue_name`, `venue_city`, `venue_state`)))``, I created a surrogate key with the `TRIM` and `LOWER` functions. This lets my database join tables to speed up querying much faster than on long strings of text
- **`dim_events_categorized`**: This table required a lot of work on the front-end, since I wanted to explore the relationships of demand forecasting by different event types. Below I outline my methodology for creating these categories by using each `event_name` and `venue_name`:
    - I began with a `base` CTE before categorizing anything. This step allowed me to clean punctuation and standardize `event_name` similar to NLP steps. I used `REGEX_REPLACE` to remove punctuation entirely and `NORMALIZE_AND_CASEFOLD` to ensure that all-caps names would be treated the same as lowercased and the same as different letter accents, such as é and e.
    - Next, I built my `raw_categorization` CTE with the help of Gemini 3. This is a massive script that uses Regular Expressions (Regex) to sort events into detailed groupings. Building this CTE required parsing through the patterns of strings in `event_name` and editing `CASE` logic with more examples of artists until my Other Events category had diminishing returns. There is a specific priority order that I used to build this CTE that matters when categorizing these events:
        - First, non-event filters identified ticket listings for parking passes, shuttle access, or VIP upgrades. Removing these rows from modeling would be helpful in reducing the noise these would insert into my ticket price averages, for example
        - Next, a niche recognition logic for categories like Theater - Vegas/Cirque, Jam/Bluegrass, and Electronic/EDM based on artists that came up while investigating my Other Events missed bucket
        - Then, a team sports logic identified team names of every major league (NBA, NFL, MLB, NHL, MLS) and placed them in their respective buckets
        - Lastly, if the `event_name` didn't give it away, the script then evaluates the `venue_name` as a final push to categorize events, such as an event at a House of Blues would be sent to the Concerts - Other category
 
> `WHEN REGEXP_CONTAINS(language code, r'\b(justin bieber|dijon)\b') THEN 'Concert - Pop'`

Above shows a shell of code that summarizes how these `CASE` logics functioned. These statements were able to handle n_grams of `event_name` matches in the list provided while also being able to handle some language translation.

These categories were built with granularity in mind, separating by genre, major and minor sports leagues, and also niche events and special attractions.

Later, these categories would be aggregated to form the basis of `focus_bucket`s for my analysis. I would combine these into seven buckets:

| Main Category      | Description                         | Event Count | Percentage |
|--------------------|-------------------------------------|-------------|------------|
| Concert            | Rock, Pop, Electronic               | 38,223      | 38%        |
| Broadway & Theater | Hamilton, Lion King, MJ The Musical | 24,439      | 24%        |
| Other              | Museums, Meow Wolf                  | 16,851      | 17%        |
| Comedy             | Stand-up, Improv, Comedy Specials   | 9,021       | 9%         |
| Major Sports       | NBA, NFL, MLB, NHL, MLS             | 7,814       | 8%         |
| Minor/Other Sports | Tennis, UFC, Rodeo, NCAA            | 3,515       | 3%         |
| Festivals          | Coachella, Lollapalooza, ACL        | 516         | 1%         |

I landed on these major categories because I thought there was enough differentiation between them and their target consumers/fans that would be telling for my project. For example, I'm expecting to see professional sports tickets move very differently than concert tickets, and will explore this later!

### 2.5 Fact Table
The `fact_event_snapshots` table acts as the central storage table for all quantitative data. Unlike dimension tables which store descriptive elements, this table is designed to grow alongside the influx of new data as I append more CSV snapshots.

This table is partioned by `imported_at` to help me query specific time ranges easily from this fact table. Additionally, the table is clustered by `event_id_stubhub`, organizing events within their own time-series. The table is also a cleaned copy of the raw `event_ticket_snapshots` source but is organized in a way that can be easily joined to my dimensional tables for creating a data mart for my specific project use.

### 2.6 Data Mart
Speaking of which, I then created a data mart within BigQuery to pull from when I begin looking at the data more closely and feature engineering and modeling. `mart_event_snapshot_panel` joins the `dim_event_categories` with the central fact table as well as event and venue metadata. 

I also decided to introduced engineered features such as `price_spread_ratio` using `SAFE_DIVIDE(get_in, listings_median)` to capture the relationship between the lowest and median listing price on StubHub. I thought this feature might help future models understand the relationship of demand to price for the related event, where a low ratio suggests that resellers might be trying to get rid of inventory for dirt cheap instead of taking the $0 salvage value of missing the event entirely. If the `price_spread_ratio` was close to 1.0, that might suggest the secondary market has a competitive and relatively stable price to actual demand.

I also feature engineering the `days_to_event` variable, which calculates the amount of days between the `event_date` and `imported_at` date. While I don't have enough aggregated events and days to see how different `focus_bucket`s truly move as events reach their days, I still included this feature in modeling to see how my limited sample size would communicate this dynamic.

Below is the Data Flow Diagram of my database:

<img width="747" height="389" alt="image" src="https://github.com/user-attachments/assets/f8e86cd8-4023-48e2-9ee1-2cea7c3d71fd" />
*Figure 1: Data Flow Diagram for my SeatData.io Warehouse*

---

## 3. Exploratory Data Analysis

With the data mart structured, I then moved onto my EDA step to validate the data and investigate patterns of my SeatData.io snapshots. This phase was important for me to gain an understanding of the secondary ticket market and its features while also helping me decide which direction I wanted to take my first project with this data.

### 3.1 Initial Data Diagnostics and Cleaning
Before diving into demand and trends in my data, I used several functions to investigate the quality of my snapshot records and their attribute distributions
  - `.info()` and `.describe()` allowed me to check for null values and verify that my type casting from my ingestion script worked across the entire database in BigQuery. Distributions of both 1-day and 7-day sales were missing no values, and only `listings_median` was missing about 15% of the time, which might be because of low ticket volume (1-2 tickets that day), where a median cannot be calculated reliably
  - I also looked for the October 4th gap mentioned by SeatData.io to understand how it affected my rolling windows for sales totals
  - Finally, I evaluated the volume of unique events across my seven `focus_bucket`s to ensure that I had enough data and total snapshots to effectively model each bucket. I took a swing with Festivals, which had only 500 unique events and about 12,000 rows. Otherwise, every other bucket had more than 2,000 events with over 71,000 rows in their respective categories. 

### 3.2 Bucket EDA
I decided to then understand demand, price and inventory statistics by each `focus bucket` to see how different markets move daily by aggregating these numbers with each day in my database. Below shows the trend of 1-day sales over time by bucket.

<img width="989" height="490" alt="image" src="https://github.com/user-attachments/assets/ea4b29f4-9109-4b17-a0c7-e41069f50765" />
*Figure 2: 1-day sales aggregated by `focus_bucket`

Some initial insights I found from this data included:
  - Major sports has many ticket transactions (with an average of around 7,000 tickets sold on StubHub per day) compared to the next tier of Concerts and Other Events
  - Major sports also is the most volatile, with major swings in the hundreds of tickets
  - Interestingly, Minor sports has about 1/4th of the ticket volume moving on StubHub than does Major sports
  - There is a day of massive dips in ticket transactions for all categories excluding Festivals, but transactions do not reach zero. After researching this discrepancy, the day was November 4th, 2025. I found a couple of reasons why this major dip would occur in the secondary market:
      - Major events ended: The World Series wrapped up on November 2nd, when the Dodgers beat the Blue Jays in Game 7, which marked the end of the MLB postseason. The playoffs had been a major driver of secondary ticket sales throughout October. Similarly, the Breeders' Cup (horse racing) wrapped up on the 1st, and the NASCAR Cup Series Championship finished on the 2nd
      - College Basketball season opening: over 200 games fired off the college basketball season opening day on November 3rd. However, these tickets were likely purchased months in advance by fans looking forward to go to the games instead of reselling them
      - Election Day: probably the biggest influence to the lack of ticket transactions on this day had to do with Election Day, where many people are heading to polls to cast their votes. Many either make plans to wait in line to vote either during their work shift or afterwards, which likely prevented people from looking to spend discretionary income on tickets

<img width="983" height="484" alt="image" src="https://github.com/user-attachments/assets/abe4a919-4e3a-453c-8a41-90f5b608066c" />
*Figure 3: Total active listings in each category over time*

I found that the total active listings in each category was fairly stable throughout the duration of data collection, where there was maybe a gradual decline as most events kicked up in the November, December months. I did not choose to investigate this further, but was shocked that millions of tickets are listed online just on StubHub alone. It is interesting to think how many of those are also listed on other ticketing sites, or how long the average ticket is listed on a site before it's either taken off or sold.

<img width="1180" height="584" alt="image" src="https://github.com/user-attachments/assets/75be51bb-8c29-4e29-ab89-33320a6f3a94" />
*Figure 4: The median get-in (minimum ticket price) in each category over time*

Next, I looked at how the median minimum ticket price in each category moved throughout the months of October to mid-December. The reason I chose median as opposed to average is because there were some extreme values that made interpretation difficult.

Median `get_in` prices are somewhat stable across different categories with reasonable barrier to entries. In this chart, it's clear that there are three tiers to ticket price minimums:
1. Sports have the lowest barrier to entry in the resale market around $30-$40. Sports also had the most transactions in the secondary market, which implies that many sports fan scour resale platforms for the best deals to get into different games. Also to note, huge stadiums might influence these lower prices, since these tickets are likely located in the upper decks with poor views of the action
2. The Other Events category sits in the middle in-between the high and low barrier to entry categories. This might represent the true average amount of money an individual would expect to spend to get in the doors of their chosen event
3. Concerts, Comedy, Broadway & Theater, and Festivals have the highest barriers to entry anywhere between $60-$90. These make sense since they are more unique experiences that are more rare than sporting events, where a home team could play tens of times in their home arena/stadium. In these categories, acts are likely on tour, and fans don't know the next time their favorite act will come back into town, so they are much more willing to pay a higher price
  - Festivals, interestingly enough, have the most volatility when it comes to minimum ticket prices. However, remembering back to the spread of these buckets and their events in the first place, festivals only make up 500 unique events and have the least amount of transactions and active listings per day. Therefore, these median swings are likely out of small sample sizes as shown in the following graph, where the greatest spike in median `get_in` price occurs when only 10,000 active listings live on StubHub:

<img width="983" height="484" alt="image" src="https://github.com/user-attachments/assets/b1e58ace-2695-4f29-bafa-ecf69da2975b" />
*Figure 5: A close-up at the number of active listings per day for Festivals.*

Next, I looked at the distributions of these features by each `focus_bucket`. I first tried to understand how 1-day sales volume is represented in each bucket.

<img width="1009" height="636" alt="image" src="https://github.com/user-attachments/assets/e2149fd3-cd36-4907-befd-6b924e1ac6fb" />
*Figure 6: The distribution of aggregated sales totals per day among each category*

The above boxplot shows the spread of total transactions in the resale marekt by category, showing again that StubHub is a happening place for major sports fans to both sell and buy inventory. Concerts and Other Events also have 2,000+ transactions per day on the platform. Meanwhile, Broadway & Theater, Comedy, and Festivals do not see many transactions per day on this ticketing site.

**Finally, I wanted to understand price-elasticity in my data by understanding sales volume as the event draws closer. By plotting `sales_total_1d` against a feature-engineered `days_to_event`, I was able to evaluate this relationship for a sample of events per category.**

To conclude, I want to wrap up with some high-level takeaways from my EDA to summarize what I've already learned about the data at this point:
-  Secondary ticket listings should be evaluated by their median statistics, since 1) there are small sample sizes of listings per event, which 2) can add noise to analysis by dragging up the mean `get_in` price, as I saw with Comedy for example
-  **StubHub is a focus platform for those who want to sell or buy sports tickets primarily. There is a unique transaction history of tickets as sporting events get closer to gametime**

Now, I wanted to do some feature engineering in order to continue my exploring of the data, since I wanted to know how price and demand move as the event draws closer.

## 4. Feature Engineering


### 3.1 Imputation Strategy

| Feature Type | Imputation Rule | Justification |
|--------------|----------------|---------------|
| Price features (`get_in`, `listings_median`) | Event-level median → global median | Preserves relative pricing within event lifecycle [file:6] |
| Inventory (`listings_active`) | Event-level median → 0 | Zero indicates sold out or not listed [file:6] |
| Sales (`sales_total_7d`, etc.) | Fill with 0 | Zero-inflation is domain truth (most events have no sales on most days) [file:6] |

### 3.2 Transforming Features
One of the features I created was translating the `imported_at` date to a day-of-the-week variable `dow`. This helped me understand sales volume and other price signals bucketed by these days of the week, to see if approaching weekends or middle of the weeks influenced price or demand.

<img width="791" height="384" alt="image" src="https://github.com/user-attachments/assets/f63c47b7-3254-47a3-9e99-f639684c8dcf" />
*Figure 7: A distribution of `days_to_event` by category*

This stacked bar chart helped me understand where events stood upon beginning my EDA and feature engineering steps. Around mid-December, a majority of my event snapshots stood in the month to two-month out bins, whereas the remaining 50% of events in my database lived in the month-to-go timeframe. 

This feature would help separate different price and demand trends in upcoming steps of understanding dynamics in the resale market further.

<img width="1509" height="1535" alt="image" src="https://github.com/user-attachments/assets/78d56391-c938-4360-a955-f1f47f121c85" />
*Figure 8: Boxplot showing 1-day sale totals by Day of the Week*

Demand clearly shows patterns throughout each `focus_bucket`. Where Sunday lives on the far left and Saturday on the far right, you can see a increase in most categories as the weekend approaches. Another interesting takeaway from this graphic is that Tuesday shows volatility in demand, which might be influenced by several factors among researching:
  - Tuesday is a common ticket on-sale day across the live entertainment industry for arena tours and major concert announcements. These on-sales experience lots of price and demand volatility as many rush to secure tickets
  - According to box office managers with 20+ years of experience, venues will typically release held-back inventory in the mid-week, usually landing on Tuesdays. This inventory includes production holds (tickets held back until the stage is built), sponsor allocations (corporate ticket packages not fully utilized by marketing partners get released back to the box office), and artist guest lists (unused complimentary tickets allocated to performers)
  - With most concerts occurring Thursday-Saturday, early in the week serves as a good amount of time to list inventory a full 48-72 hours before the prime time weekend plans are made. Resellers can then respond to visible demand signals by driving price up or down depending on adjacent sales

<img width="788" height="390" alt="image" src="https://github.com/user-attachments/assets/569cb212-4500-4916-8cc1-64262b9cf27f" />
*Figure 9: Median `get_in` price as the event draws closer by category*

Again, looking at the minimum ticket price for events in each category as the `event_date` draws nearer, we can see the three tiers of pricing. However, it appears that prices are somewhat stable and unaffected as time progresses. If anything, you could maybe say there is a slight decrease in the minimum ticket price, as sellers are likely dropping prices on StubHub to reduce the likelihood of unsold inventory with no salvage opportunity after the event.

<img width="979" height="484" alt="image" src="https://github.com/user-attachments/assets/f6c84d32-613c-4e46-b833-620e71bdb2ff" />
*Figure 10: Average daily sales per category by `days_to_event` bins* 

However, looking at the market volume in these categories per day as the event/performance draws near tells a unique story: StubHub is a great place to dump tickets off for sporting events, especially the week before (or day of!) the game. All other categories see a minor increase in transaction volume, and all categories see very little tickets change hands two months prior to the event.

<img width="978" height="484" alt="image" src="https://github.com/user-attachments/assets/b8b8b1fb-b643-44c9-8477-0b33d26f7f39" />
*Figure 11: Average active listings per category by `days_to_event` bins*

As most sales occur in the final week leading up to the event (for those last-minute decisions, as I often do!), surprisingly enough, the average number of listings per event drop on that final day possible. This shows the risk of putting up last-minute inventory only to see it expire without any bites. There is a unique risk-and-reward trade-off to the resale market that is a gutsy game to play.


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
