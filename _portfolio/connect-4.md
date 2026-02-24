---
layout: single
title: "UT Project: Connect 4"
date: 2026-02-08
description: "How we used Monte Carlo Tree Search to generate training data, then trained a CNN and Transformer to play Connect 4"
author_profile: true
toc: true
toc_sticky: true
classes: wide
tags:
  - deep-learning
  - reinforcement-learning
  - mcts
  - cnn
  - transformer
  - connect4
  - python
  - tensorflow
  - keras
excerpt: "We built two neural networks (CNN and Transformer) to play Connect 4, using Monte Carlo Tree Search for self-play data generation. Here's what worked, what didn't, and what the models taught us about the game."
---

## Part 1: The Problem

Connect 4 is a two-player game most people learn as children. Drop a piece, try to get four in a row. But building an AI that plays it well turns out to be surprisingly non-trivial.

The classic approach -- MCTS -- works. Given enough time per move, it can find strong plays in almost any position. The problem is speed. MCTS does thousands of simulations per decision. That is fine for a research setting, but it makes for a slow, compute-heavy experience in a web app.

Our goal for this project (team: Tommy, Sophia, Carolina, and Niladri) was to train a neural network to **play like an MCTS agent without running MCTS at inference time.** The network would learn from thousands of MCTS self-play games and generalize from those examples, not from hand-coded rules about what makes a good Connect 4 position.

The central challenge is a classic one in supervised-from-self-play learning: the data does not exist until you generate it, and generating it requires the very intelligence you are trying to teach.

**The framing question for this post:** How do you teach a neural network to think like a chess engine, using only examples of strong play?

---

## Part 2: Generating Training Data with MCTS

### Why MCTS?

Monte Carlo Tree Search is a best-first search algorithm. It builds a game tree by repeatedly:

1. **Selecting** the most promising unvisited node, balancing how often a move has won against how rarely it has been tried
2. **Expanding** that node by generating its legal children
3. **Rolling out** from that node by simulating play to the end of the game
4. **Backpropagating** the result up the tree to update visit counts and win rates

The selection step uses a formula that rewards high win rates but also penalizes moves that have been visited too often -- this keeps the search from fixating on one option without exploring alternatives. After enough rollouts, the most-visited child of the root is the move MCTS recommends. We use those recommendations as training labels.

### The Self-Play Pipeline

We ran **20,000 games of self-play**, with each position evaluated using **10,000 MCTS rollouts**. The key design choices:

**Majority voting (K=3).** Rather than running MCTS once and taking the top move, we run three independent MCTS searches per position and take the majority vote. This reduces label noise from individual unlucky rollout sequences. If all three agree on column 4, that label is much more trustworthy than a single run.

**Heuristic rollouts.** Pure random rollouts produce noisy win estimates because they ignore obvious moves. Our rollout policy checks, in order: (1) take an immediate win, (2) block an opponent's immediate win, (3) prefer the center column with 20% probability, (4) otherwise play randomly. This applies across all four directions -- horizontal, vertical, and both diagonals. Better rollouts mean cleaner training labels.

**Dirichlet noise at root (AlphaZero-style).** To prevent MCTS from always selecting the same opening and to encourage diversity in the training data, we blend the root move distribution with random noise -- 75% from the prior, 25% from noise. This is applied only at the root node, so deeper search is unaffected.

**Random opening moves.** Each game begins with 1--8 random moves before MCTS takes over. This spreads the dataset across many different board configurations, not just positions that arise from MCTS-vs-MCTS games starting from the empty board.

### Scale and Time

Data generation is the bottleneck of this entire project. Most of the compute time is not training -- it is generating labeled examples.

| Config | Games | Est. Time | Raw Samples |
|--------|-------|-----------|-------------|
| Overnight | 15,000 | 31--42 hours | ~285,000 |
| Quick | 5,000 | ~12 hours | ~95,000 |
| Test | 1,000 | ~2--3 hours | ~19,000 |

### Canonical Form

One structural decision made the data pipeline much cleaner: we always store board states from the **current player's perspective**.

Without this, the model would need to learn separate strategies for Player 1 and Player 2 -- even though the game is symmetric from each player's viewpoint. With canonical form, the model always sees one layer as "my pieces" and another as "my opponent's pieces", regardless of who is actually to play. This removes a confound and cuts the learning problem roughly in half.

---

## Part 3: From Board to Tensor

### Board Encoding

A Connect 4 board is 6 rows by 7 columns. We encode it as a **(6, 7, 2)** array:

- **Layer 0:** 1 where the current player has a piece, 0 elsewhere
- **Layer 1:** 1 where the opponent has a piece, 0 elsewhere

This is a standard representation in board game AI (AlphaGo, AlphaZero). Separating the two players into distinct layers lets the network distinguish friendly from opponent pieces through simple filter responses, rather than learning to interpret a sign convention (positive vs. negative, 1 vs. 2).

