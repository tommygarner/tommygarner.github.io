---
title: "SeatData.io Series"
layout: archive
permalink: /seatdata-series/
author_profile: true
---

{% include base_path %}

{% assign seatdata_posts = site.posts | where: "series", "seatdata" %}
{% for post in seatdata_posts %}
  {% include archive-single.html %}
{% endfor %}
