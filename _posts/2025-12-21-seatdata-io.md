---
layout: single
title: "Market-Segmented Demand Forecasting Secondary Ticket Sales"
date: 2026-01-07
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

To conclude, I want to wrap up with some high-level takeaways from my EDA to summarize what I've already learned about the data at this point:
-  **Good, full data**: The database has complete numerical statistics from 1-day sales to 1-week sales. Of course, many are low-volume events with 1-2 tickets sold, but it is nice to not have to worry about imputation of these volume statistics. Also, all categories have thousands of unique events with many snapshots, so there is both length and width in our data
-  **StubHub is a major Sports resale platform**: Stubhub appears to primarily cater towards the sports fan resale market, averaging nearly 7,000 sales per day. The major/minor sports categories are also the most volatile of all focus buckets
-  **November 4th**: Election Day likely caused the massive dip in ticket sales across the platform (and likely many other platforms). This will be interesting for future modeling to learn from, and it is good that our models will not be able to memorize patterns due to this outlier day
-  **Median will be my best friend**: Since ticket listings and prices are up to the user, initial EDA showed some fantastical ticket prices that largely influenced visuals and comparisons across focus buckets. Therefore, I decided to lean on median, which reduces the effect of outlier statistics in this project, such as a comedy show with a $900K ticket listing as the `get_in`...
-  **Pricing tiers**: I noticed there are generally three pricing tiers amongst the categories I investigated, where smaller inventory events such as Festivals or Comedies have the highest median `get_in` prices ($60-80), the Sporting events with the most inventory having the lowest median `get_in` prices ($30-40), and the Other Events category sitting somewhere in the middle.  

Now, I wanted to do some feature engineering in order to continue my exploring of the data, since I wanted to know how price and demand move as the event draws closer.

## 4. Feature Engineering

My feature engineering notebook was motivated by some initial questions I came across as I explored the data:
-  How does demand react to price amongst StubHub consumers?
-  How does price react to demand amongst sellers?
-  Is there any relationship between the `event_date` drawing closer and demand? price?

This section will explore these questions while creating new variables to help index the data and prepare my data mart for modeling.

### 4.1 Filtering the Mart

After pulling my data mart into a Python Colab notebook, I wanted to ensure that the data I grabbed only events that hadn't expired yet with `days_to_event > 0`. Most of the filtering has been performed in the EDA SQL queries and database engineering, so thankfully the data mart is prepared to get started.

### 4.2 Creating New Features
A feature I was suggested to create by Gemini 3 was the `price_spread_ratio`, which is a `SAFE_DIVIDE` of the `get_in` price and the `listings_median`. Essentially, this ratio helps us understand the relationship between the lowest and middle values of tickets per event.

A high ratio would tell us that there is similar pricing across the board for an event, whereas a lower ratio describes either a great deal or a great suspicion compared to the rest of inventory for that event. Somewhere in the middle represents the minimum ticket price for that event sitting low enough for a potential customer to pull the trigger and buy the tickets. 

Another one of the features I created was translating the `imported_at` date to a day-of-the-week variable `dow`. This helped me understand sales volume and other price signals bucketed by these days of the week, to see if approaching weekends or middle of the weeks influenced price or demand.

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

<img width="977" height="484" alt="image" src="https://github.com/user-attachments/assets/8a349c19-73b5-48b7-99c1-18b4f214dc66" />
*Figure 10: Average daily sales per category by `days_to_event` bins* 

However, looking at the market volume in these categories per day as the event/performance draws near tells a unique story: StubHub is a great place to dump tickets off for sporting events, especially the week before (or day of!) the game. All other categories see a minor increase in transaction volume, and all categories see very little tickets change hands two months prior to the event.

<img width="976" height="484" alt="image" src="https://github.com/user-attachments/assets/63565a19-0688-4182-ab1c-82034ac83cd9" />
*Figure 11: Average active listings per category by `days_to_event` bins*

As most sales occur in the final week leading up to the event (for those last-minute decisions, as I often do!), surprisingly enough, the average number of listings per event drop on that final day possible. This shows the risk of putting up last-minute inventory only to see it expire without any bites. There is a unique risk-and-reward trade-off to the resale market that is a gutsy game to play.

I also asked Claude Sonnet 4.5 for other variables that would be helpful in understanding price-elasticity in my data. The GPT suggested I do the following with my SQL query to pull from my data mart:

1) Create an `inv_per_day` variable by `SAFE_DIVIDE` the active listings and days until the event to understand how many tickets are still available relative to the days remaining, also preventing the calculation from failing if there are no more days remaining
2) Create lagged features using the `LAG()` function, which I will discuss in the next section. These features look backwards and serve as the most recent data our model will use to determine its predictions
3) Create the target variable `sales_total_7d_next` by summing 1-day sales totals beginning for tomorrow through seven days from today. This is extremely important to reduce data leakage where there could have been overlap in data the model both sees and predicts
4) Create delta calculations that observe changes in week-total sales and active listings to understand how each events' market is behaving

With that, I want to talk about why I lagged features and the intuition from my Supply Chain and Demand Forecasting course this Fall.

### 4.3 Lagging Features

This course introduced me to several demand forecasting concepts such as Naive forecasting and ARIMA modeling that all consider lagged (historical) variables. The core idea across these techniques is that the best predictor of future behavior is often recent/past behavior. Since this project focuses on predicting the next week's worth of sales, 
I needed to give my model an understanding of what happened leading up to today.

To achieve this, I lagged features. By using `t` as the current snapshot date, I can lag sales and inventory seen in the previous day with `t-1` and in the previous week with `t-7` and so on. Using SQL's `LAG` function on week-long sales totals and active listings `OVER` partitioned `event_ids`, I created columns that show the model the previous week's performance alongside the current day's stats. This allows future models to detect trends like the momentum of sales, rather than just seeing static numbers.

