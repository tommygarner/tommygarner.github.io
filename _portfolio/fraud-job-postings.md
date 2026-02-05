---
title: "Detecting Fraudulent Job Postings"
collection: portfolio
excerpt: "End-to-end machine learning pipeline to flag fraudulent job postings using text, metadata, and calibrated thresholds."
date: 2026-11-01
external_link: "[https://medium.com/](https://medium.com/generative-ai/stanford-just-killed-prompt-engineering-with-8-words-and-i-cant-believe-it-worked-8349d6524d2b)"   # paste your actual Medium URL
tags:
  - fraud detection
  - machine learning
  - nlp
  - streamlit
  - github
---
[<i class="fab fa-github" aria-hidden="true"></i> View Code on GitHub](https://github.com/tommygarner/job-postings-fraud){: .btn .btn--primary}

This project explores how to make machine learning models interpretable and explainable in a real-world classification task. Using an ensemble of three distinct architectures—Naive Bayes, LSTM, and a MiniLM transformer—we built a system to detect fraudulent job postings, then focused on understanding why each model makes its predictions. The project implements LIME, SHAP, and Integrated Gradients to provide word-level and token-level explanations, showing users exactly which phrases and patterns triggered a fraud warning.

The result is a Streamlit web application that goes beyond simple predictions. Users can input job posting details and receive not just a risk assessment, but visual explanations of model confidence, feature importance, and the specific signals that influenced the decision. This project was developed for the Advanced Machine Learning course at UT Austin, with the goal of demonstrating that responsible ML isn't just about accuracy—it's about building systems people can understand and trust.
