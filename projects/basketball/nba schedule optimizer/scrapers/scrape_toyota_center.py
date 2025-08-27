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

# Load the Toyota Center URL from the Excel sheet
venue_events = pd.read_excel('venue_events.xlsx')
toyota_center_url = venue_events.loc[venue_events['Venue'].str.contains('Toyota Center', case=False, na=False), 'Website']
toyota_center_url_value = toyota_center_url.iloc[0] if not toyota_center_url.empty else None

if not toyota_center_url_value:
    print("Toyota Center URL not found in the Excel sheet.")
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
        print("Cookie banner not found or already dismissed.")

def clean_date(date_str):
    """Clean up date string by removing extra spaces, commas, and handling invalid values."""
    # Remove extra spaces, fix formatting issues like commas, and clean up the date format
    date_str = re.sub(r'\s+', ' ', date_str).strip()  # Clean multiple spaces
    date_str = date_str.replace(',', '')  # Remove commas to avoid issues

    # Fix common month typos using regex
    typos = {"Junee": "June", "Julyy": "July"}
    for typo, correct in typos.items():
        date_str = re.sub(typo, correct, date_str, flags=re.IGNORECASE)

    # Map abbreviated months (Jan, Feb, etc.) to full month names
    for abbr, full in month_abbr.items():
        date_str = re.sub(rf"\b{abbr}\b", full, date_str, flags=re.IGNORECASE)

    # Debugging: print the cleaned date string
    #print(f"Cleaned date string: {date_str}")
    
    # Skip invalid dates like '00'
    if '00' in date_str:
        return None
    
    return date_str

def scrape_multi_day_event(link):
    """Scrape the multi-day event page for individual dates and times."""
    driver.execute_script("window.open('');")
    driver.switch_to.window(driver.window_handles[-1])
    driver.get(link)

    multi_day_times = {}

    try:
        date_elements = driver.find_elements(By.CLASS_NAME, "m-date__singleDate")

        for date_element in date_elements:
            try:
                month = date_element.find_element(By.CLASS_NAME, "m-date__month").text.strip()
                day = date_element.find_element(By.CLASS_NAME, "m-date__day").text.strip().zfill(2)
                year = date_element.find_element(By.CLASS_NAME, "m-date__year").text.strip().strip(',')
                
                date_str = f"{month} {day} {year}"
                clean_date_str = clean_date(date_str)

                if clean_date_str:
                    date = datetime.strptime(clean_date_str, "%B %d %Y").strftime("%Y-%m-%d")
                    time_element = date_element.find_element(By.CLASS_NAME, "presale-time") if date_element.find_elements(By.CLASS_NAME, "presale-time") else None
                    time_str = time_element.text.strip().replace("@", "").strip() if time_element else "TBD"
                    multi_day_times[date] = time_str
            except Exception as e:
                print(f"Error parsing multi-day event date/time: {e}")
    except Exception as e:
        print(f"Error scraping multi-day event page: {e}")

    driver.close()
    driver.switch_to.window(driver.window_handles[0])

    return multi_day_times

def extract_event_details(event):
    try:
        title = event.find('h3', class_='title').get_text(strip=True)
        link = event.find('a', title="More Info")['href']
        date_div = event.find('div', class_='date')
        dates = []

        if not date_div:
            print(f"Skipping event due to missing date div: {title}")
            return None

        if date_div.find('span', class_='m-date__rangeFirst'):  # Multi-day event
            multi_day = True
            month = date_div.find('span', class_='m-date__month').get_text(strip=True)
            start_day = date_div.find('span', class_='m-date__rangeFirst').find('span', class_='m-date__day').get_text(strip=True).zfill(2)
            end_day = date_div.find('span', class_='m-date__rangeLast').find('span', class_='m-date__day').get_text(strip=True).zfill(2)
            year = date_div.find('span', class_='m-date__rangeLast').find('span', class_='m-date__year').get_text(strip=True).strip(',')

            try:
                start_date_str = f"{month} {start_day} {year}"
                end_date_str = f"{month} {end_day} {year}"
                
                start_date_clean = clean_date(start_date_str)
                end_date_clean = clean_date(end_date_str)
                
                if start_date_clean and end_date_clean:
                    start_date = datetime.strptime(start_date_clean, "%B %d %Y")
                    end_date = datetime.strptime(end_date_clean, "%B %d %Y")
                else:
                    print(f"Invalid date range: {start_date_str} - {end_date_str}")
                    return None
            except ValueError:
                print(f"Error parsing date range: {month} {start_day}-{end_day}, {year}")
                return None

            for i in range((end_date - start_date).days + 1):
                current_date = start_date + timedelta(days=i)
                if start_date_filter <= current_date <= end_date_filter:
                    dates.append(current_date.strftime("%Y-%m-%d"))

            # Scrape times for multi-day events
            if not event.find('h5', class_='time'):
                times = scrape_multi_day_event(link)
                if times:
                    return [{"Venue": "Toyota Center", "Title": title, "Date": date, "Time": times.get(date, "TBD"), "Link": link} for date in dates]
        else:  # Single-day event
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

        # Handle event time
        time_element = event.find('h5', class_='time')
        time_str = time_element.get_text(strip=True).replace("Event Starts", "").strip() if time_element else "TBD"

        return [{"Venue": "Toyota Center", "Title": title, "Date": date, "Time": time_str, "Link": link} for date in dates]

    except Exception as e:
        print(f"Error extracting event details for {title}: {e}")
        print(traceback.format_exc())
        return None

# Start scraping
driver.get(toyota_center_url_value)
dismiss_obstructions()

events_data = []
scraped_links = set()

try:
    while True:
        WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.CLASS_NAME, 'eventItem')))
        page_source = driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')
        events = soup.find_all('div', class_='eventItem')

        for event in events:
            link = event.find('a', title="More Info")['href']
            if link not in scraped_links:
                scraped_links.add(link)
                event_details = extract_event_details(event)
                if event_details:
                    events_data.extend(event_details)

        try:
            load_more_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, 'loadMoreEvents')))
            driver.execute_script("arguments[0].scrollIntoView(true);", load_more_button)
            driver.execute_script("arguments[0].click();", load_more_button)
            time.sleep(2)
        except Exception:
            #print("No more 'Load More Events' button found.")
            break

finally:
    driver.quit()

# Save to Excel
df = pd.DataFrame(events_data)
output_file = 'Toyota_Center_Events.xlsx'
df.to_excel(output_file, index=False)
print(f"Scraped data saved to {output_file}.")

# Append the scraped events to all_venue_events.xlsx
all_venue_events_file = 'all_venue_events.xlsx'

# Check if the file exists, and if it does, load it
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

print(f"Events have been added to {all_venue_events_file}.")