### 4.4 Imputing Missing Data

I decided to add the `venue_capacity` to help the model understand how available inventory influences sales relative to how much the venue can hold. 1,000 tickets available on StubHub for an NFL arena is extremely different than 1,000 available tickets for a college basketball game or concert.

However, this proved to be challenging, since just under 50% of events had missing capacities listed. I knew this variable would help our models make better predictions, so I focused on sourcing data and logical assumptions to help me fill in the gaps.

First, I used another ticket source called TouringData.org[https://touringdata.org/] to help bring in missing capacity values. This Patreon contains aggregated ticket revenue and inventory statistics for many shows and will post daily CSVs. Periodically, they will post files that contain all shows up to that point within the year, and so I relied on both their completed 2024 and 2025 documents for my missing capacities.

To do this, I mounted my Google Drive into Google Colab, defined my folder path, and read both documents into my directory using Pandas. After this, I concatenated both files and standardized venue names and cities, using these as my primary mapping keys between my SeatData.io and TouringData.org sources. This meant the usual `.str.lower()` lowercasing, `.str.strip()` removing leading and trailing whitespace, and `.fillna('')` handling missing cities or venue names. These names and cities are then placed into a `venue_capacity_map` dictionary.

Then, I created a helper function that first checks the existing data in my data mart to see if the row is missing `venue_capacity`. If there is already existing data, I skip the row. However, if the row is missing that feature, a lookup key is created with `(row['join_name'], row['join_city'])` and then searched to return the `venue_capacity` from my dictionary created from TouringData.org's documents.

Upon my first attempt, 42K capacities were imputed from the additional source. However, I was stilling missing 900K. So, I decided to introduce fuzzy matching with my key and dictionary pairs to improve this imputation. What fuzzy matching does is look for approximately similar spelled names and pair them together, instead of looking for exact matches. This includes typos, different languages, and special characters.

My `fuzzy_match_venue` function first looks only for venues within the city found in that row by using if, then logic: `if not venue or not city or city not in master_by_city: return None`. So, if I was missing Madison Square Garden's capacity, this function prevents me from accidentally matching with Madison Square Park in Georgia. Then, it collects potential candidates in a list.

The function then compares my `venue_name` against the filtered list of candidates using the `scorer=fuzz.token_set_ratio` scoring. Using NLP, this will focus on token pairings between my venues and potential candidates, where The Staples Center from SeatData.io will match Staples Center, Los Angeles" because of the shared core tokens, resulting in a nearly perfect score. And I accept only matches that are found 85% confident to prevent false positives. Finally, it will impute that venues capacity to my data.

<img width="1024" height="385" alt="image" src="https://github.com/user-attachments/assets/839ec1d1-ea1e-4048-8d0e-a77da6616162" />
*Figure 12: Conceptual design of fuzzy matching, candidates, and ranking/scoring*

This round helped me find an additional 100K venue capacities, which was great! Yet, I still had 33% of rows with missing venue data and no more additional sources to duplicate this strategy, since APIs I looked into did not share this data with rate limits I needed for my scope.

So, secondary to my data aggregating strategy, I decided to use logical imputation to impute the remaining capacities. The following are assumptions I made after researching conservative average venue sizes:

| Venue Type      | Estimated Average Capacity |
|-----------------|----------------------------|
| Stadium         | 60000                      |
| Arena           | 15000                      |
| Amphitheater    | 10000                      |
| Theater/Theatre | 2500                       |
| Ballroom        | 1500                       |
| Club            | 500                        |
| Cafe            | 150                        |
| Bar             | 100                        |

After creating this dictionary, I performed the same imputing strategy with *exact* pairings in both the `venue_name` and the `event_name`, since some event titles included the location of the performance. This strategy brought me down to now 25% of rows missing their `venue_capacity`, and I knew I was in the home stretch.

So, finally, I decided to conditionally impute the remaining missing values with the median `venue_capacity` of that focus bucket. Doing this would not misrepresent the data's middle values for this variable, and assumed that the remaining Festivals, for example, had similar capacities to the rest of the festivals in my data. This was an aggressive assumption looking back on it, but I would need the complete variable for later modeling and wanted to be as fair as possible.

After double-checking my now-filled `venue_capacity` distribution, I found some extreme outliers, such as Dickies Arena having a 240K capacity(???), so after correcting this figure to its estimated 14K figure, I was able to investigate the distribution of capacities:

<img width="551" height="428" alt="image" src="https://github.com/user-attachments/assets/bfe97fb8-4789-4c2b-bd9a-2f56ae12a2b7" />
*Figure 13: Distribution of the `venue_capacity` variable after imputation*

Extremely right-skewed data, where there are still some extreme values for motorsports, and many venues holding no more than 2,500ish people. This tailed distribution would become a familiar sight as I looked at specific variables, and the `np.log1p` function would become a best friend as I prepared the data for modeling.

### 4.5 Transforming Variables

This log function is not simply the natural log, but it includes a safety net. It calculates $$ln(1+x)$$. We need this because our data contains zeroes. Taking the log of a zero results in an undefined value, so this error handling helps the `np.log1p(0)` become just 0, preventing our model from crashing.

<img width="578" height="413" alt="image" src="https://github.com/user-attachments/assets/0d9ca6be-44ad-4501-b308-8b05f2e2082f" />
*Figure 14: Distribution of `venue_capacity_log` variable after imputation*

This distribution is much closer to normal and will be better for our models to use in predicting, instead of associating outlier capacities with the same week-long sales total since there aren't enough samples.

The `sales_total_7d_next` variable had a similar problem:

<img width="556" height="428" alt="image" src="https://github.com/user-attachments/assets/5559fd2b-b7f5-4a31-9d6e-42b653e1f0c1" />
*Figure 15: Distribution of `sales_total_7d_next`*

And I got to see the `np.log1p` error handling play out in this case, where many records have no transactions within a weeks' time:

<img width="547" height="428" alt="image" src="https://github.com/user-attachments/assets/7bc9c0f2-1628-4da9-87ec-70f4d2bd1129" />
*Figure 16: Distribution of `sales_total_7d_next_log`*

With this large discrepancy in total events with no ticket transactions in the following week and some, this could become a classification problem in its own right, predicting if any sales will occur in the next week for a show. GPT suggested that I add this layer on top of my demand forecasting prediction project, essentially answering:

1) Will there be any sales in the next week for this event? (Classification)
2) If so, how many? (Prediction)

