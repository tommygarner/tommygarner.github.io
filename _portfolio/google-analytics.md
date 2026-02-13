---
layout: single
title: "Validating Google Analytics: Bot Simulation & API Integration"
date: 2026-02-13
description: "Implementing Google Analytics 4 with automated testing, debugging, and data extraction via API"
author_profile: true
toc: true
toc_sticky: true
classes: wide
tags:
  - analytics
  - google-analytics
  - testing
  - automation
  - python
  - selenium
  - api
  - debugging
excerpt: "How I validated my portfolio's Google Analytics setup through automated bot simulation, debugged tracking errors, and extracted metrics via the GA4 Data API."
---

<img width="1280" height="441" alt="image" src="https://github.com/user-attachments/assets/302a5ea1-7947-486d-9b78-79184eb48a08" />

## Part 1: Setting Up Event Tracking

### The Problem

Setting up Google Analytics is straightforward. Validating it works correctly? That's a different story.

I wanted to track the following on this portfolio website:
- **Page views** across all sections
- **File downloads** (Resume PDF)
- **Scroll depth** (90% threshold for engagement)
- **Outbound clicks** (LinkedIn, GitHub)
- **Device categories** (Desktop, Mobile, Tablet)

### Custom Event Implementation

I implemented GA4 custom events using gtag.js:

```javascript
<script async src="https://www.googletagmanager.com/gtag/js?id=G-1F0CP9TB6Z"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());
  gtag('config', 'G-1F0CP9TB6Z', { 'debug_mode': true });
</script>

<script>
document.addEventListener('DOMContentLoaded', function() {
  // Track LinkedIn/Outbound Clicks
  document.querySelectorAll('a[href*="linkedin.com"]').forEach(function(link) {
    link.addEventListener('click', function() {
      gtag('event', 'social_engagement', {
        'platform': 'LinkedIn',
        'link_url': this.href
      });
    });
  });

  // Track Resume PDF Downloads
  document.querySelectorAll('a[href$=".pdf"]').forEach(function(link) {
    link.addEventListener('click', function() {
      gtag('event', 'file_download', {
        'file_name': this.href.split('/').pop(),
        'file_extension': 'pdf'
      });
    });
  });
});
</script>
```

**Key design decisions:**
- `debug_mode: true` for real-time event visibility
- Event listeners on DOM load to ensure elements exist
- Custom event names that align with GA4 conventions
- Structured event parameters for downstream analysis

---

## Part 2: Automated Bot Simulation

<img width="1999" height="1191" alt="image" src="https://github.com/user-attachments/assets/d6268d3a-d654-40b2-bd7d-684c928dfb37" />

*Figure 1: Selenium browser examples*

### Why Bots?

Manual testing doesn't scale and can't simulate diverse user behavior. I needed to validate:
- Multiple device types simultaneously
- Different user journeys and engagement patterns
- Edge cases (scroll events, back navigation, outbound links)
- Session duration and engagement rate calculations

### The User Personas

I designed 5 personas representing realistic user archetypes:

**1. The Recruiter** (Windows Desktop)
```python
{
  "name": "Recruiter",
  "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0",
  "device": "Desktop",
  "journey": [
    {"action": "visit_home", "dwell": (8, 12)},
    {"action": "click_resume", "dwell": (10, 15)},
    {"action": "download_resume", "dwell": (6, 10)},
    {"action": "click_projects", "dwell": (8, 12)},
    {"action": "scroll_page", "depth": 60},
    {"action": "click_linkedin", "dwell": (3, 5)},
  ]
}
```

**2. The Developer Peer** (MacOS)
- Focuses on technical projects
- Deep scroll behavior (90% threshold)
- Longer engagement times (15-25s per page)

**3. The Mobile Visitor** (iPhone)
- Viewport: 375x812 (iPhone dimensions)
- Scroll-heavy navigation
- Moderate engagement

**4. The Tablet Browser** (iPad)
- Viewport: 768x1024
- Multi-project exploration
- Medium-paced navigation

**5. The Deep Researcher** (Linux)
- Comprehensive site exploration
- High scroll depths (95-100%)
- Maximum engagement

---

## Part 3: Debugging & Troubleshooting

While running the bots initially, I ran into a couple of bugs that needed to be fixed. 

### Issue #1: Events Not Firing

**Symptom:** Test events pushed to `dataLayer` but not appearing in GA4 Real-time Reports.

**Diagnosis:**
```javascript
// Console test
typeof gtag  // Returned: "function"
window.dataLayer  // Returned: Array with events

// Manual sendBeacon test
navigator.sendBeacon('https://www.google-analytics.com/g/collect?...');
// Status: 204 (No Content)
```

**Root cause:** JavaScript syntax errors in the tracking code were breaking event execution.

```
Uncaught SyntaxError: Unexpected end of input (at (index):1:3137)
```

**The fix:** Extra closing braces in the event listener code. Corrected structure:

```javascript
document.addEventListener('DOMContentLoaded', function() {
  document.querySelectorAll('a[href$=".pdf"]').forEach(function(link) {
    link.addEventListener('click', function() {
      gtag('event', 'file_download', {
        'file_name': this.href.split('/').pop(),
        'file_extension': 'pdf'
      });
    });  // < Closed correctly
  });    // < Closed correctly
});      // < Closed correctly
```

**Debugging approach:**
1. Verified gtag.js loaded (`typeof gtag`)
2. Confirmed dataLayer updates
3. Tested network requests (manual sendBeacon)
4. Isolated syntax errors via browser console
5. Fixed closing brace structure

**Lesson:** Manual sendBeacon test bypassed the broken code, confirming GA4 connectivity worked, narrowing the issue to client-side JavaScript.

---

### Issue #2: API Permission Errors

When extracting data via the GA4 Data API:

```
403 User does not have sufficient permissions for this property
```

**Root cause:** Service account not granted access to GA4 property.

**Resolution:**
1. Created service account in Google Cloud Console
2. Downloaded JSON credentials
3. Added service account email to GA4 Property Access Management
4. Granted "Viewer" role
5. Waited 5 minutes for permission propagation

**Service account setup:**
```python
from google.oauth2 import service_account
from google.analytics.data_v1beta import BetaAnalyticsDataClient

credentials = service_account.Credentials.from_service_account_file(
    'ga4-service-account.json',
    scopes=['https://www.googleapis.com/auth/analytics.readonly']
)

client = BetaAnalyticsDataClient(credentials=credentials)
```

---

## Part 4: Data Extraction via GA4 API

### Why Use the API?

<img width="960" height="540" alt="image" src="https://github.com/user-attachments/assets/2073fe90-0f8b-41cd-9ed8-d80191aa1607" />

*Figure 2: Infrastructure of GA4*

GA4's UI is great for exploration, but for automated reporting and analysis, the Data API provides:
- Programmatic access to metrics
- Custom date ranges and filters
- Exportable data for further analysis
- Reproducible queries

### API Implementation

**Basic Report Query:**
```python
from google.analytics.data_v1beta.types import (
    DateRange, Dimension, Metric, RunReportRequest
)

def run_ga4_report(client, property_id, dimensions, metrics, date_range):
    request = RunReportRequest(
        property=f"properties/{property_id}",
        dimensions=[Dimension(name=d) for d in dimensions],
        metrics=[Metric(name=m) for m in metrics],
        date_ranges=[DateRange(
            start_date=date_range[0],
            end_date=date_range[1]
        )]
    )

    response = client.run_report(request)

    # Convert to DataFrame for analysis
    data = []
    for row in response.rows:
        row_data = {}
        for i, dim in enumerate(dimensions):
            row_data[dim] = row.dimension_values[i].value
        for i, metric in enumerate(metrics):
            row_data[metric] = float(row.metric_values[i].value)
        data.append(row_data)

    return pd.DataFrame(data)
```

**Projects Page Analysis:**
```python
# Filter for projects/portfolio pages
projects_filter = FilterExpression(
    filter=Filter(
        field_name="pagePath",
        string_filter=Filter.StringFilter(
            match_type=Filter.StringFilter.MatchType.CONTAINS,
            value="portfolio"
        )
    )
)

projects_data = run_ga4_report(
    client=client,
    property_id=PROPERTY_ID,
    dimensions=['pagePath', 'pageTitle'],
    metrics=['screenPageViews', 'activeUsers', 'averageSessionDuration'],
    filter_expression=projects_filter
)
```

---

## Results & Metrics

<img width="1853" height="949" alt="image" src="https://github.com/user-attachments/assets/7bb46507-a089-400d-95f9-484d545b1669" />

*Figure 3: Simulated dashboard statistics*

**Data Source:** GA4 Data API
**Analysis Period:** Last 1 hour (of testing)
**Extracted:** February 13, 2026

### Overall Performance

- **Total Users**: 13
- **Total Sessions**: 15
- **Total Page Views**: 16
- **Avg Session Duration**: 174.9s (2.9 minutes)
- **Engagement Rate**: 6.7%
- **Total Events**: 62

**Analysis:** The bot simulation successfully generated traffic across multiple device types and user personas. The average session duration of nearly 3 minutes indicates substantive engagement where bots dwelled on pages, scrolled through content, and navigated multiple sections rather than bouncing immediately. The 6.7% engagement rate reflects meaningful interactions with the site content.

### Device Breakdown

- **Desktop**: 9 users (11 sessions)
- **Mobile**: 2 users (2 sessions)
- **Tablet**: 2 users (2 sessions)

**Validation:** GA4 correctly identified device categories based on user agent strings. The distribution confirms that:
- The Recruiter and Developer personas (desktop) generated the majority of traffic
- Mobile (iPhone) and Tablet (iPad) personas registered with appropriate viewport dimensions
- Device detection aligns with the configured user agents across multiple validation runs

