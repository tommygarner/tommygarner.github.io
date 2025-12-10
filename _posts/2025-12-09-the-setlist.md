---
layout: single
title: "The Setlist: A Personalized Concert Recommender"
date: 2025-04-15
description: "A Streamlit app that combines Spotify data with Ticketmaster and SeatGeek APIs to recommend upcoming concerts."
author_profile: true
tags:
  - recommender systems
  - live entertainment
  - python
  - streamlit
excerpt: "Built The Setlist, a Streamlit app that syncs with Spotify and surfaces upcoming concerts from Ticketmaster and SeatGeek that match a listener’s taste."
---

The Setlist is a personalized concert recommendation app designed to bridge the gap between streaming and live shows. The app connects to Spotify to pull a user’s top artists and saved albums, then matches that profile to upcoming concerts using the Ticketmaster and SeatGeek APIs.

On the front end, Streamlit provides a simple, interactive UI with a Tinder-style swiping experience for artists. Users can quickly indicate which artists they’re excited to see, filter by market or date range, and explore a curated list of shows tailored to their listening history.

Under the hood, the app handles authentication, rate-limited API calls, and data alignment between Spotify artist metadata and ticketing platforms. The recommendation logic combines artist overlap, popularity, and show proximity to rank events, and the entire workflow runs in Python, making it easy to iterate on both the model and the user experience as new data and feedback come in.
