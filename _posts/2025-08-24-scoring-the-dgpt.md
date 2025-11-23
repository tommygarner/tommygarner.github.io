---
layout: default
title: "Scoring the DGPT: Finding the Hardest Course in Pro Disc Golf"
date: 2025-08-24
description: "Using analytics to determine which DGPT courses and holes are the most difficult on the Pro Tour"
---

## Introduction
I love playing and watching disc golf, but I'm no good. I just play for fun. There's only a handful of courses in my area, and most of the time it's just too hot to play. And I always get a breakfast-ball, or two (per hole).

In my 3 years of playing, I've brought along friends and had some of the deepest conversations on the course. I've made incredible shots on video and have used UDisc as my Strava equivalent. Eventually, as everyone does, I came across Jomez.

[JomezPro](https://www.youtube.com/@JomezPro) is a disc golf media channel that captures a large majority of content on the Disc Golf Pro Tour (DGPT). The channel features lead cards from every round while also incorporating highlight plays from the Chase cards and other players in competition.

I love JomezPro. The content is pure. Scorecards are clean. Video editing is sharp. And the BigSexyCommentary can always make me chuckle.

Over time, my love for disc golf has grown, culminating in going to my first ever pro event at the 2024 MVP Open at Austin, where Niklas Anttila won his second-straight tournament in Austin at the Harvey Penick course. 

As I've watched more and more of the 2025 pro tour this year, I've wondered what the hardest course is. You know, the one that the pros dread to visit. Or the hardest holes that give you the heart-breaking triple bogeys. Or what the easiest 'gimmie' hole is, that would be total embarrassment to miss the bird.

## Methodology
To answer these questions, I chose to turn to the raw data.

How can we use analytics to determine the difficulty of a course or a specific hole? What determines difficulty? Is it subjective?

The following poll was found on [Reddit](https://www.reddit.com/r/discgolf/comments/u0whi7/how_do_you_determine_the_difficulty_of_a_course/) that polled nearly 440 responses on r/discgolf asking that very question: *What determines difficulty?*

| What determines difficulty? | Number of responses |
| :--- | :--- |
| Typical scores relative to par | 136 |
| Number of obstacles, OB, hazards, water, etc. | 115 |
| Subjective feel, intangibles, overall layout | 82 |
| Physical demands of a hole (elevation, length, wind exposure, heat) | 56 |
| Results | 45 |
| Any other suggestions (comments)? | 2 |

Eventually, I determined that performance will be my chosen relative proxy for determining difficulty of a course, especially accounting for intangibles such as subjective feel or even accounting for OBs, Mandatories (mandos), and Hazards that are much harder to quantify and structure in data.

### Data Collection
This website [Statmando](https://statmando.com/stats/tour-holes-2024-mpo) is a platform that provides granular disc golf statistics on every pro and many amateur events and tournaments. The company was found by a group of disc golfers who wanted to create a resource where statistics live for the niche sport, and their data helps rank, profile, and compare statistics amongst players and performances. 

The table this project drew inspiration from is from  Statmando's StatZone, a specific page on the site that contains data on individual holes from Major and Elite series events in the 2024 MPO (Mixed Professional Open) division. This would classify as hole-by-hole data, including data analysis metrics like Avg to Par, under and over Par percentages.

Statmando has been collecting hole-by-hole data since 2021 for the MPO division. So after finding the data source, I then aggregated each year's statistic into the same dataframe. For the scope of answering my driving question, I decided that their average-to-par statistic will be the best measurement available.

*It is good to note that some Events and Layouts have changed names over the years. Likewise, some Holes have been drastically altered between 2021-2024. While data cleaning, I decided to standardize each Layout to help in the aggregating of statistics. There are some discrepancies as courses have changed tees or pins or even entirely revamped a specific hole. But for the most part, hole dimensions are consistent (as much as I could control).

---

## Top 5 Hardest Holes

| Event | Layout | Hole # | Hole Par | Length | Avg to Par | Times Played | Year |
|---|---|---|---|---|---|---|---|
| Discraft Ledgestone Open | Northwood Black | 12 | 5 | 1050 | 1.41 | 281 | 2023 |
| Discraft Ledgestone Open | Northwood Black | 12 | 5 | 1050 | 1.34 | 324 | 2021 |
| Discraft Ledgestone Open | Northwood Black | 14 | 5 | 893 | 1.31 | 324 | 2021 |
| Discraft Ledgestone Open | Northwood Black | 12 | 5 | 1050 | 1.27 | 291 | 2022 |
| PDGA Professional Disc Golf World Championships | New London | 6 | 5 | 1215 | 1.18 | 411 | 2024 |

**#1 Discraft Ledgestone Open - Northwood Black - Hole 12**

Par 5, 1,050ft at *1.41 Avg to Par*

<iframe width="560" height="315" src="https://youtube.com/embed/OpvKldRbmL8?start=498" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe>

This hole looks like it sucks. A wooded tee shot that needs to get ~400ft down the fairway for even a chance at par. A narrow upshot over a low water crossing that has a generous landing zone. And the final approach into another technical wooded area. And to top it all off, a lowered basket. 

In the 2023 Discraft Ledgestone Open, this hole claimed its most victims. Only 3 people birdied (or better, but will be a miracle if we ever see it) on this hole. That's about 1%. In contrast, 74% of the field bogeyed or worse, and 25% of players managed to get par. 

Funny enough, this hole also takes the 2nd and 4th places in the most difficult holes seen on the DGPT since 2021. If it wasn't for a course change in 2024, I'd have no doubt this hole would've taken 4 of the top 5 spots, and the course maybe all 5 spots, on this list.

---

## Top 5 Easiest Holes

| Event | Layout | Hole # | Hole Par | Length | Avg to Par | Times Played | Year |
|---|---|---|---|---|---|---|---|
| The Open at Austin | Harvey Penick | 5 | 4 | 520 | -0.89 | 109 | 2024 |
| Las Vegas Challenge | Innova Discs | 16 | 5 | 888 | -0.86 | 194 | 2021 |
| Green Mountain Championship | 2024 DGPT Playoffs: GMC Fox Run MPO | 10 | 3 | 315 | -0.85 | 88 | 2024 |
| Green Mountain Championship | 2024 DGPT Playoffs: GMC Fox Run MPO | 6 | 3 | 265 | -0.84 | 88 | 2024 |
| Green Mountain Championship | 2024 DGPT Playoffs: GMC Fox Run MPO Rd4 | 6 | 3 | 265 | -0.79 | 87 | 2024 |

**#1 The Open at Austin - Harvey Penick - Hole 5**

Par 4, 520ft at *-0.89 Avg to Par*

<iframe width="560" height="315" src="https://youtube.com/embed/XrSRVafYhhI?start=1263" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe>

Now for the easiest hole on the 'whole' tour: The Open at Austin's Hole 5 at Harvey Penick. 

Hole 5 at Harvey Penick looks challenging on paper with OBs taking up majority of the fairway. However, the hole is relatively short for a par 4. For context, across all par 4s in the available data, this hole is less than 100ft shorter than the average par 4. 

In 2023, hole 5 was previously recorded as a par 3 at 482ft. But in 2024, the course decided to make some changes including forcing players to carry over an OB area for their second shots. There are a couple of trees immediately coming out of the teeshot, and the basket also includes some small trees to limit C2 putting.

However, from the included snippet, you can see that many players pushed to carry over the OB on their teeshots, essentially allowing them to 'run' their second shots for eagles. If a player instead chose to lay up in the landing zone, their approach shot more often than not landed within C2, still rewarding them with a chance for birdie.

Relative to par, The Open at Austin saw almost every player receive a par, bird, or better! Only 2.75% of players received a bogey or worse on this hole, while 13.76% received a par and 83.5% of the field birdied or better.

Out of the many disc golf events I have watched online, I would've never guessed that the only event I've attended was the one with the easiest hole since 2021!

The major caveat in this table is the sample size. 3 of the 5 holes have been played less than 100 times, meaning they were likely featured for only one round. So, it must be noted to take this with a grain of salt, as with more opportunities for holes to be played (and remain unchanged), we can better find determine this target objective.

---

## Top Hardest Courses

| Event | Layout | Avg to Par |
|---|---|---|
| Discraft Ledgestone Open | Northwood Black | 0.245185 |
| PDGA Champions Cup | Northwood Park | 0.162778 |
| PCS Open | Overas Diskgolfpark | 0.095556 |
| Dynamic Discs Open | Emporia Country Club | 0.084259 |
| PDGA Professional Disc Golf World Championships | New London | 0.079444 |

**#1 Northwood Black, Morton, IL**

Shocker. With 4 of the top 5 hardest holes on the entire DGPT in the past 4 years, this course is a gauntlet. Wooded. Technical. Long. Unforgiving. Illinois. The whole 9 yards.

To think that players will typically score, on average, 0.25 points higher than par on a given round at Northwood Black is pretty insane. Granted, watching JomezPro has inadvertedly caused me to expect negative scores from any professional on any course. However, the only followed cards are your lead cards on Jomez, which are shooting sometimes 10-down per round. 

To put the whole field into perspective, then, the average-to-par across the 4 year span in the entire dataframe is -0.06. This means that, on average, any given player on the DGPT, playing any course during any yearbetween 2021 and 2024, will shoot 0.06 points less than par. 

But for Northwood Black to have almost +0.10 points on average over the second-hardest course is a significant occurrence. The average player would expect their score to increase by over 0.3 points when flying out to Illinois for the Discraft Ledgestone Open. 

Good thing we aren't evaluating how much my average score would increase...

---

## Top Easiest Courses

| Event | Layout | Avg to Par |
|---|---|---|
| PDGA Champions Cup | WR Jackson Memorial Course | -0.195278 |
| Las Vegas Challenge | Innova Discs | -0.194630 |
| Green Mountain Championship | Brewster Ridge | -0.188519 |
| Las Vegas Challenge | Infinite Discs | -0.181389 |
| The Preserve Championship | Black Bear | -0.177222 |

**#1 W.R. Jackson Memorial Course, Appling, GA**

The W.R. Jackson Memorial Course is an interesting case because many consider the course a "championship-level wooded course". However, in 2022, the course had an average-to-par score of -0.22, and in 2023, the field scored -0.17 less than par for the course. 

In fact, upon researching this topic, many consider The Preserve Championship being the easiest course on the DGPT. By breaking down scores by year, however, the Black Bear layout received a -0.17 'Avg to Par' score in 2021, -0.13 in 2022, -0.29 in 2023, and -0.18 in 2024.

This is largely due to the amount of times each course has been played. The Black Bear layout has been played more than 2x as much as the W.R. Jackson Memorial Course. Therefore, with more opportunities to play in the future, we will be able to see the average-to-par statistics converge to their true means, possibly revealing the fans' intution of Black Bear being the easiest course statistically on the DGPT.

---

## Thank you for reading! 

*I hope you enjoyed my ramble about disc golf.*

*My hope is that I've convinced you to try out a JomezPro video next time you're searching YouTube while you eat your food.*

-Tommy G

---
**Tools used:** Python, Pandas, Web scraping  
**Data source:** [Statmando](https://statmando.com)  
[View project on GitHub →](https://github.com/tommygarner)
