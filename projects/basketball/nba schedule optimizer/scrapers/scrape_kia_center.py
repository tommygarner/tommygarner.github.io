import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import re
import traceback
import os

# Define the date range for filtering events
start_date_filter = datetime(2025, 4, 14)
end_date_filter = datetime(2025, 7, 31)

# Month abbreviation to full name mapping
month_abbr = {
    "Jan": "January", "Feb": "February", "Mar": "March", "Apr": "April", "May": "May", "Jun": "June", 
    "Jul": "July", "Aug": "August", "Sep": "September", "Oct": "October", "Nov": "November", "Dec": "December"
}

# Load the Kia Center URL from the Excel sheet
venue_events = pd.read_excel('venue_events.xlsx')
kia_center_url = venue_events.loc[venue_events['Venue'].str.contains('Kia Center', case=False, na=False), 'Website']
kia_center_url_value = kia_center_url.iloc[0] if not kia_center_url.empty else None

if not kia_center_url_value:
    print("Kia Center URL not found in the Excel sheet.")
    exit()

# Set up Chrome options for headless mode (no UI)
options = Options()
driver = webdriver.Chrome(options=options)

def dismiss_obstructions():
    """Dismiss cookie banners or other obstructions."""
    try:
        WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.ID, 'onetrust-banner-sdk')))
        accept_button = driver.find_element(By.ID, 'onetrust-accept-btn-handler')
        accept_button.click()
    except Exception:
        #print("Cookie banner not found or already dismissed.")
        pass

def clean_date(date_str):
    """Clean up date string by removing extra spaces, commas, and handling invalid values."""
    date_str = re.sub(r'\s+', ' ', date_str).strip()  # Clean multiple spaces
    date_str = date_str.replace(',', '')  # Remove commas
    date_str = date_str.replace('/', '')  # Remove slashes

    # Fix common month typos using regex
    typos = {"Junee": "June", "Julyy": "July"}
    for typo, correct in typos.items():
        date_str = re.sub(typo, correct, date_str, flags=re.IGNORECASE)

    # Map abbreviated months (Jan, Feb, etc.) to full month names
    for abbr, full in month_abbr.items():
        date_str = re.sub(rf"\b{abbr}\b", full, date_str, flags=re.IGNORECASE)

    # Skip invalid dates like '00'
    if '00' in date_str:
        return None

    return date_str


def find_event_cards(soup):
    """Find all event cards on the page."""
    return soup.find_all('div', class_='eventItem')

def click_load_more_events():
    """Handle the 'Load More Events' button if available."""
    try:
        load_more_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, 'loadMoreEvents')))
        driver.execute_script("arguments[0].scrollIntoView(true);", load_more_button)
        driver.execute_script("arguments[0].click();", load_more_button)
        time.sleep(2)
        return True
    except Exception:
        #print("No more 'Load More Events' button found.")
        return False

def extract_event_details(event):
    try:
        title = event.find('h3', class_='title').get_text(strip=True)
        link = event.find('a', title="More Info")['href']
        date_div = event.find('div', class_='date')
        dates = []

        if not date_div:
            print(f"Skipping event due to missing date div: {title}")
            return None

        month = date_div.find('span', class_='m-date__month').get_text(strip=True)
        day = date_div.find('span', class_='m-date__day').get_text(strip=True).zfill(2)
        year = date_div.find('span', class_='m-date__year').get_text(strip=True).strip(',')

        # Skip invalid dates like "00"
        date_str = f"{month} {day} {year}"
        clean_date_str = clean_date(date_str)

        if not clean_date_str:
            print(f"Skipping event due to invalid day: {title}")
            return None

        try:
            date = datetime.strptime(clean_date_str, "%B %d %Y")
        except ValueError:
            print(f"Error parsing single date: {month} {day}, {year}")
            return None

        if start_date_filter <= date <= end_date_filter:
            dates = [date.strftime("%Y-%m-%d")]

            # Check for duplicate events
            unique_id = (title, dates[0])  # Unique identifier: (title, date)
            if unique_id in processed_events:
                #print(f"Duplicate event detected, skipping: {title} on {dates[0]}")
                return None

            processed_events.add(unique_id)  # Add to the set of processed events

            # Extract time from the More Info link
            event_time = extract_event_time_from_link_in_window(link)

            return [{"Venue": "Kia Center", "Title": title, "Date": date, "Time": event_time, "Link": link} for date in dates]

    except Exception as e:
        print(f"Error extracting event details for {title}: {e}")
        print(traceback.format_exc())
        return None
    
def extract_event_time_from_link_in_window(event_link):
    """Open the event's More Info link in a new browser window and extract the event time."""
    # Open a new window using JavaScript
    driver.execute_script(f"window.open('{event_link}', '_blank', 'width=800,height=600');")
    driver.switch_to.window(driver.window_handles[-1])  # Switch to the new window

    try:
        # Wait for the element containing the time to load
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'showings_date')))
        page_source = driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')

        # Extract the time
        time_element = soup.find('span', class_='time')
        event_time = time_element.get_text(strip=True) if time_element else "TBD"

        #print(f"Extracted time: {event_time}")
        return event_time

    except Exception as e:
        #print(f"Error extracting event time: {e}")
        return "TBD"

    finally:
        driver.close()  # Close the current window
        driver.switch_to.window(driver.window_handles[0])  # Switch back to the original window



# Start scraping
driver.get(kia_center_url_value)
dismiss_obstructions()

events_data = []
processed_events = set()


try:
    while True:
        WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.CLASS_NAME, 'eventItem')))
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        events = find_event_cards(soup)

        for event in events:
            event_details = extract_event_details(event)
            if event_details:
                events_data.append(event_details)

        if not click_load_more_events():
            break

finally:
    driver.quit()

# Flatten the list of event details
flattened_events = [event for sublist in events_data for event in sublist]

# Convert the flattened list to a DataFrame
df = pd.DataFrame(flattened_events)

# Ensure each column (Venue, Title, Date, Time, Link) is separate
if not df.empty:
    output_file = 'kia_center_events.xlsx'
    df.to_excel(output_file, index=False)
    print(f"Scraped data saved to {output_file}.")

    # Append the scraped events to all_venue_events.xlsx
    all_venue_events_file = 'all_venue_events.xlsx'

    # Check if the file exists, and if it does, load it
    if os.path.exists(all_venue_events_file):
        all_venue_events = pd.read_excel(all_venue_events_file)
    else:
        all_venue_events = pd.DataFrame()  # Create an empty DataFrame if the file doesn't exist

    # Append the new data to the existing DataFrame
    all_venue_events = pd.concat([all_venue_events, df], ignore_index=True)

    # Save the updated DataFrame back to the Excel file
    all_venue_events.to_excel(all_venue_events_file, index=False)

    print(f"Events have been added to {all_venue_events_file}.")
else:
    print("No data to save.")


