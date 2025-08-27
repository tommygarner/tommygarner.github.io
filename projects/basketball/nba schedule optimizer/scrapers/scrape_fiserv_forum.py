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

# Load the Fiserv Forum URL from the Excel sheet
venue_events = pd.read_excel('venue_events.xlsx')
fiserv_url = venue_events.loc[venue_events['Venue'].str.contains('Fiserv Forum', case=False, na=False), 'Website']
fiserv_url_value = fiserv_url.iloc[0] if not fiserv_url.empty else None

if not fiserv_url_value:
    print("Fiserv Forum URL not found in the Excel sheet.")
    exit()

# Define the venue name
venue_name = "Fiserv Forum"

# Configure Selenium WebDriver
options = Options()
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
driver = webdriver.Chrome(options=options)

def get_current_month_year():
    """Extract the current month and year from the calendar header."""
    try:
        header = driver.find_element(By.CSS_SELECTOR, '.ch_calendar-header .month_name').text
        current_month = datetime.strptime(header, "%B %Y")
        return current_month
    except Exception as e:
        print(f"DEBUG: Error extracting current month - {e}")
        return None

def navigate_to_next_month():
    """Click the 'Next' button to navigate to the next month."""
    try:
        next_button = driver.find_element(By.CSS_SELECTOR, '.ch_calendar-header .cal-next')
        next_button.click()
        time.sleep(2)  # Allow the page to load
    except Exception as e:
        print(f"DEBUG: Error navigating to the next month - {e}")

def extract_events_from_calendar():
    """Scrape events from the calendar view."""
    events_data = []

    # Get the current month and year
    current_month = get_current_month_year()
    if not current_month:
        return events_data

    # Loop through months until the end_date_filter is reached
    while current_month and current_month <= end_date_filter:
        try:
            # Locate all day elements
            day_elements = driver.find_elements(By.CSS_SELECTOR, ".ch_calendar-day")

            for day_element in day_elements:
                try:
                    # Extract event date
                    date_str = day_element.get_attribute("data-fulldate")
                    event_date = datetime.strptime(date_str, "%m-%d-%Y")

                    # Skip dates outside the range
                    if not (start_date_filter <= event_date <= end_date_filter):
                        continue

                    # Locate events within this day
                    event_items = day_element.find_elements(By.CSS_SELECTOR, ".event_item")

                    for item in event_items:
                        try:
                            # Extract event details
                            event_title_raw = item.find_element(By.CSS_SELECTOR, ".desc h3 a").text.strip()
                            event_title = event_title_raw.title()  # Standardize title case
                            event_time = item.find_element(By.CSS_SELECTOR, ".showings.time").text.strip()
                            event_link = item.find_element(By.CSS_SELECTOR, ".desc h3 a").get_attribute("href")

                            # Append event details to the list
                            events_data.append({
                                "Venue": venue_name,
                                "Title": event_title,
                                "Date": event_date.strftime("%Y-%m-%d"),
                                "Time": event_time,
                                "Link": event_link,
                            })
                        except Exception as e:
                            print(f"DEBUG: Error processing event item - {e}")
                except Exception as e:
                    # Skip problematic day elements
                    pass
        except Exception as e:
            print(f"DEBUG: Error processing month - {e}")

        # Navigate to the next month
        navigate_to_next_month()
        current_month = get_current_month_year()

    return events_data


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

# Start scraping events from Fiserv Forum calendar
driver.get(fiserv_url_value)

events_data = extract_events_from_calendar()

# Save the scraped events to Fiserv Forum Excel file
save_events_to_excel(events_data, 'fiserv_forum_events.xlsx')

# Append the events to all_venue_events.xlsx
append_events_to_all_venue_events(events_data)

# Close the driver
driver.quit()