So, I created the binary variable `any_sales_7d_next` and understood the class weights to be around 60% of events with no sales in the next week and 40% with at least one sale in the next week. 

I then log-transformed other volume and price featuers in the dataset, such as `sales_total_7d`, `get_in`, `listings_median`, and `listings_active` since their distributions also showed heavy right-skews.

Finally, I took the `dow` (day-of-week) variable and created the binary `event_weekend` feature that recognizes either the 6th or 7th (...) day as the weekend, marking Friday and Saturday nights. These are very popular nights for events where people can afford a late night at a concert or sports game without penalty to waking up early the following morning.

### 4.6 Remaining NaNs

Lastly, I evaluated the missingness of my data and summarize below my thought process for the final remaining missing features:

| Variable                    | Percentage Missing | Imputation Strategy                                                                                                                                                                                            |
|-----------------------------|--------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `listings_median`           | 10%                | First attempted to impute with the median of that event by `event_id_stubhub`. If all NaNs for that event, imputing with the global median listing value. Cannot afford 0s which would create undefined ratios |
| `listings_median_log`       | 10%                | Same applies as above                                                                                                                                                                                          |
| `price_spread_ratio`        | 10%                | Lastly recalculated with the missing `listing_median` values                                                                                                                                                   |
| `listings_active_prev`      | 5%                 | NaNs likely because these rows are the very first record. So using today's value as yesterdays in backfill                                                                                                     |
| `listings_active_change_7d` | 5%                 | As per above, the delta value becomes zero                                                                                                                                                                     |
| `sales_total_change_7d`     | 3%                 | As per `listings_active_prev` situation, followed similar logic                                                                                                                                                |
| `sales_total_7d_prev`       | 3%                 | As per `listings_active_prev` situation, followed similar logic                                                                                                                                                |
| `inv_per_day`               | 2%                 | Recalculated after imputing `listings_active` feature                                                                                                                                                          |
| `listings_active`           | 2%                 | Assuming that missing values actually mean 0 active listings                                                                                                                                                   |
| `listings_active_log`       | 2%                 | After imputing `listings_active`, using `.clip(lower=1)` if `days_to_event` is small or 0 to prevent undefined calculations                                                                                    |

After this, my data had no more missing values and I was finally ready to push this back to BigQuery and begin modeling. 

Some takeaways from this section:
-  **Filled Venue Capacity is Context**: My model understanding that 100 ticket sales in a 500-person club signals a viral event whereas those 100 sales in a stadium event is nothing at all. Future models will now be able to tell this apart after the imputation on `venue_capacity`, which was missing nearly half of entries
-  **Solving Sparsity**: Sales numbers in my data is extremely sparse, with many days having zero transactions. Both by log-transforming these sales figures and splitting up the target into a classification and regression problem, I've created a modeling strategy that won't be overwhelmed by zeros
-  **Lagging Features**: The idea of giving my later models a memory of the previous week will hopefully benefit predictions by giving prediction models more access to historical data, such as the previous week. Now, a model can understand momentum for an event and adjust predictions accordingly, rather than simply seeing today's sales volume

---

## 5. Modeling

Now with my understanding of StubHub's secondary ticket transaction data and my feature engineered variables, I'm ready to move onto the ML piece to answer two primary questions:

1) **Classification**: Are there any sales in the next week for this event?
2) **Regression**: If I predict yes, how many sales will occur in the next week for this event?

So, I began with setting up my variables with dummy coding, train and test splits, and deciding which modeling algorithms I wanted to use based on previous coursework and experimentation.

*It's important to note, this first round of modeling did not facet by `focus_bucket`. I chose to investigate if modeling all of the data (with dummy coding) universally would result in tight predictions.*

### 5.1 Dummy Coding

Dummy variables separate columns into categorical variables with buckets as columns, with k-1 columns. So, trading my `days_to_event` numerical data into bins using Pandas' `.get(dummies)` function helped me represent my events in six possible buckets, ranging from one week span to three-week span and beyond.

### 5.2 Building X and y

Next, I wanted to build my X and y variables to easily pass through my models. X would include any column in my data that did not include the target variable or any leakage variables (`any_sales_7d_next`, `sales_total_7d_next_log`). This also includes string variables like `venue_name` and `event_id_stubhub`, where a model could potentially just memorize that The Moody Center will always have high sales volume. So we want to get these identifiers out.

### 5.3 Train/Test Splits

Any normal ML project would consider around 70/20/10 train, test, and validation splits for their data. However, doing so would jumble around different dates for our events, possibly trying to predict previous dates sandwiched between training dates, and some events would totally be excluded in testing! This will not work for time-series data, and so I took a different approach.

<img width="1344" height="960" alt="image" src="https://github.com/user-attachments/assets/ccc2b491-fd4b-4a66-a523-8602a4e78a17" />
*Figure 17: An example of train/test split with time-series data*

