---
title: "The Setlist: A Personalized Concert Recommender"
collection: portfolio
excerpt: "Streamlit app that matches your Spotify taste with upcoming concerts using Ticketmaster and SeatGeek APIs."
date: 2025-12-01
tags:
  - recommender systems
  - live entertainment
  - python
  - streamlit
  - supabase
---
[<i class="fab fa-github" aria-hidden="true"></i> View Code on GitHub](https://github.com/tommygarner/The-Setlist){: .btn .btn--primary}

The Setlist is a personalized concert recommendation app that connects listeners’ Spotify libraries with real‑time concert data. The app pulls a user’s favorite artists from Spotify, enriches them with metadata, and then queries Ticketmaster and SeatGeek APIs to find matching shows in selected markets.

Users can swipe through suggested artists in a Tinder‑style interface, save favorites, and explore upcoming events tailored to their taste. The app is built in Python with Streamlit for the UI and deployed as an interactive web app, tying together API integration, recommendation logic, and a smooth fan‑facing experience.

This app was refined using Claude Code to make the repo compatible with Docker containers and local hosting, but also runs a lighter version on [Streamlit Cloud](https://thesetlist.streamlit.app/). Feel free to test it out and push my API rate limits to the max to figure out your next concert!
