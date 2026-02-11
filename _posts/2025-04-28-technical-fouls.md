---
layout: single
title: "Do Technical Fouls Hurt Your Team?"
date: 2025-04-28
description: "An analysis of 12,458 NBA technical fouls reveals surprising insights about their impact on team performance"
author_profile: true
toc: true
toc_sticky: true
tags:
  - NBA
  - sports analytics
  - statistics
  - python
  - data science
  - basketball
excerpt: "After analyzing 12,458 NBA technical fouls across multiple seasons and running statistical tests on 3,334 filtered games, I found something surprising: technical fouls show no statistically significant impact on team performance. Even for Draymond Green."
published: true
---

<img width="1236" height="810" alt="image" src="https://github.com/user-attachments/assets/f7962289-7640-4e5f-acaa-2700e7661a56" />


## The Question Everyone Assumes They Know the Answer To

We've all seen it play out a thousand times: A player argues a call, the ref blows the whistle, a technical foul is assessed. The opposing team gets a free throw and possession.

Surely this hurts the team, right?

**What if I told you the data says otherwise?**

---

## Enter: Draymond Green

When you think of technical fouls in the modern NBA, one name immediately comes to mind: Draymond Green. The Warriors' emotional leader has become synonymous with passionate (some might say excessive) referee interactions.

<img width="1200" height="1200" alt="image" src="https://github.com/user-attachments/assets/ffda3e28-eed4-4ea1-ac94-2649b877a405" />

Surely Draymond Green's technicals aren't the same as Tim Duncan's technicals. Therefore, no two techs are the same, since they all have unique contexts, and the sheer amount of them cannot capture an overall generalization.

But what if we could isolate the impact? What if we could measure whether these emotional outbursts actually translate to performance changes on the court?

Let's look only at Draymond Green's technical fouls to see what the numbers tell us.

---

## 12,458 Technical Fouls and Counting

To answer this question rigorously, I analyzed NBA play-by-play data covering thousands of games. Here's what went into the analysis:

- **12,458 total technical fouls** across multiple NBA seasons
- **3,334 technical fouls** in the final analysis after filtering for:
  - Games with exactly **one** technical foul (to avoid confounding effects)
  - Technical fouls occurring between 4 and 44 minutes of game time (enough time to measure before/after impact)
  - Proper roster matching to confirm the player was on the team that season
- **91% regular season games**, 9.4% playoff games

---

## Net Rating Before and After

The key metric I used was **net rating**: the number of points scored minus points allowed per 100 possessions. This normalizes for pace and gives us a clean measure of team performance.

For each technical foul, I calculated:
1. **Net rating in the period BEFORE the technical** (from game start to the tech)
2. **Net rating in the period AFTER the technical** (from the tech to game end)

Then I ran paired t-tests to see if there was a statistically significant difference.

---

## The Results

### Overall Analysis: No Significant Impact

Across all 3,334 analyzed technical fouls:

- **Mean Net Rating Before Tech Foul**: 0.33
- **Mean Net Rating After Tech Foul**: 1.69
- **P-value**: 0.1045 (not statistically significant at α=0.05)

Surprisingly, the net rating went *up* after the sole technical for the afflicted team. But, it's not statistically significant.

---

### The 2001 Rule Change: Did It Matter?

In 2001, the NBA implemented the "Defensive Three Seconds" rule, fundamentally changing how defense is played. Maybe this changed the impact of technical fouls?

**Pre-2001 Era (Before October 29, 2001):**
- Mean Net Rating Before: 2.41
- Mean Net Rating After: 2.57
- **P-value**: 0.9710 (about as far from significant as you can get)

**Post-2001 Era (After October 29, 2001):**
- Mean Net Rating Before: 0.23
- Mean Net Rating After: 1.65
- **P-value**: 0.0962 (close, but still not significant)

The rule change didn't fundamentally alter how technical fouls impact performance. In both eras: **no statistically significant impact**.

---

### Draymond Green: The Stretch Case

Remember how we started with Draymond? Here's what the data shows:

- **40 total games** where Draymond had at least one technical or flagrant foul
- Out of **1,116 total Warriors games** in the Draymond era (Oct 2012 - present):
  - 96.4% of games: **No Draymond technical/flagrant**
  - 3.6% of games: **Draymond technical/flagrant**

But here's the kicker:

**Draymond Green Technical Fouls Analysis:**
- **P-value**: 0.7937
- **T-statistic**: 0.264

Even for the player most famous for technical fouls in the modern NBA, there's **no statistically significant impact** on his team performance.

---

### Context Matters... Or Does It?

Maybe technical fouls only matter in close games? I split the analysis:

