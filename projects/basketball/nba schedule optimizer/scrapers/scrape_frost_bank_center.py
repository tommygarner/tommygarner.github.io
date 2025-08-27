import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import re
import traceback
import os
import logging

# Suppress warnings and error messages from TensorFlow or Selenium
logging.getLogger("tensorflow").setLevel(logging.ERROR)

# Define date filters
start_date_filter = datetime(2025, 4, 14)
end_date_filter = datetime(2025, 7, 31)

# Month abbreviation to full name mapping
month_abbr = {
    "Jan": "January", "Feb": "February", "Mar": "March", "Apr": "April", "May": "May", "Jun": "June",
    "Jul": "July", "Aug": "August", "Sep": "September", "Oct": "October", "Nov": "November", "Dec": "December"
}

# Load the venue URL from the Excel sheet
venue_events = pd.read_excel('venue_events.xlsx')
frost_bank_center_url = venue_events.loc[venue_events['Venue'].str.contains('Frost Bank Center', case=False, na=False), 'Website']
frost_bank_center_url_value = frost_bank_center_url.iloc[0] if not frost_bank_center_url.empty else None

if not frost_bank_center_url_value:
    print("Venue URL not found in the Excel sheet.")
    exit()

# Setup Chrome options
options = Options()
options.add_argument('--disable-gpu')
options.add_argument('--window-size=1920,1080')

driver = webdriver.Chrome(options=options)

def dismiss_obstructions():
    """Dismiss cookie banners or other obstructions."""
    try:
        WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.ID, 'onetrust-banner-sdk')))
        accept_button = driver.find_element(By.ID, 'onetrust-accept-btn-handler')
        accept_button.click()
    except Exception:
        pass  # No cookie banner or already dismissed

def clean_date(date_str):
    """Clean and normalize date strings."""
    for abbr, full in month_abbr.items():
        date_str = re.sub(rf"\b{abbr}\b", full, date_str, flags=re.IGNORECASE)
    return re.sub(r'\s+', ' ', date_str).strip()

def extract_showtimes_from_event_page(event_link):
    """Extract showtimes from the event page."""
    showings_data = []
    try:
        driver.get(event_link)
        WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.CLASS_NAME, 'showings_list')))
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        showings = soup.find_all('li', class_='entry')

        for showing in showings:
            date_text = showing.find('span', class_='date').get_text(strip=True)
            time_text = showing.find('span', class_='time').get_text(strip=True)
            full_date = f"{date_text} {datetime.now().year}"  # Add the year
            try:
                parsed_date = datetime.strptime(clean_date(full_date), "%A, %B %d %Y")
                showings_data.append({"Date": parsed_date.strftime("%Y-%m-%d"), "Time": time_text})
            except Exception as e:
                print(f"Error parsing date: {date_text}, {e}")
    except Exception as e:
        pass  # Suppress any errors during event extraction
    return showings_data

def extract_event_details(event):
    """Extract details from an event."""
    try:
        title = event.find('h3', class_='title').get_text(strip=True)
        link_tag = event.find('a', href=True)
        link = link_tag['href'] if link_tag else None

        date_range_tag = event.find('span', class_='m-date__rangeFirst')
        single_date_tag = event.find('span', class_='m-date__singleDate')

        if date_range_tag:
            start_month = date_range_tag.find('span', class_='m-date__month').get_text(strip=True)
            start_day = date_range_tag.find('span', class_='m-date__day').get_text(strip=True).zfill(2)
            end_day = event.find('span', class_='m-date__rangeLast').find('span', class_='m-date__day').get_text(strip=True).zfill(2)
            year = event.find('span', class_='m-date__year').get_text(strip=True).strip(',')

            start_date = datetime.strptime(clean_date(f"{start_month} {start_day} {year}"), "%B %d %Y")
            end_date = datetime.strptime(clean_date(f"{start_month} {end_day} {year}"), "%B %d %Y")

            if start_date_filter <= end_date <= end_date_filter:
                showings = extract_showtimes_from_event_page(link)
                return [{"Venue": "Frost Bank Center", "Title": title, "Date": s["Date"], "Time": s["Time"], "Link": link} for s in showings]

        elif single_date_tag:
            month = single_date_tag.find('span', class_='m-date__month').get_text(strip=True)
            day = single_date_tag.find('span', class_='m-date__day').get_text(strip=True).zfill(2)
            year = single_date_tag.find('span', class_='m-date__year').get_text(strip=True).strip(',')

            date = datetime.strptime(clean_date(f"{month} {day} {year}"), "%B %d %Y")
            if start_date_filter <= date <= end_date_filter:
                showings = extract_showtimes_from_event_page(link)
                return [{"Venue": "Frost Bank Center", "Title": title, "Date": s["Date"], "Time": s["Time"], "Link": link} for s in showings]
    except Exception as e:
        pass  # Suppress any errors during event extraction
    return []

def click_load_more_events():
    """Scroll to and click the 'Load More Events' button."""
    try:
        load_more_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "loadMoreEvents"))
        )
        actions = ActionChains(driver)
        actions.move_to_element(load_more_button).perform()
        load_more_button.click()
        time.sleep(2)
        return True
    except Exception:
        return False  # Suppress load button errors

# Start scraping
driver.get(frost_bank_center_url_value)
dismiss_obstructions()

events_data = []

try:
    while True:
        WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.CLASS_NAME, 'entry')))
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        events = soup.find_all('li', class_='entry')

        for event in events:
            details = extract_event_details(event)
            if details:
                events_data.extend(details)

        if not click_load_more_events():
            break

finally:
    driver.quit()

# Convert to DataFrame
df = pd.DataFrame(events_data)

if not df.empty:
    # Save to individual output file
    output_file = "frost_bank_center_events.xlsx"
    df.to_excel(output_file, index=False)
    print(f"Scraped data saved to {output_file}.")

    # Append to all_venue_events.xlsx
    all_venues_file = "all_venue_events.xlsx"
    if os.path.exists(all_venues_file):
        all_venues_df = pd.read_excel(all_venues_file)
    else:
        all_venues_df = pd.DataFrame()

    # Combine the new data with the existing data
    combined_df = pd.concat([all_venues_df, df], ignore_index=True)
    combined_df = combined_df.drop_duplicates(subset=['Title', 'Date', 'Venue'])

    # Save updated combined data
    combined_df.to_excel(all_venues_file, index=False)
    print(f"Events have been appended to {all_venues_file}.")
else:
    print("No events found.")