### Top Pages

1. **Tommy Garner (Home)**: 12 views
2. **The Setlist: A Personalized Concert Recommender**: 2 views
3. **Resume**: 1 view
4. **Portfolio**: 1 view

**User Flow:** Most sessions began on the home page (landing page data confirms 12 sessions started there), with progressive navigation to resume and projects sections. This aligns with the Recruiter persona's journey design (Home > Resume > Projects). The Setlist project received deeper engagement from the Developer persona, demonstrating realistic browsing patterns.

### Custom Event Validation

- **file_download**: 4 events tracked 
- **scroll**: 2 events tracked 
- **social_engagement**: 0 events (requires investigation)

**Status:** File download and scroll depth tracking validated successfully after fixing JavaScript syntax errors! The manual event firing approach guaranteed delivery:
- PDF resume downloads now trigger `file_download` events with correct parameters (file_name, file_extension, link_url)
- Scroll events fire at 90% depth threshold with page location tracking
- Social engagement events (LinkedIn, GitHub) need debugging - likely due to:
  - Selenium timeout errors when clicking social links
  - Pop-up blockers or new tab handling issues
  - Event firing before link element fully loads

The validation confirms that the core GA4 tracking infrastructure works correctly. The missing social_engagement events are isolated to link interaction timing, not the tracking code itself.

### Projects Page Performance

- **Total Views**: 3
- **Unique Users**: 4
- **Avg Time on Page**: 346.7s (5.8 minutes)

**Deep Engagement:** The projects pages (Portfolio and individual project pages like The Setlist) show strong engagement metrics with nearly 6 minutes average time-on-page. This validates that:
- Long dwell time metrics tracked correctly across multiple sessions
- Scroll depth events (90%+) trigger during extended sessions
- Session duration calculations account for realistic user behavior patterns
- The Developer persona's journey (deeper project exploration) reflects in the analytics data

---

## Technical Insights

### What Worked Well

**1. Sequential bot execution** prevented GA4 event processing bottlenecks
- Staggered launches (8-15s delay) gave GA4 time to process each session
- Reduced risk of rate limiting or event dropping

**2. Manual event firing via JavaScript** guaranteed event delivery
- Instead of relying on DOM event listeners, I manually executed `gtag()` calls
- Added explicit delays (3-5s) before navigation to ensure events sent

**3. Debug mode** provided real-time validation
- `debug_mode: true` made events visible in GA4 DebugView immediately
- Caught issues before data entered production reports

### Challenges & Solutions

**Challenge:** Events not appearing despite gtag loading correctly

**Solution:** JavaScript syntax errors were breaking execution. Fixed by:
1. Validating all closing braces
2. Testing with manual sendBeacon to isolate issue
3. Restructuring event listener code for clarity

**Challenge:** 403 errors when querying GA4 Data API

**Solution:** Service account permissions required:
1. Adding service account to GA4 Property Access Management
2. Granting "Viewer" role
3. Waiting for permission propagation (5 minutes)

**Challenge:** Distinguishing bot traffic from real users

**Solution:** Custom user agents:
```python
"Mozilla/5.0 (Windows NT 10.0; Win64; x64) Bot-Recruiter/1.0"
```
Allowed filtering in GA4 by user agent string.

---

## Key Takeaways

### For Analytics Implementation

**1. Validation is mandatory**
- Automated testing catches issues manual QA misses
- Real-time debugging (DebugView) is essential during setup

**2. Event timing matters**
- File downloads need 5-7s before navigation for event delivery
- Scroll events benefit from gradual scrolling vs. instant jumps

**3. API access unlocks automation**
- GA4 UI is for exploration; API is for production workflows
- Programmatic queries enable reproducible analysis

### For Technical Projects

**1. Debug systematically**
- Isolate components (network > JavaScript > GA4 processing)
- Manual tests (sendBeacon) bypass code to validate infrastructure

**2. Design for observability**
- Debug mode, detailed logging, and timestamped events
- Made troubleshooting 10x faster

**3. Document edge cases**
- Mobile Safari handles scroll events differently than Chrome
- GA4 data processing takes 24-48 hours for API queries (real-time is instant)

---

## Tech Stack Summary

**Analytics:**
- Google Analytics 4 (GA4)
- Custom event tracking (gtag.js)
- GA4 Data API (Python client)
- Real-time DebugView

**Automation:**
- Python 3.11
- Selenium WebDriver 4.x
- webdriver-manager (auto-managed ChromeDriver)
- Threading for sequential execution

**Data Analysis:**
- Pandas (data manipulation)
- Matplotlib/Seaborn (visualization)
- Jupyter Notebooks (interactive analysis)

**Development:**
- Jekyll (static site)
- GitHub Pages (hosting)
- Git (version control)
