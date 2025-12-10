---
title: "Fraud Detection on Job Postings"
collection: portfolio
excerpt: "Built a supervised learning pipeline to flag fraudulent job postings using text, metadata, and behavioral features, with a focus on interpretable model decisions."
date: 2024-02-01
github: "https://github.com/tommygarner/Fraud_Job_Postings"  # update to exact repo URL
tags:
  - fraud detection
  - classification
  - NLP
  - streamlit
  - github
---

This project tackles the challenge of detecting fraudulent job postings by combining classic feature engineering with modern machine learning. The pipeline cleans and vectorizes job descriptions, engineers metadata features (e.g., company information, salary anomalies, location patterns), and trains tree‑based and linear models to predict whether a posting is legitimate or suspicious.

Model performance is evaluated with precision–recall–oriented metrics to reflect the cost of false positives and false negatives, and interpretation tools are used to highlight which words and attributes push a listing toward the “fraud” label. A forthcoming Medium article will walk through the full workflow, including EDA, modeling decisions, and how this kind of system could be integrated into a real review process.
