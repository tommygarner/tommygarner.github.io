---
layout: single
title: "Building Two NBA Scheduling Optimizers"
date: 2026-03-19
description: "NBA teams travel over 40,000 miles in a season. Playoff arenas hold dates months before the bracket is set. Here are two separate optimization problems I built solutions for."
author_profile: true
published: false
tags:
  - NBA
  - optimization
  - operations-research
  - scheduling
  - sports-analytics
excerpt: "NBA teams travel over 40,000 miles in a season. Playoff arenas hold dates months before the bracket is set. Here are two separate optimization problems I built solutions for."
---

NBA scheduling sits at the intersection of competitive fairness, logistics, and venue operations. The league juggles 30 teams, 82 regular season games per team, and a playoff bracket that gets determined days before arenas need to host games. I built two separate tools to address two separate problems in that system. This post walks through both.

## Problem 1: Player Fatigue on the Road

Not all road trips are equal. A team flying east across five time zones plays a different game than a team taking a two-hour hop. The NBA schedule is built to minimize back-to-backs and distribute rest, but the order of games within a road trip is rarely optimized for fatigue. A team could visit the same six cities in two different sequences and accumulate dramatically different travel strain.

### The Fatigue Model

I built a per-game fatigue scoring model grounded in published sports science. Each game's score is a function of four components:

**Travel miles.** Using the Haversine formula applied to arena coordinates, I calculate exact great-circle distance between consecutive game locations for every team.

**Travel direction penalty.** Eastward travel disrupts circadian rhythm more than westward travel. Pradhan et al. (2022, *Frontiers in Physiology*) quantified this at roughly 0.72 points per timezone hour crossed eastward. My model applies a 1.3x multiplier on eastward legs and no penalty on westward ones.

**Back-to-back penalty.** Games on consecutive days carry a 1.5x fatigue multiplier on top of travel. JCSM (2021) documented the interaction between back-to-backs and travel direction — the compounding effect is real.

**Jet lag carryover.** Residual jet lag from prior travel decays at roughly one timezone hour recovered per rest day eastward, and 1.5 per day westward. Each unrecovered timezone hour adds 50 fatigue points to the next game. International games (Paris, London, Mexico City, Abu Dhabi) carry a flat 2.0x multiplier on arrival.

The model runs independently for every team across all 1,230 regular season games.

### Road Trip Reordering with TSP

Once every game has a fatigue score, the question becomes: for a given road trip, what order of cities minimizes total accumulated fatigue? This is a variant of the Traveling Salesman Problem. Given a set of required stops (the scheduled opponents on a road trip), find the sequence that reduces total travel strain.

The starting and ending cities are fixed — teams leave from home and return home — but the internal order of stops is the optimization target. I ran TSP across every road trip in the 2025-26 schedule to find the best reordering for each one.

### Results

The potential savings are significant. Across all 30 teams, optimizing road trip sequences reduces accumulated fatigue scores by 30 to 49 percent depending on the team.

| Team | Fatigue Saved | Reduction |
|---|---|---|
| Sacramento Kings | 25,927 | 49.25% |
| Memphis Grizzlies | 35,237 | 48.29% |
| Denver Nuggets | 26,759 | 45.50% |
| Philadelphia 76ers | 19,975 | 45.05% |
| Portland Trail Blazers | 27,360 | 44.01% |

Western Conference teams with wide geographic spreads benefit most, because the variance in sequencing options is higher when cities span more longitude. The LA Clippers' best single road trip optimization is illustrative: a November 14 seven-game trip originally routed through Dallas → Boston → Philadelphia → Orlando → Charlotte → Cleveland could be reordered to Boston → Philadelphia → Cleveland → Charlotte → Orlando → Dallas, saving 2,107 miles of cumulative travel while hitting the same six cities.

The model does not rearrange which opponents a team plays on which dates — those are fixed by the NBA schedule. What it identifies is whether the game-to-game travel order within a road trip could be improved, and by how much.

## Problem 2: Playoff Conflict Scheduling

The regular season optimizer looks backward at an existing schedule. The playoff problem is different: it requires making decisions before the bracket is known.

NBA arenas host hundreds of non-basketball events every year — concerts, hockey games, boxing matches, family shows. When the playoff bracket is finalized in April, the league has a narrow window to assign series home courts before conflicts accumulate. Arenas that have pre-booked a major concert on the date a Game 4 might fall have a problem. The venue either moves the concert (often impossible at short notice), the game (requires league coordination), or accepts revenue loss and logistical strain.

The standard industry response is "hold dates" — arenas block calendar days for potential playoff games months in advance, releasing them only when the team is eliminated. The cost of holding is real: a date held for a Game 6 that never happens is a date that could have hosted a revenue-generating event.

### The Approach

I collected all 2025-26 arena events using the Ticketmaster Discovery API, querying a 5-mile geolocation radius around each of the 30 NBA arenas with weekly date chunks to stay under the API's 1,000-result limit. After deduplication and cleaning, the dataset covers roughly 2,500 events across the full season window (October 2025 through April 2026).

From that, I scored each arena-date pair by event density and built a conflict heatmap across the league. Some arenas have low playoff exposure because they host fewer events; others have densely booked spring calendars that create real scheduling pressure.

The core optimizer uses Monte Carlo simulation to model playoff bracket uncertainty. Because we cannot know in advance which teams will advance, I ran thousands of bracket scenarios weighted by team win probability. For each scenario, a linear program (solved with Gurobi) assigns home/away game dates to minimize total conflict score across all active series simultaneously. The output is a recommended playoff schedule for the 2026 postseason that performs best across the simulated bracket distribution.[^1]

### What the Data Shows

Arena conflict risk is not uniformly distributed. A handful of arenas carry disproportionate scheduling pressure in April — typically large markets with densely booked entertainment calendars and high-probability playoff teams. The conflict heatmap makes clear that the current practice of assigning playoff schedules reactively, after the bracket is set, leaves room for improvement that could be addressed with earlier data-driven hold date strategy.

The full interactive optimizer is available [here](https://github.com/RogueTex/NBAScheduler), with the fatigue dashboard linked in the project files.

---

Both of these tools were built because the scheduling problem interested me from multiple angles at once: it is an operations research problem, a data engineering problem, and a live entertainment problem. The arenas that host playoff games are the same arenas that host the concerts and events I have been building demand forecasting models for. The scheduling decisions the league makes have downstream effects on the secondary ticket market, venue revenue, and fan experience that extend well beyond win-loss records.

### References
[^1]: Pradhan, Cheri N., et al. "The Effect of Circadian Misalignment and Travel Fatigue on Sport Performance." *Frontiers in Physiology*, 2022.