Instead, I had to define a cutoff date that my training cannot see beyond, thus using the unseen days as the test set. I decided to use the last two weeks of data for my events as the test set by converting the `snapshot_date` with `.to_datetime` and creating the cutoff date with `model_data['snapshot_date`].max() - pd.Timedelta(days=14)`. Then, I separated training data (`<= cutoff_date`) from testing (`> cutoff_date`). To further prevent any data leakage, I also dropped `snapshot_date` at this point, while also some modeling methods would require inputs as floats and not date formats.

Next, I had separate my y outputs in the classification and regression problems, since classification problems are trying to predict a binary 0/1 outcome and regression problems are trying to predict the number of (log) ticket sales for the following week, assuming there will be!

I did this by first defining `y_class` as only the `any_sales_7d_next` column in my data (both 0 and 1 values). Then, `y_reg` would become the locations (`.loc`) where there are sales in the next week (`model_data[any_sales_7d_next] == 1`) and only the `sales_total_7d_next_log` value in that row. Same locations, different output to predict. X would follow a similar method, where X_reg is only the locations where there are sales in the next week, and includes all our feature columns. 

Then I defined my train and test X and y feature spaces according to each problem. `X_train_c` would include my feature columns before the cutoff date (as would `X_train_r` for regression). `X_test_c` would include the feature space after the cutoff date. `y_train_c` included the `any_sales_7d_next` values before the cutoff date, and `y_test_c` would have the records after those two weeks held out for testing. I did the same thing with my regression train/test split, however the prediction output would be different, as I discussed earlier. Same locations, different target outputs.

### 5.4 Model Selections

Now, the fun part. I began to decide which models I wanted to try for both problems, classification and regression. 

Up to this point, I knew my data was both wide and long, with many variable types. This was telling for tree-based learning, which is efficient and fast with this type of data. However, in my courses I have also been learning and experimenting with models such as Naive and Neural Networks, so I wanted to try these out as well and compare, in the end, which model performed the best for this specific data. 

Also, I had to consider and predict which models would be best for which data problem, since I had split this up into both classification and regression. Except for Naive, which could only predict outputs, the remaining models I tried were able to attempt both problems with the same input feature space, which simplified my decision beforehand.

Now, I will begin detailing how I built each model and the inspiration behind trying these methods.

### 5.5 Naive

My Naive model became my baseline predictor. I learned about Naive modeling in my Supply Chain and Demand Forecasting course this Fall, and the method essentially assumes that the best predictor of tomorrow's demand is today's demand. Naive assumes no volatility, which some focus buckets did have. However, this initial modeling notebook sought out to predict using the model against all `focus_buckets`, so while Theater/Broadway and Festivals, with low and constant sales volumes, might have low errors, Sports categories would suffer from this method conceptually.

To build this model, I could simply take the previous value as my prediction for the next value with `y_pred_naive` as `X_test_r.iloc[:, list(X_reg.columns).index("sales_total_7d_log")]`. This takes the test features (of X) and finds the column that holds the current `sales_total_7d_next_log` and returns that value as the prediction.

The reason this model is my baseline predictor is because, if other models cannot outperform a model that is a lagged value behind, then it is not worth looking at any further. Naive predictions will always chase the true value, in this case by one week distance. We're looking for better predictions!

### 5.6 Tree-Based Models

GPTs love to suggest tree-based models like Gradient Boosting (GB), XGBoost, and Light GBM. They're the fastest and somewhat effective techniques that don't require much data munging, and they can handle both classification and regression cases. I was also encouraged by Claude Sonnet 4.5 to try these out, but first want to explain what tree-based learning is at a super high level.

Regular decision trees is the most basic form of these models. Trees essentially split data based on a filtering question, such as "Is this event a Major Sport?" or "Is the price greater than or equal to $45?". Decision trees are easy to interpret, but prone to overfitting data, memorizing patterns of training data and struggling to predict/generalize new records. 

<img width="640" height="480" alt="image" src="https://github.com/user-attachments/assets/0becc4c0-17c6-49bf-847a-15e391d819d9" />

*Figure 18: A single decision tree example*

Gradient Boosting attempts to fix the overfitting problem by creating many trees instead of just one. This is also a sequential training method, where each tree is predicting the error of the previous tree. By the time all trees are summed up, the model is able to capture more because each tree covers the mistakes of the one before it.

<img width="617" height="337" alt="image" src="https://github.com/user-attachments/assets/3310e6a7-4261-4cf1-9994-e206b8fa8db9" />

*Figure 19: An example of sequential gradient boosting trees*

XGBoost and LightGBM introduce some tailored advantages on top of Gradient Boosting. XGBoost contains regularization, which penalizes trees that get too complex (approaching overfitting and memorization) and is able to handle missing values or zeros. LightGBM is designed for massive datasets and grows its trees vertically, as opposed to XGBoost's horizontal growth. LightGBM focuses only on the leaf with the highest error and ignores other leaves. These two methods speed up training significantly and use less computational energy. 

<img width="756" height="287" alt="image" src="https://github.com/user-attachments/assets/f1835955-edd3-4db0-b8d4-b5051d6460bb" />
*Figure 20: Horizontal (XGBoost) vs. Vertical (LightGBM) decision tree training*

These tree-based models can handle both classification and prediction problems, and I eventually chose to fit each method in each scenario.
Sklearn contains the packages for these tree-based models, and so I used `GradientBoostingClassifier.fit()`, `XGBClassifier().fit`, and `LGBMClassifier.fit()` on both `X_train_c` and `y_train_c` (and their Regressor, X_train_r and y_train_r counterparts). 

#### Hyperparameters

These tree-based models also had the option of defining hyperparameters when training. Hyperparameters are the options you can define in a machine learning algorithm before you start training. 

In my case, I decided to fit the base Gradient Boosting model to our data, and then evaluate a set of hyperparamters with XGBoost and LightGBM to compare performances. These hyperparameters were suggested by Gemini 3, but I want to briefly explain how they work and what I learned after looking into each option:

-  `objective`: This defines the output space of a tree-based model
    -  `'binary:logistic'`: Used for Classifiers to output a probability between 0 and 1, similar to Logistic Regression
    -  `'reg:squarederror'`: Used for Regressors to minimize the squared difference between the predicted sales and actual sales, in this case
-  `eval_metric`: In ML, the goal of any model is to minimize a loss function. This option tells our tree models what to minimize when training
    -  `'auc'`: the Area Under the Curve is used in Classification problems. This measures how well my model can distinguish between no sales and some sales, where 0.5 is a random guess, and 1 is perfect
    -  `'rmse'`: Root Mean Squared Error is used for my regressors, determining how far off residuals are. This measure keeps my error in the same units as my target variable and helps me later on with interpreting results
-  `tree_method = 'hist'`: To speed up training, I was suggested to used this 'histogram-based' method, which groups values into bins before finding the best split, rather than searching every unique value in my data
-  `n_estimators = 400`: Here I defined both the XGBoost and LightGBM to build 400 sequential trees
-  `max_depth = 4`: This hyperparameter limits the maximum number of splits within each tree. Keeping this number low prevents overfitting
-  `learning_rate = 0.05`: A learning rate helps dilute the influence of the current tree on the final outcome. Learning rates usually stay between 0.1-0.001 and help models generalize better by making many more trees, in this scenario
-  `subsample` and `colsample_by_tree`: Both of these settings simulate a randomization of my data. The `subsample` setting allows me to define the percentage of events my trees are allowed to see in training, while `colsample_by_tree` can define how many feature columns each tree is allowed to see
    -  Doing this also aims to prevent overfitting and forces each tree to predict based on different data than the previous trees. By the end of training, the hope is that the overall model can generalize on the test set after seeing different variations of training data
 
#### Hyperparameter Search

With that, GPT also introduced me to what it called a 'grid search'. By defining a list of different hyperparameter settings, like three learning rates I'd like to test, I can run a search between those values to find the settings where our loss function is minimized. 

I decided to attempt this search with my XGBoost Classifier and Regressor, calling these "tuned" variants, since these were the fastest to train on my data. However, running this full Grid Search would be computationally heavy for my scope, which included 6 options for `n_estimators`, 5 options each for `max_depth`, `learning_rate`, and 4 options for `subsample` and `colsample_by_tree`. This results in 2,400 unique combinations, which would be too ridiculous to train just for a portfolio project.

Instead, I used RandomizedSearchCV. This method won't check every single intersection of my hyperparameter list, but gives me the knobs to tell my search when to stop.

<img width="1088" height="588" alt="image" src="https://github.com/user-attachments/assets/bac15c61-bc7e-44ed-9506-6e92525c5c42" />
*Figure 21: Conceptual idea behind Grid Search (a) and Random Search (b)*

Specifically, I set `n_iter=50`, which asks the algorithm to randomly select only 50 unique combinations. I also implemented cross-validation with three folds during this search. So, for each of the 50 combinations, an XGBoost was trained on three separate slices of my data, so that each combo of hyperparameters sees new data each time to prevent lucky draws.

Now, I'd like to introduce the next model I selected that I thought might be more challenging and fun to try on this data.

### 5.7 Neural Network

In my Advanced Machine Learning and Optimization courses this Fall, we have been learning about Neural Nets, models that train weights and biases in a structure not too distant from the human brain, and use a concept called Gradient Descent in minimizing the loss function. 

<img width="1318" height="862" alt="image" src="https://github.com/user-attachments/assets/27c096cf-36d8-44a6-9f7d-de49c4d34b03" />
*Figure 22: A simplified diagram of Neural Network structure*

Neural Networks are great in that they can also be used in classification and regression problems and are able to find minima of very complicated loss function landscapes. Honestly, I wanted more practice with building one with this data, and thought it would be a great opportunity to try out. 

#### Preparing Data

This model cannot take the same inputs as tree-based learning, though. Trees make splits on features regardless of their ranges, but Neural Nets are distorted if features are not scaled down. If Gradient Descent is similar to trying to find the lowest point in a valley, data that is not scaled confuses our model's descent, where one step in the `get_in` price is a small increment, and another step in the `listings_active` feature could be a large distance. So, before starting to build, I had to scale my X input features with sklearn.preprocessing to be consistent. 

<img width="686" height="386" alt="image" src="https://github.com/user-attachments/assets/e54c7318-9515-4b7f-bf95-e0eabb9aa6c0" />
*Figure 23: A visual example of Gradient Descent*

To fix this, I used sklearn's StandardScaler, which implements a Z-score normalization, with mean 0 and standard deviation of 1, to transform my data so every feature became normalized. 

During this prcoess, I learned that there was a major opportunity for data leakage between training and testing data. If I scaled both train and testing data at one, my training data would be influenced by the mean and variance of the future (test data). So, I used `.fit_transform()` for my training data only, which first calculated mean and standard deviation before transforming, to simulate what the model would know up to that point. Then I used `.transform()` on my test data, applying the training set's rules to my test set. 

Now, I was ready to move on to building the framework of these Neural Networks.

#### Architecture

Neural Networks can be as shallow or deep as you'd like, considering balancing bias and variance, overfitting, the input feature space, and the problem type. That is why this step is really important. Setting up hidden layers in a way that encourages the model to learn but not memorize is the entire trick that I've learned so far in fitting Neural Nets. 

Using tensorflow, I wanted to play around with different combinations of hidden layers, neuron counts, activation functions, and other techniques suggested to me by Claude. Below is the architecture I landed on for both my classification and regression networks with some explanation of terms.

<img width="736" height="393" alt="image" src="https://github.com/user-attachments/assets/b416d0e8-2840-4b6b-835c-15744aa83001" />
*Figure 24: My Feed-Forward Neural Network architecture used for classification and regression*

My Neural Network for regression included a third hidden layer with 32 neurons, and between my classification and regression output neurons, I used different activation functions to get my desired target output. Here are some more options I landed on after tinkering and trying again new architectures:

-  `activation=`: this allows me to define activation functions, which introduces nonlinearity to model learning to handle complex patterns in my data, and then passing to the next layer
    -  I used three different activation functions in these two Neural Networks, two of which are familiar (`'sigmoid'` on the output layer during Classification, and `'linear'` to output a prediction on sales in my Regressor) and one which is new, `'relu'`
    -  ReLU helps avoid vanishing gradients by outputing the input if positive and outputing zero if negative. I used this activation function in each hidden layer
-  `regularizers.l2`: introduces regularization into hidden layers, and specifically, ridge regression, which prevents any single neuron from having too much influence and forcing the model to look at all the features rather than just one. Ridge regression decays weights of neurons towards zero, as opposed to Lasso which forces weights to zero, all added to the loss function as a penalty
-  `layers.BatchNormalization()`: between each layer I normalized gradients to prevent either vanishing/exploding gradients, which helps the Neural Net converge faster

#### Compiling Models

Then, I complied these models using `tf.keras.optimizers.Adam()`, which is a learning rate optimization method that automates the step size of our model's gradient descent. I didn't want my model to get stuck in a shallow valley (local minima), so Adam is able to adapta learning rate with the concept of momentum, taking larger steps and smaller steps in succession.

I also defined each loss function for my classifier and regressor in this step. My Classification problem used `loss='binary_crossentropy'`, since the output is a probability that there will be any sales in the next week between 0 and 1. This loss function penalizes the model for predicting a high probability for an event with no actual sales. For Regression I was suggested to use Huber Loss, which is a new concept to me that I had to investigate before using.

<img width="892" height="669" alt="image" src="https://github.com/user-attachments/assets/1852070b-534c-4776-9a38-8a39425c4709" />
*Figure 25: The Huber loss function*

Huber Loss helps specifically with long right tails and outliers, which my sales target had. The graph above shows how Huber Loss treats small errors like MSE and large errors like MAE. I defined a threshold at 0.75 where the Huber Loss function would flip from MSE to MAE using `tf.keras.losses.Huber(delta=0.75)`. 

Finally, I wanted to standardize the metrics I use to compare these Neural Nets against my trees and Naive models, so I defined metrics for these models to log while training and stored them in the tensorflow models. Classification stored both `'auc'` and `'pr_auc'`, while Regression logged the `'mse'` that would later be used to calculate RMSE.

#### Training Options

Fitting Neural Networks require some final definitions, like how long I'd want to train for, the size of data I want my model to see, and how to handle validation data. 

Here is where I pass through my `X_train_c_scaled` (and r_scaled) and `y_train_c.astype('float32')` (and regression counterpart). I had landed on this data type because Tensorflow and Keras are built to run on this data type, which saved me from TypeErrors during training. I also defined my `validation_data` with `X_test` and `y_test` for each model. 

Then, I told my Neural Net the dimensions of training I wanted. This included 300 epochs, which represent a complete pass through the dataset, and a batch size of 2,048, which tells our Neural Net how many rows of data to look at before updating weights.

Now, hitting "go" on these Neural Networks now would run training until all 300 epochs are complete, likely leading to overfitting. So I needed to setup some guardrails that balanced underfitting and overfitting this data.

A **Learning Rate Schedule** works with my Adam optimizer. Using `ReduceLROnPlateau` helps my Gradient Descent by not overshooting valleys with too-large of steps, but gradually decreasing steps as it observes the validation metric, in this case, maximizing `val_auc` for Classification and minimizing `val_mse` for Regression. I've also defined a minimum learning rate these schedules can reach at 1e-4, and with `patience` can tell the model how to decrease the learning rate `factor` after my choice of epochs (passes through my data). 

<img width="1034" height="388" alt="image" src="https://github.com/user-attachments/assets/f2df722b-9d4d-426f-b98b-d9954e686b49" />
*Figure 26: Learning Rate relative to finding minima*

**Early Stopping** is another method I used to immediately stop training once I recognize any overfitting. By keeping an eye on my model's `'val_auc'` or `'val_mse'` I can stop training my Neural Network once I see this begin to gradually decline. I decided that, after 20 epochs, if these metrics were to decline/incline respectively, I would `restore_best_weights` of the epoch that minimized each question's loss function, and quit training on my data.

<img width="800" height="450" alt="image" src="https://github.com/user-attachments/assets/682aeff4-a724-477c-a8b0-2a619aadee27" />
*Figure 27: Early Stopping visualized to prevent overfitting*

Altogether, I was able to train my Neural Networks and find their predictions using the `.ravel()` function, which reshapes the output into a one-dimensional array (where before, it output as a tuble in the shape n_samples, 1). This would prepare my predictions for the `np.sqrt(mean_squared_error())` of my actual and predicted values, aligning my metrics for comparison.


### 5.8 Naive + Neural Network

I also got ambitious to combine both the Naive logic with Neural Network predictions. Since the Naive model (assuming next week's sales equals this week's sales) was already my baseline, I wanted to investigate if it would be more efficient to have my Neural Network learn instead upon the changes between each week.

$$
\hat{y} = x_{\text{naive}} + f_\theta(x)
$$

Where $$x_{\text{naive}}$$ is current 7‑day log sales and $$f_\theta(x)$$ is the Neural Net’s learned correction (delta) to adjust the Naive guess.

<img width="1200" height="700" alt="image" src="https://github.com/user-attachments/assets/eafa53e4-1f0c-42c1-a1f6-dfb538a75270" />
*Figure 28: Naive + Neural Network architecture visualized*

All this changed in my Regression Neural Network was including this naive term and, instead of predicting the sales for the next week, predicting the change in this week's sales to next, while adding that Naive term to the output layer. This is called a skip connection, which creates a path that bypasses dense hidden layers to carry that Naive term directly to the end.

In code, I was able to find the Naive term with a Lambda layer (`layers.Lambda()`) with the index of the naive term. This allowed me to hold onto that value before starting training. Then, merging the output layer with my Naive term using `layers.Add()`, I converge both paths together in my architecture and began training with the same options as before.

Finally, it was time to evaluate my results.

### 5.9 Performances

To fairly compare all my models, I evaluated them in two ways: their ability to classify if an event would sell at all (AUC) and their accuracy in predicting the number of tickets sold in the following week (RMSE). 

**Classification**

| Model              | AUC      | PR       |
|--------------------|----------|----------|
| **Neural Network** | 0.919900 | 0.806871 |
| Light GBM          | 0.919481 | 0.807930 |
| XGBoost            | 0.919468 | 0.807311 |
| GradientBoosting   | 0.917353 | 0.804151 |
| Tuned XGBoost      | 0.914157 | 0.799772 |

In this classification scenario, deep learning with my Neural Network performed the best with the highest AUC (0.919900), which balances the true positive rate from false positive rate. Essentially, there is a 92% probability that the Neural Net will rank an event with any sales higher than a non-selling event. This suggests there are some non-linear signals in my feature space, such as interactions between terms, that determine which events will/won't sell any tickets on StubHub. 

<img width="691" height="547" alt="image" src="https://github.com/user-attachments/assets/72aedf02-5dc5-4b46-878f-0894e825d8fc" />
*Figure 29: Comparing models using the ROC Curve*

**Regression**

| Model                  | RMSE (in Tickets)     | MAE (in Tickets) |
|------------------------|----------|----------|
| **XG Boost**     | 17.667931 | 5.518347 |
| Light GBM | 17.868582 | 5.549856 |
| Naive + Neural Net                | 18.039503 | 5.534035 |
| GradientBoosting              | 18.183927 | 5.655028 |
| Tuned XGBoost       | 18.249732 | 5.676055 |
| Neural Net          | 18.732760 | 5.623084 |
| Naive                  | 161.112980 | 87.988088 |

To convert RMSE values back into ticket-scale, I used the `np.expm1()` function on each model's predictions. Then, to calculate RMSE, I took the `np.sqrt()` of the `mean_squared_error()` between the actual tickets and predictions of each model. Finally, MAE only required this `mean_squared_error()` calculation on the actual and predicted values. 

To put these errors into context, my Naive Baseline (predicting the same sales as last week) is off by an average of 88 tickets per day. In contrast, the XGBoost model reduces this error to just 5.5 tickets per day. This massive reduction in residuals transforms the prediction from a rough guess into a precise prediction tool that departments can use to make better decisions.

When looking at Root Mean Squared Error (RMSE), the gap widens. Because RMSE squares the errors, it penalizes outliers heavily. The fact that XGBoost's RMSE (~17.7) is roughly 3x its MAE (~5.5) suggests that while the model is precise on average, it still faces challenges with events that spike unexpectedly in ticket sales. However, even with these outliers, it provides a reliable improvement over the delayed reaction of the Naive method.

However, I think we can break down these residuals to get an even better idea on each bucket's resale ticket movement.

#### Per-Bucket Error (in Tickets)

Next, I broke down these errors by `focus_bucket`. The results show a clear difference between stable and volatile markets.

| Focus Bucket       | RMSE (in Tickets) | MAE (in Tickets) |
|--------------------|-------------------|------------------|
| Broadway & Theater | 5.54              | 1.96             |
| Festivals          | 6.13              | 3.16             |
| Comedy             | 13.65             | 5.90             |
| Other              | 16.39             | 4.16             |
| Concert            | 16.60             | 5.38             |
| Major Sports       | 26.21             | 11.36            |
| Minor/Other Sports | 29.04             | 9.64             |

The comparison across different categories show that Major and Minor sports are the hardest to get right, with an average absolute error of 11 and 10 tickets off for the true ticket sales of the following week. Also, these errors are more volatile, shown by their RMSE values, which penalizes larger misses, as I talked about before. Broadway & Theater and Festivals have the most precise predictions using the tree-based regressor in XGBoost, suggesting these are more stable markets and easier to predict within a reasonable range.

<img width="1189" height="590" alt="image" src="https://github.com/user-attachments/assets/77778194-97d6-42c3-910e-ae1617ef0214" />
*Figure 30: MAE comparison across categories*

#### Per `days_to_event` Bins

Finally, I evaluated how the error changes as the event gets closer.

| `days_to_event` Bin | RMSE (in Tickets) | MAE (in Tickets) |
|---------------------|-------------------|------------------|
| 60+                 | 5.94              | 2.35             |
| 31-60               | 7.83              | 3.26             |
| 15-30               | 22.86             | 7.34             |
| 8-14                | 23.50             | 8.14             |
| 1-7                 | 22.70             | 7.66             |

The results align with my logic. It's far easier to predict next week's sales the further out from the event, since there is little movement in the resale market. However, as I saw in my EDA, many ticket transactions happen in the two weeks approaching the event, which is where most of the XGBoost's prediction error falls in. However, a prediction error of roughly 8 tickets off per day in those two weeks still beats out a Naive guess, which is what will help other departments make better decisions when it comes to a final marketing push, for example.

My takeaways up to this point:
-  one
-  two
-  ...

After understanding these error distributions and groups of thought by categories of events and timelines leading up to showtime, I thought I could find even more improvement by individually fitting the best classifiers and regressors to each focus bucket, aligning with a more market-segmented modeling approach.

---

## 6. Market-Segmented Models

At a high level, in this section I chose to fit all tree-based, Neural Networks, and Naive models for both Classification and Regression to each DataFrame of event categories. For example, all models will be fit to Comedy events, where I still keep my same train/test split logic and holding out the 14 days leading up to the event. Then, by comparing the same metrics as before, I found which model works best for the specific category while trying to make small wins in reducing the distribution of errors.

### 6.1 My Intuition

The difference between what I've already done and what I'm setting out to do is based on conditional probability. My first attempt at a Universal predictor included both classification and regression problems, but didn't combine them in the final product, effectively estimating sales and probability of sales in the next week separately. With this next method, I want to introduce conditional probability while finding each `focus_bucket's` best predictor and classifier.