### Symmetry Augmentation

Connect 4 is left-right symmetric -- the board looks the same mirrored horizontally, and the best move mirrors accordingly. We exploit this by duplicating every training sample with its horizontal mirror image and flipping the target column.

We do **not** swap the player layers during augmentation. Swapping them would mean asking the model to respond from the opponent's perspective -- but since all data is already in canonical form, swapping would corrupt the labels.

The result:
- **Original:** 348,844 samples
- **After horizontal mirror:** 697,688 samples
- **After deduplication:** 697,603 samples

### Deduplication via Majority Vote

The same board position can appear multiple times across different games, sometimes with different MCTS recommendations. Rather than keep all copies, we deduplicate: for each unique board state, we keep the most common label across all occurrences. If there is a tie, we prefer the column closer to center.

### The Data Leakage Lesson

This one hurt. Early in the project we split our dataset with a random shuffle -- 85% train, 15% validation. Val accuracy looked great. Then we realized the problem: positions from the same game are highly correlated. If game 1247 has 30 positions and some land in train while others land in val, the model is effectively being tested on its own training games.

We had to learn this the hard way after running all of our models. The fix was to split by **game ID**: all positions from a given game go entirely into train or entirely into val.

After correcting for this, val accuracy dropped meaningfully. The numbers we report here reflect the honest, game-ID-split evaluation.

### Legal Move Masking

A model should never play into a full column. We enforce this by adding a large negative penalty to any column that is already full, before the model converts its raw scores into probabilities. This makes full columns have effectively zero probability without requiring a special output layer -- a simple fix with an important practical effect.

---

## Part 4: Model 1 -- The CNN Bot

### Why CNN?

Connect 4 is full of local spatial patterns: immediate wins, blocking moves, three-in-a-row threats, and stacking opportunities. A convolutional neural network applies the same learned filter across every region of the board, looking for the same local arrangement of pieces wherever it appears. That is exactly the right match for this problem.

CNNs have a strong **inductive bias toward local patterns**, which we expected to align well with Connect 4's tactical structure.

### Architecture

Our CNN uses four convolutional blocks followed by global average pooling and a dense head:

- Input: 6x7 board with 2 layers
- Four stacked convolution stages, each with 192 filters and 5x5 kernels, batch normalization, and ReLU activation
- Global average pooling to compress spatial dimensions
- A dense layer of 320 units with dropout for regularization
- A final 7-unit output (one per column) with legal move masking
- **~192,000 parameters total**

### Training

- 85% train / 15% validation split by game ID
- Adam optimizer with learning rate reduction when progress stalls
- Early stopping to prevent overfitting, with the best checkpoint saved
- Trained on Google Colab with GPU acceleration

### Result: 64.40% Validation Accuracy

![CNN training curves placeholder]
*Figure 1: CNN training and validation accuracy over epochs. The model converges cleanly with early stopping.*

### Gameplay Insights

Playing the CNN bot revealed some interesting strengths and weaknesses:

**Hard to beat (center stacking).** When the CNN builds a vertical stack in the center column, it creates multiple diagonal continuation threats simultaneously. Blocking one diagonal opens another. These positions are genuinely difficult to counter.

**Exploitable (horizontal three-in-a-row).** In testing, we found a repeatable checkmate in three turns: build an unchecked horizontal three-in-a-row on one side. The CNN consistently failed to recognize and block this threat until it was too late.

**Quirk: column 2 preference.** When starting first from an empty board, the CNN chose the third column from the left in 5 out of 7 cases across our tests. This appears to be a vertical-stacking strategy learned from the training distribution. The true center column was not its default.

**Asymmetry.** The model was noticeably more sensitive to left-side horizontal threats than right-side threats. This is likely a dataset artifact -- the distribution of positions in our self-play data may have favored left-side examples in some way.

**Better late than early.** The CNN played more reliably in late-game positions (more pieces on the board) than in early-game positions. This reflects the training distribution: MCTS makes its most consequential decisions after the random opening phase, so the training data is weighted toward mid-to-late positions.

---

## Part 5: Model 2 -- The Transformer Bot

### Why Transformer?

Self-attention can model relationships between any two cells on the board regardless of distance. Where CNN filters are constrained to a local receptive field, a Transformer can directly attend to the relationship between, say, the top-left and bottom-right corners in a single step. For board games with long-range strategic dependencies, this global context could matter.

### Architecture

We treat each cell of the 6x7 board as a separate input token, producing 42 tokens total. A special summary token (called a CLS token, borrowed from language model design) is prepended, and its final representation is used to predict the move:

- 42 board cell tokens, each describing that cell's contents, plus a learned CLS token
- Learned embeddings to map each cell to a higher-dimensional representation
- Learned positional embeddings so the model knows where each cell is on the board
- Several Transformer encoder layers, each using multi-head attention followed by a small feed-forward network, with normalization and dropout
- The CLS token's output feeds into a 7-unit prediction layer with legal move masking
- **~137,000 parameters total**

