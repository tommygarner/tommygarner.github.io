---
layout: single
title: "Detecting Fraudulent Job Postings with Machine Learning"
date: 2025-12-09
description: "Building a supervised learning pipeline to flag fraudulent job postings using text, metadata, and calibrated thresholds."
author_profile: true
tags:
  - fraud detection
  - classification
  - nlp
  - machine learning
excerpt: "Built an end-to-end ML workflow to identify fraudulent job postings, from feature engineering on text and metadata to model comparison, calibration, and threshold tuning."
---

In this project, I worked with a labeled dataset of job postings containing both legitimate and fraudulent listings. The goal was to build a supervised learning pipeline that could automatically flag suspicious postings before they reach applicants.

The workflow covered data cleaning, exploratory analysis, and extensive feature engineering on both structured fields (e.g., salary, location, employer metadata) and unstructured text (e.g., job descriptions, titles, and benefits). I experimented with several models—including regularized logistic regression, tree ensembles, and gradient boosting—using cross-validation and stratified splits to handle class imbalance.

Beyond raw accuracy, the focus was on precision, recall, and calibrated probabilities so that decision-makers can choose thresholds that balance false positives versus false negatives. The final model was paired with feature importance and interpretability tools to highlight which patterns and phrases were most indicative of fraud, making the system easier to trust and iterate on in a real-world setting.