$$E[\text{# Sales}] = P(\text{Any Sale}) \times E[\text{# Sales} | \text{Any Sale}]$$

This method simulates a better understanding of probabilities and real-time data known while making these decisions. Finding the estimated value of sales isn't just a hard guess but weighted by its probability there will be any sales in the first place.

### 6.2 How I Built the Pipeline (code-heavy)

This method required a complex Python loop that I benefited from using Gemini 3 to build. It acts more as an ML pipeline than a simple script before where I ran each model separately. I'll break it down into four phases.

#### Preprocessing the Data

Same as before, I needed to prepare my training and testing data before building my models. With the same cutoff date and logic as before, I split up my data with the 14 days held out for testing. I also excluded features that contributed to data leakage as I did previously. 

Then, I implemented a for loop that iterates through each `focus_bucket` to isolate preprocessing. In each bucket I performed the following steps:
-  Created a dummy column called `bucket_col` that targets the current `focus_bucket`, resulting in a 1 if the string `f"focus_bucket_{bucket}"` matches the current `focus_bucket` in my iteration list
-  Filtered both `train_df` and `test_df` to only include event rows where `bucket_col` is an exact match (1)
-  Filtered these dataframes for regression to only include rows in my data where there are sales (`'any_sales_7d_next' == 1`)
    -  Only my training data will be modeled on this non-zero data, while my predictions will have to both classify and regress, using the conditional probabilities I discussed earlier
-  Create each problem's training and testing (X and y) data
-  Store these index locations for later visualizations

After all my training and testing data is prepared, I redefined my previous hyperparamter grid search dictionary, learning rate schedule for both classification and regression, early stopping for both problems, and defined functions with the same architecture for my Neural Nets to save me for the next beast of a for loop.

#### Model Training

In the largest for loop I have yet to build, I began to model this data, this time with two loops! I first created empty dictionaries to hold my results, run histories, best-performing model names for each bucket, and lists for my predictions and residuals that I'd use later for visualizations.

My outer loop consisted of my `focus_buckets`, as I defined which data I wanted to model on, scaled my data yet again with `StandardScaler()`, and used `.fit_transform()` on my training data and `.transform()` on my testing data. Then, I began with classification models, creating a list for results and a dictionary to hold the metrics for evaluating winning models. Then, for each model, I had a for loop that did the following for each method:
-  **Gradient Boosting**: Used the `GradientBoostingClassifier()` function with a random state using my classification training data
-  **XGBoost**: As with Gradient Boosting, using the `XGBClassifier()` function on my training data
-  ***Light GBM**: One more time, using the `LGBMClassifier()` function on my training data with the default hyperparameter settings
-  **Neural Network**: Used my predefined functions with my architecture to pass through my scaled classification training data (this time, only running for 100 epochs), again casting my `any_sales_7d_next` variable with `.astype('float32')` for probabilities, saving my run history, and raveling my probabilities
-  **Tuned XGBoost**: Ran the `RandomizedSearchCV()` between my `param_dist` dictionary for hyperparameter tuning with my objective as `binary:logistic`, fitting my classification training data with the best hyperparameter setup

After my classification setups, I saved these results in my dictionary for later comparison, saving each model name, `auc` score, and `pr` score.

Then, still within each model for loop, I immediately ran the regression script after creating another list for results and a dictionary to hold those metrics, this time for my prediction error terms. In the same fashion as before, here is how I tackled the regression piece in this for loop:
-  **Gradient Boosting**: Used the `GradientBoostingClassifier()` function with a random state using my regression training data
-  **XGBoost**: As with Gradient Boosting, using the `XGBClassifier()` function on my training data
-  ***Light GBM**: The `LGBMClassifier()` function on my training data with the default hyperparameter settings
-  **Neural Network**: Used my predefined functions with my architecture to pass through my scaled regression training data (this time, only running for 100 epochs), again casting my `sales_total_7d_next_log` variable with `.astype('float32')` for predictions, saving my run history, and raveling my predictions
-  **Tuned XGBoost**: Ran the `RandomizedSearchCV()` between my `param_dist` dictionary for hyperparameter tuning with my objective as `reg:squarederror`, fitting my regression training data with the best hyperparameter setup

For later visualizations, I also appended each run's bucket name, model name, actual sales (log), predicted sales (log), and residuals in a dictionary. Saving the RMSEs in another regression dictionary, I then closed the model loop, storing each problem's results for each bucket in another dictionary.

Lastly, I had the for loop find the best model for each bucket by maximizing the `auc` and `rmse` scores that were stored from each run while generating predictions on the full test set, including both inactive and actively reselling events using the conditional probability logic. When classification probabilities were greater than 0.5, I chose to set that as the threshold that differentiated a dead event from an active one.

### 6.2 Comparison to Global Models

Finally, I was able to look at these performances across both classification and regression problems to see if this hypothesis was worth the rabbit hole.

| Modeling Type   | RMSE (in Tickets) | MAE (in Tickets) |
|-----------------|-------------------|------------------|
| Universal       | 17.67             | 5.52             |
| Market-Specific | 9.94              | 1.83             |

### 6.3 Market-Segmented Performances

| `focus_bucket`     | RMSE (in Tickets) | MAE (in Tickets) |
|--------------------|-------------------|------------------|
| Broadway & Theater | 3.31              | 2.34             |
| Festivals          | 4.95              | 3.49             |
| Comedy             | 7.69              | 5.91             |
| Other              | 8.36              | 4.41             |
| Concert            | 10.52             | 5.55             |
| Minor/Other Sports | 17.17             | 9.04             |
| Major Sports       | 21.64             | 11.49            |

My takeaways from this experiment: 
-  one
-  two
-  ...

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
