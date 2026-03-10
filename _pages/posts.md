---
title: "Blog"
permalink: /posts/
layout: archive
author_profile: true
---

{% include base_path %}

{% for post in site.posts %}
  {% unless post.series == "seatdata" %}
    {% include archive-single.html %}
  {% endunless %}
{% endfor %}