**Close Games** (net rating within ±10 points):
- 1,904 games analyzed
- Mean net rating before: 0.23
- Mean net rating after: 1.51
- **P-value**: 0.124 (not significant)

**Blowout Games** (net rating >10 or <-10 points):
- 1,430 games analyzed
- Mean net rating before: 0.47
- Mean net rating after: 1.92
- **P-value**: 0.363 (not significant)

Neither close games nor blowouts showed a statistically significant impact.

---

## What About Multiple Comparisons?

Any good statistician knows that when you run multiple tests, you need to correct for multiple comparisons. I applied the **Bonferroni correction**, which is conservative:

- Original significance level: α = 0.05
- Corrected for multiple tests: α = 0.0125

**Result**: Even with the more lenient 0.05 threshold, none of the tests reached significance. With the corrected threshold, it's not even close.

---

## Visualizing the Data

The distributions tell the story visually:

### Technical Fouls Throughout the Game
Technical fouls occur relatively evenly throughout games, across all four quarters. There's no particular "danger zone" where technicals cluster.

<img width="1466" height="454" alt="image" src="https://github.com/user-attachments/assets/1a136296-7f66-4faa-8fa5-93be63d7fb25" />

*Figure 1: The distribution of technical fouls throughout an NBA game*


### Net Rating Before vs. After

<img width="1466" height="454" alt="image" src="https://github.com/user-attachments/assets/0d1e82f9-00ba-437d-99dd-7734768dd930" />

*Figure 2: The spread of net rating before and after a sole technical foul*

When you look at the distribution of net ratings before and after technical fouls:
- The distributions are remarkably similar
- Both show wide variance (ranging from -100 to +100)
- The medians and quartiles overlap substantially
- No dramatic shift in the distribution

The box plots confirm what the statistics tell us: **there's no meaningful difference**.

---

## So What Does This Mean?

Here's the truth: **Technical fouls don't appear to have a measurable immediate impact on team performance**.

This doesn't mean they're good. They still:
- Give the opponent a free throw
- Can lead to ejections (two technicals = ejection)
- Set a bad example
- Might have longer-term psychological effects not captured in single-game net rating

But the idea that a technical foul "gives the opponent momentum" or "hurts your team's performance" in the immediate aftermath? **The data doesn't support it.**

---

## Why Might This Be?

A few hypotheses:

1. **The free throw is negligible**: One free throw rarely changes the course of a game
2. **Teams refocus**: The technical might actually snap a team back into focus
3. **It's already accounted for**: Teams that get technicals might be performing poorly anyway (selection bias)
4. **Emotional release**: Sometimes showing emotion galvanizes rather than hurts

The most likely explanation? Sole technical fouls are relatively rare events (only 3.6% of games in the Draymond era for the Warriors), and their impact is drowned out by the much larger variance in normal game flow.

Another study might find the impact of ejections, for instance, which is an entirely different research question.

---

## The Draymond Green Paradox

Let's circle back to where we started. Draymond Green is known for his technical fouls. His passionate play style includes arguing calls, demonstrating frustration, and yes, picking up technicals.

The Warriors won **4 NBA championships** with Draymond Green (2015, 2017, 2018, 2022) playing exactly this way.

The data suggests his sole technical fouls didn't hurt the team's performance. Maybe, just maybe, the emotional intensity that leads to technical fouls is part of what makes him effective. Not in spite of the techs, but because that passion drives his defensive intensity, communication, and leadership.

---

## The Bottom Line

After analyzing 12,458 technical fouls across multiple seasons, eras, contexts, and even focusing on the NBA's most notorious technical foul recipient, the conclusion is clear:

**Technical fouls show no statistically significant immediate impact on team net rating.**

This null result is consistent across:
- Overall analysis (p = 0.10)
- Pre-2001 era (p = 0.97)
- Post-2001 era (p = 0.096)
- Draymond Green specifically (p = 0.79)
- Close games (p = 0.12)
- Blowout games (p = 0.36)

Sometimes the most interesting finding in data analysis is when your hypothesis is proven wrong. We assume technical fouls hurt teams because they feel dramatic in the moment. But the numbers tell a different story.

---

## Methodology Notes

For the statistically inclined:

- **Sample size**: 3,334 technical fouls after filtering
- **Statistical test**: Paired t-tests (comparing before/after within same game)
- **Significance level**: α = 0.05 (with Bonferroni correction to α = 0.0125 for multiple comparisons)
- **Metric**: Net rating (points per 100 possessions)
- **Filtering criteria**:
  - Exactly one technical foul per game
  - Technical occurred between 4-44 minutes of game time
  - Proper roster matching confirmed
  - Sufficient play time before and after to calculate net rating

