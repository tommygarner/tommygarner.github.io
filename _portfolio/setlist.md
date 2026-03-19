---
title: "Setlist - Personalized Concert Discovery"
collection: portfolio
excerpt: "Full-stack concert discovery app that matches your Spotify taste with upcoming shows, with a Tinder-style artist swipe queue and real-time friend coordination."
date: 2025-11-23
tags:
  - recommender systems
  - live entertainment
  - react
  - fastapi
  - python
  - supabase
---
[<i class="fab fa-github" aria-hidden="true"></i> View Code on GitHub](https://github.com/tommygarner/setlist){: .btn .btn--primary}
[<i class="fas fa-play" aria-hidden="true"></i> Live Demo](https://thesetlist.streamlit.app/){: .btn}

The Setlist is a personalized concert discovery app built for music fans who want to stop missing shows by artists they actually like. It connects to your Spotify account, analyzes your listening history, and surfaces upcoming concerts ranked by how well they match your taste.

![Discover Concerts](/images/setlist-discover.png)

The core ranking system combines Spotify's short and medium-term top artist data with explicit swipe preferences to produce an affinity score for each discovered event. Artists you've liked get a boost; artists you've disliked are filtered out entirely. Scores are computed at discovery time and updated live as you swipe, so the list re-sorts without requiring a full re-fetch.

<img width="882" height="818" alt="image" src="https://github.com/user-attachments/assets/a2762e8f-3875-4dc5-af87-f3b8b8b29180" />
*Ticketmaster's Discovery API architecture*

Concert discovery fans out async requests to Ticketmaster across all of your Spotify artists in parallel using aiohttp, then deduplicates and caches results for 24 hours to stay within API rate limits. A streaming progress bar (via Server-Sent Events) shows each step in real time rather than leaving the user staring at a spinner.

![Artist Swipe](/images/setlist-swipe.png)

The app also includes an artist swipe queue that shows each artist's top tracks with album art and Spotify/YouTube links, a Music Discovery section with tabs for similar artists and surprise picks, and a friends system with direct messaging and inline concert sharing.

The project started as a Streamlit prototype and was later rebuilt as a React 18 + FastAPI application, containerized with Docker, and deployed behind nginx with SSE proxy buffering disabled for the streaming endpoint. The demo above runs the original Streamlit version.
