from bs4 import BeautifulSoup
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import time
import pandas as pd
import os

# Suppress TensorFlow Lite delegate messages
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

# Set up date range for filtering
start_date = datetime.strptime("2025-04-14", "%Y-%m-%d")
end_date = datetime.strptime("2025-07-31", "%Y-%m-%d")

def scrape_calendar_page(html):
    """
    Parse the calendar HTML and extract event links and basic info for dates within range.
    """
    soup = BeautifulSoup(html, "html.parser")
    events = []

    # Find all date blocks
    date_blocks = soup.select("div.tl-date")

    for block in date_blocks:
        try:
            # Extract the date
            event_date_str = block.get("data-fulldate")
            if not event_date_str:
                continue
            
            event_date = datetime.strptime(event_date_str, "%m-%d-%Y")
            
            # Filter by date range
            if not (start_date <= event_date <= end_date):
                continue

            # Check for events on this date
            event_items = block.select("div.event_item")
            for item in event_items:
                # Extract event title, link, and time
                title_tag = item.select_one("div.desc h3 a")
                if not title_tag:
                    continue
                
                title = title_tag.text.strip()
                link = title_tag.get("href", "No Link")

                time_tag = item.select_one("div.showings.time")
                time = time_tag.text.strip() if time_tag else "TBA"

                # Add event to the list for further inspection
                events.append({
                    "Date": event_date.strftime("%Y-%m-%d"),
                    "Time": time,
                    "Title": title,
                    "Link": link
                })
        except Exception as e:
            print(f"Error parsing event: {e}")
            continue

    return events

def verify_event_venue(events):
    """
    Open 5 event links at a time and verify if they are at Little Caesars Arena.
    """
    verified_events = []
    batch_size = 5
    drivers = []

    # Create a pool of 5 browser instances
    for _ in range(batch_size):
        drivers.append(webdriver.Chrome(options=chrome_options, service=service))

    try:
        for i in range(0, len(events), batch_size):
            batch = events[i:i + batch_size]

            # Open up to 5 event links in parallel
            for j, event in enumerate(batch):
                try:
                    drivers[j].get(event["Link"])
                    time.sleep(2)  # Allow the page to load
                except Exception as e:
                    print(f"Error opening link for event: {event['Title']} - {e}")

            # Inspect each browser tab for venue information
            for j, event in enumerate(batch):
                try:
                    page_html = drivers[j].page_source
                    soup = BeautifulSoup(page_html, "html.parser")
                    
                    # Attempt to extract venue using structure 1
                    venue_tag_1 = soup.select_one("section[aria-label='Event Header'] a.sc-1akkrr6-1")
                    venue_name_1 = venue_tag_1.text.strip().split(",")[0] if venue_tag_1 else None
                    
                    # Attempt to extract venue using structure 2
                    venue_tag_2 = soup.select_one("li.sidebar_event_venue span")
                    venue_name_2 = venue_tag_2.text.strip() if venue_tag_2 else None
                    
                    # Determine the venue
                    venue_name = venue_name_1 or venue_name_2 or "Unknown Venue"
                    
                    # Check if the venue is Little Caesars Arena
                    if venue_name == "Little Caesars Arena":
                        verified_events.append({
                            "Venue": "Little Caesars Arena",
                            "Title": event["Title"],
                            "Date": event["Date"],
                            "Time": event["Time"],
                            "Link": event["Link"]
                        })
                except Exception as e:
                    print(f"Error verifying venue for event: {event['Title']} - {e}")
    finally:
        # Close all browser instances
        for driver in drivers:
            driver.quit()

    return verified_events

def scrape_313_calendar(venue_url):
    """
    Scrape events for Little Caesars Arena from the provided URL.
    """
    driver = webdriver.Chrome(options=chrome_options, service=service)

    # Navigate to the website
    driver.get(venue_url)
    time.sleep(2)

    all_events = []

    while True:
        # Get the page source and scrape events
        page_html = driver.page_source
        events = scrape_calendar_page(page_html)
        all_events.extend(events)
        
        # Extract the current month
        try:
            current_month_element = driver.find_element(By.CSS_SELECTOR, "div.month_name")
            current_month_text = current_month_element.text.strip()
            current_date = datetime.strptime(current_month_text, "%B %Y")
        except Exception as e:
            print(f"Error extracting current month: {e}")
            break

        # Stop navigation if we have reached the end date
        if current_date > end_date:
            break

        # Click the "Next Month" button
        try:
            next_button = driver.find_element(By.CSS_SELECTOR, "div.cal-next")
            if next_button.is_enabled():
                next_button.click()
                time.sleep(2)  # Allow time for the new month to load
            else:
                break
        except Exception as e:
            print(f"No more months to navigate or error occurred: {e}")
            break

    # Quit the browser
    driver.quit()

    # Verify events are at Little Caesars Arena
    verified_events = verify_event_venue(all_events)
    return verified_events

def save_to_excel(events, filename="little_caesars_arena_events.xlsx"):
    """
    Save the scraped events to a specific Excel file and append to all_venue_events.xlsx.
    """
    # Save to the specific file
    df = pd.DataFrame(events)
    df = df[["Venue", "Title", "Date", "Time", "Link"]]  # Reorder columns
    df.to_excel(filename, index=False)
    print(f"Saved {len(events)} events to {filename}")

    # Append to all_venue_events.xlsx
    all_venues_file = "all_venue_events.xlsx"

    try:
        # Load existing data
        if os.path.exists(all_venues_file):
            existing_df = pd.read_excel(all_venues_file)

            # Combine and drop duplicates
            combined_df = pd.concat([existing_df, df]).drop_duplicates(subset=["Venue", "Title", "Date", "Time", "Link"])
            combined_df.to_excel(all_venues_file, index=False)
            print(f"Appended {len(df)} events to {all_venues_file}. Total events: {len(combined_df)}")
        else:
            # Create new file
            df.to_excel(all_venues_file, index=False)
            print(f"Created new file {all_venues_file} with {len(df)} events.")
    except Exception as e:
        print(f"Error saving to {all_venues_file}: {e}")

if __name__ == "__main__":
    # Configure Chrome options to suppress logs
    chrome_options = Options()
    chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
    service = Service()

    # Read the Excel file and get the URL for Little Caesars Arena
    venue_file = "venue_events.xlsx"
    venues = pd.read_excel(venue_file)
    
    # Filter for Little Caesars Arena
    venue_row = venues[venues["Venue"] == "Little Caesars Arena"]
    if venue_row.empty:
        print("Little Caesars Arena not found in venue_events.xlsx.")
    else:
        venue_url = venue_row.iloc[0]["Website"]
        print(f"Scraping events for Little Caesars Arena from {venue_url}")
        
        # Scrape events and save to Excel files
        scraped_events = scrape_313_calendar(venue_url)
        save_to_excel(scraped_events)