### Result: 55.82% Validation Accuracy (vs. 64.40% CNN)

![Transformer training curves placeholder]
*Figure 2: Transformer training and validation accuracy. Training accuracy reached ~60% but validation plateaued at 55%, indicating weaker generalization than the CNN.*

### Gameplay Insights

**No center preference.** Unlike the CNN, the Transformer bot rarely chose the center column as an opening move. Its opening play appeared nearly uniform across columns, suggesting it did not internalize the strategic value of center control.

**Reactive, not strategic.** The Transformer tended to respond to immediate local threats rather than building long-term plans. It played defensively when under attack but did not create threats proactively.

**Horizontal detection failure.** Like the CNN but more consistently, the Transformer struggled to detect and block horizontal three-in-a-row threats. This was its most exploitable weakness in human testing.

**Pattern continuation, not board value.** The Transformer appeared to learn continuation patterns (if a column has pieces, keep stacking there) rather than board-value principles (center control, threat creation). This is consistent with a model that picked up local correlations in the training data without the spatial inductive bias to generalize them.

**Less generalization.** The gap between training accuracy (~60%) and validation accuracy (55.82%) was larger than for the CNN, and val accuracy plateaued earlier. The Transformer needed more data or a deeper architecture to match the CNN's generalization.

---

## Part 6: CNN vs. Transformer -- What the Numbers Say

| Metric | CNN | Transformer |
|--------|-----|-------------|
| Val Accuracy | **64.40%** | 55.82% |
| Parameters | 192k | 137k |
| Convergence | Fast | Slower, plateaus |
| Local patterns (wins/blocks) | Strong | Weaker |
| Center control | Moderate | Poor |
| Horizontal threat detection | Reliable | Struggles |

### Why CNN Wins Here

Connect 4 at this scale is dominated by **local spatial patterns**: is there a three-in-a-row here? Can I extend it? Is the opponent one move from winning? These are exactly the features CNN filters detect naturally.

Transformers need **scale** -- more data, larger models, deeper architectures -- to overcome the CNN's strong spatial inductive bias. At 137k parameters trained on roughly 700k samples, the Transformer does not have enough capacity or data to discover spatial structure from scratch the way a CNN does implicitly through its design.

This does not mean Transformers are the wrong tool for board games in general. Modern Go and chess engines that use Transformer-based architectures are trained on orders of magnitude more data than we used here. At our scale, the CNN's structural assumptions about local patterns were simply a better match to the problem.

### Easy vs. Hard Positions

**Easy positions** (immediate wins and forced blocks) are where both models perform well. If the winning move is obvious -- a three-in-a-row with an open end -- MCTS will label it consistently and the models learn to recognize it.

**Hard positions** (two-move traps, ambiguous offense/defense tradeoffs) are where both models struggle. When the best response requires seeing two moves ahead, MCTS labels are noisier and both models tend to default to locally plausible but strategically shallow moves.

---

## Part 7: Live Demo

**Try it yourself:** [https://msba25optim2-29.anvil.app/](https://msba25optim2-29.anvil.app/)

Login: `dan` / `Optimization1234`

The web app lets you choose between the CNN bot and the Transformer bot. Play a game and see if you can find the horizontal checkmate exploit described above. The Transformer is more vulnerable; the CNN will occasionally see it coming.

---

## Key Takeaways

1. **Data volume dominates.** Going from 200 games to 1,000 games raised validation accuracy by roughly 18 percentage points. Architecture improvements on the same small dataset moved the needle far less. If you are working on a similar project, invest in data generation before tuning model depth or width.

2. **Split by game ID, not randomly.** Positions from the same game are highly correlated. A random shuffle leaks correlated examples between train and val and produces inflated, misleading accuracy numbers. Always split at the game level.

3. **Local patterns favor CNNs.** For board games where tactics are spatial, CNNs are hard to beat without massive Transformer scale. The spatial inductive bias is a real advantage when the signal in the data is local.

4. **Canonical form simplifies training.** Always encoding board states from the current player's perspective removes the need for the model to learn separate strategies for each player. It is a clean, simple transformation with meaningful downstream impact.

5. **MCTS heuristics matter.** Pure random rollouts produce noisier training labels than heuristic rollouts that check for immediate wins and blocks. Better rollout policy means less label noise means a more learnable dataset.

---

## Tech Stack Summary

**Data Generation:** Python, custom MCTS implementation, multiprocessing, NumPy

**Training:** TensorFlow/Keras, Google Colab (GPU), sparse categorical crossentropy, early stopping, learning rate reduction on plateau

**Models:** CNN (4-block convolutional with global average pooling), Transformer encoder with CLS token

**Deployment:** Anvil web app, Python backend
