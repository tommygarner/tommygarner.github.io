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
*Figure 12: Distribution of the `venue_capacity` variable after imputation*

Extremely right-skewed data, where there are still some extreme values for motorsports, and many venues holding no more than 2,500ish people. This tailed distribution would become a familiar sight as I looked at specific variables, and the `np.log1p` function would become a best friend as I prepared the data for modeling.

### 4.5 Transforming Variables

This log function is not simply the natural log, but it includes a safety net. It calculates $$ln(1+x)$$. We need this because our data contains zeroes. Taking the log of a zero results in an undefined value, so this error handling helps the `np.log1p(0)` become just 0, preventing our model from crashing.

<img width="578" height="413" alt="image" src="https://github.com/user-attachments/assets/0d9ca6be-44ad-4501-b308-8b05f2e2082f" />
*Figure 13: Distribution of `venue_capacity_log` variable after imputation*

This distribution is much closer to normal and will be better for our models to use in predicting, instead of associating outlier capacities with the same week-long sales total since there aren't enough samples.

The `sales_total_7d_next` variable had a similar problem:

<img width="556" height="428" alt="image" src="https://github.com/user-attachments/assets/5559fd2b-b7f5-4a31-9d6e-42b653e1f0c1" />
*Figure 14: Distribution of `sales_total_7d_next`*

And I got to see the `np.log1p` error handling play out in this case, where many records have no transactions within a weeks' time:

<img width="547" height="428" alt="image" src="https://github.com/user-attachments/assets/7bc9c0f2-1628-4da9-87ec-70f4d2bd1129" />
*Figure 15: Distribution of `sales_total_7d_next_log`*

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
