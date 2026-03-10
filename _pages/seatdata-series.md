---
title: "SeatData.io Series"
layout: single
permalink: /seatdata-series/
author_profile: true
---

An 11-part series documenting the full ML pipeline built on secondary ticket market data — from raw database engineering through demand forecasting models.

<details>
<summary><strong>SeatData.io Series &mdash; 11 posts (click to expand)</strong></summary>

<ul>
{% assign seatdata_posts = site.posts | where: "series", "seatdata" %}
{% for post in seatdata_posts %}
<li>
  <a href="{{ post.url | relative_url }}">{{ post.title }}</a><br>
  <small>{{ post.date | date: "%B %d, %Y" }} &mdash; {{ post.excerpt | strip_html | truncatewords: 20 }}</small>
</li>
{% endfor %}
</ul>

</details>
