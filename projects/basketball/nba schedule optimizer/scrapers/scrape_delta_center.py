import time
import json
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from datetime import datetime
import os

# Define the date range for filtering events
start_date_filter = datetime(2025, 4, 14)
end_date_filter = datetime(2025, 7, 31)

# Load the Delta Center URL from the Excel sheet
venue_events = pd.read_excel('venue_events.xlsx')
delta_center_url = venue_events.loc[venue_events['Venue'].str.contains('Delta Center', case=False, na=False), 'Website']
delta_center_url_value = delta_center_url.iloc[0] if not delta_center_url.empty else None

if not delta_center_url_value:
    print("Delta Center URL not found in the Excel sheet.")
    exit()

# Define the venue name
venue_name = "Delta Center"

# Configure Selenium WebDriver
options = Options()
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
driver = webdriver.Chrome(options=options)

# Function to load all events by clicking "Load More"
def load_all_events():
    while True:
        try:
            # Scroll to the "Load More" button
            load_more_button = driver.find_element(By.CSS_SELECTOR, ".mec-load-more-wrap .mec-load-more-button")
            ActionChains(driver).move_to_element(load_more_button).perform()

            # Click the button
            load_more_button.click()
            time.sleep(3)  # Wait for more events to load
        except Exception:
            # Suppress "No more Load More button" messages
            break

# Function to extract event data
def extract_event_data():
    events = set()  # Use a set to ensure unique events

    # Load the Delta Center URL
    driver.get(delta_center_url_value)
    time.sleep(5)  # Allow the page to load fully

    # Load all events by clicking "Load More" button
    load_all_events()

    # Find all rows of events
    event_rows = driver.find_elements(By.CSS_SELECTOR, "div.row div.col-md-4")

    for event in event_rows:
        try:
            # Extract JSON block
            json_block = event.find_element(By.CSS_SELECTOR, "script[type='application/ld+json']").get_attribute("innerHTML")
            event_data = json.loads(json_block)

            # Extract details
            event_name = event_data.get("name", "N/A").strip()
            start_date = event_data.get("startDate", "N/A").strip()
            event_url = event_data.get("url", "N/A").strip()
            time_details = None

            # Parse the date and filter by range
            try:
                event_date = datetime.strptime(start_date, "%Y-%m-%d")
                if not (start_date_filter <= event_date <= end_date_filter):
                    continue  # Skip events outside the date range
            except ValueError:
                continue  # Skip events with invalid dates

            # Extract time from visible content if available
            try:
                time_details = event.find_element(By.CSS_SELECTOR, "span.mec-start-time").text.strip()
            except Exception:
                pass

            # Create a tuple to represent the event (used for uniqueness)
            event_tuple = (event_name, start_date, time_details, event_url)

            # Append to the set if unique
            if event_tuple not in events:
                events.add(event_tuple)

        except Exception:
            # Suppress errors related to missing JSON blocks or elements
            continue

    # Convert set to list of dictionaries
    event_list = [
        {
            "Venue": venue_name,
            "Title": name,
            "Date": date,
            "Time": time or "N/A",
            "Link": link,
        }
        for name, date, time, link in events
    ]

    # Sort events by date
    event_list.sort(key=lambda x: datetime.strptime(x["Date"], "%Y-%m-%d"))

    return event_list

# Save events to a specific file
def save_events_to_excel(event_list, file_name):
    """Save events to the specified Excel file."""
    events_df = pd.DataFrame(event_list)
    events_df.to_excel(file_name, index=False)
    print(f"Events have been saved to {file_name}.")

# Append events to all_venue_events.xlsx
def append_events_to_all_venue_events(event_list):
    """Append the events to the 'all_venue_events.xlsx' file."""
    all_venue_events_file = 'all_venue_events.xlsx'

    # Check if the file exists and append data
    if os.path.exists(all_venue_events_file):
        all_venue_events = pd.read_excel(all_venue_events_file)
    else:
        all_venue_events = pd.DataFrame()  # Create an empty DataFrame if the file doesn't exist

    # Convert events_data to a DataFrame before appending
    new_events_df = pd.DataFrame(event_list)

    # Append the new data to the existing DataFrame
    all_venue_events = pd.concat([all_venue_events, new_events_df], ignore_index=True)

    # Drop duplicates
    all_venue_events.drop_duplicates(inplace=True)

    # Save the updated DataFrame back to the Excel file
    all_venue_events.to_excel(all_venue_events_file, index=False)
    print(f"Events have been appended to {all_venue_events_file}.")

# Run the scraper
driver.get(delta_center_url_value)
events_data = extract_event_data()

# Save the scraped events to Delta Center Excel file
save_events_to_excel(events_data, 'delta_center_events.xlsx')

# Append the events to all_venue_events.xlsx
append_events_to_all_venue_events(events_data)

# Close the browser
driver.quit()
