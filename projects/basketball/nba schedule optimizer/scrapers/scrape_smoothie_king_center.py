import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from datetime import datetime
import os

# Define the date range for filtering events
start_date_filter = datetime(2025, 4, 14)
end_date_filter = datetime(2025, 7, 31)

# Load the Smoothie King Center URL from the Excel sheet
venue_events = pd.read_excel('venue_events.xlsx')
smoothie_king_center_url = venue_events.loc[venue_events['Venue'].str.contains('Smoothie King Center', case=False, na=False), 'Website']
smoothie_king_center_url_value = smoothie_king_center_url.iloc[0] if not smoothie_king_center_url.empty else None

if not smoothie_king_center_url_value:
    print("Smoothie King Center URL not found in the Excel sheet.")
    exit()

# Define the venue name
venue_name = "Smoothie King Center"

# Configure Selenium WebDriver
options = Options()
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
driver = webdriver.Chrome(options=options)

def extract_events_from_list():
    """Scrape events from the `.list` class, handling date ranges and extracting times from event pages using new browser windows."""
    events_data = []
    current_page_url = smoothie_king_center_url_value

    while current_page_url:
        driver.get(current_page_url)
        time.sleep(2)  # Allow the page to load

        # Locate all event entries on the page
        event_entries = driver.find_elements(By.CSS_SELECTOR, "#list .entry")

        for entry in event_entries:
            try:
                # Extract event title
                event_title_raw = entry.find_element(By.CSS_SELECTOR, ".info h3 a").text.strip()
                event_title = event_title_raw.title()  # Standardize title case

                # Extract event link
                event_link = entry.find_element(By.CSS_SELECTOR, ".info h3 a").get_attribute("href")

                # Extract event date
                month = entry.find_element(By.CSS_SELECTOR, ".date .m").text.strip()
                day = entry.find_element(By.CSS_SELECTOR, ".date .d").text.strip()
                year_element = entry.find_element(By.CSS_SELECTOR, ".date .y").text.strip()
                year = year_element if year_element else str(datetime.now().year)

                # Handle date ranges
                if "-" in day:
                    start_day, end_day = map(str.strip, day.split("-"))
                    start_date = datetime.strptime(f"{month} {start_day}, {year}", "%b %d, %Y")
                    end_date = datetime.strptime(f"{month} {end_day}, {year}", "%b %d, %Y")
                else:
                    start_date = datetime.strptime(f"{month} {day}, {year}", "%b %d, %Y")
                    end_date = start_date

                # Skip dates outside the range
                if end_date < start_date_filter or start_date > end_date_filter:
                    continue

                # Process event link in a new browser window
                event_showings = scrape_event_showings(event_title, event_link, start_date, end_date)
                events_data.extend(event_showings)

            except Exception as e:
                print(f"Error processing event entry - {e}")

        # Check for the next page
        try:
            next_page_element = driver.find_element(By.CSS_SELECTOR, ".paging .next")
            current_page_url = next_page_element.get_attribute("href")
        except:
            current_page_url = None  # No more pages to navigate

    return events_data

def scrape_event_showings(event_title, event_link, start_date, end_date):
    """Scrape event showings by opening the event link in a new browser window."""
    showings_data = []
    try:
        # Open a new browser window for the event link
        event_driver = webdriver.Chrome(options=options)
        event_driver.get(event_link)
        time.sleep(2)  # Allow the page to load

        # Locate showings for the event
        showings = event_driver.find_elements(By.CSS_SELECTOR, ".showings .entry")
        for showing in showings:
            try:
                showing_date = datetime.strptime(showing.find_element(By.CSS_SELECTOR, ".date").text.strip(), "%B %d, %Y")
                showing_time = showing.find_element(By.CSS_SELECTOR, ".time").text.strip()

                # Remove "at " prefix from the time
                if showing_time.startswith("at "):
                    showing_time = showing_time[3:].strip()

                # Only include dates within the range
                if start_date_filter <= showing_date <= end_date_filter:
                    showings_data.append({
                        "Venue": venue_name,
                        "Title": event_title,
                        "Date": showing_date.strftime("%Y-%m-%d"),
                        "Time": showing_time,
                        "Link": event_link,
                    })
            except Exception as e:
                print(f"Error processing showing: {e}")

        # Close the event driver
        event_driver.quit()

    except Exception as e:
        print(f"Error scraping event showings: {e}")

    return showings_data

def save_events_to_excel(events_data, file_name):
    """Save events to the specified Excel file."""
    events_df = pd.DataFrame(events_data)
    events_df.to_excel(file_name, index=False)
    print(f"Events have been saved to {file_name}.")

def append_events_to_all_venue_events(events_data):
    """Append the events to the 'all_venue_events.xlsx' file."""
    all_venue_events_file = 'all_venue_events.xlsx'

    # Check if the file exists and append data
    if os.path.exists(all_venue_events_file):
        all_venue_events = pd.read_excel(all_venue_events_file)
    else:
        all_venue_events = pd.DataFrame()  # Create an empty DataFrame if the file doesn't exist

    # Convert events_data to a DataFrame before appending
    new_events_df = pd.DataFrame(events_data)

    # Append the new data to the existing DataFrame
    all_venue_events = pd.concat([all_venue_events, new_events_df], ignore_index=True)

    # Save the updated DataFrame back to the Excel file
    all_venue_events.to_excel(all_venue_events_file, index=False)
    print(f"Events have been appended to {all_venue_events_file}.")

# Start scraping events from Smoothie King Center calendar
driver.get(smoothie_king_center_url_value)

events_data = extract_events_from_list()

# Save the scraped events to Smoothie King Center Excel file
save_events_to_excel(events_data, 'smoothie_king_center_events.xlsx')

# Append the events to all_venue_events.xlsx
append_events_to_all_venue_events(events_data)

# Close the driver
driver.quit()
