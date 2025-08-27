import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
import os

# Define the date range for filtering events
start_date_filter = datetime(2025, 4, 14)
end_date_filter = datetime(2025, 7, 31)

# Load the Golden 1 Center URL from the Excel sheet
venue_events = pd.read_excel('venue_events.xlsx')
golden_1_center_url = venue_events.loc[venue_events['Venue'].str.contains('Golden 1 Center', case=False, na=False), 'Website']
golden_1_center_url_value = golden_1_center_url.iloc[0] if not golden_1_center_url.empty else None

if not golden_1_center_url_value:
    print("Golden 1 Center URL not found in the Excel sheet.")
    exit()

# Define the venue name
venue_name = "Golden 1 Center"

# Configure Selenium WebDriver
options = Options()
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
driver = webdriver.Chrome(options=options)

def accept_cookies():
    """Click the 'Accept All' button to handle the cookie consent popup."""
    try:
        wait = WebDriverWait(driver, 10)
        cookie_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button.cky-btn-accept")))
        ActionChains(driver).move_to_element(cookie_button).perform()
        cookie_button.click()
        time.sleep(1)
        print("Accepted cookies.")
    except Exception as e:
        print(f"No cookie popup found or error accepting cookies - {e}")

def get_current_month_year():
    """Extract the current month and year from the calendar header."""
    try:
        header = driver.find_element(By.CSS_SELECTOR, ".fc-toolbar .fc-center h2").text
        return datetime.strptime(header, "%B %Y")
    except Exception as e:
        print(f"Error extracting current month - {e}")
        return None

def navigate_to_next_month():
    """Click the 'Next' button to navigate to the next month."""
    try:
        next_button = driver.find_element(By.CSS_SELECTOR, ".fc-toolbar .fc-next-button")
        next_button.click()
        time.sleep(2)  # Allow the page to load
    except Exception as e:
        print(f"Error navigating to the next month - {e}")

def extract_event_details_from_page(event_url):
    """Extract event details from the event page."""
    try:
        new_driver = webdriver.Chrome(options=options)
        new_driver.get(event_url)
        time.sleep(2)  # Allow the page to load

        # Extract the event date and other details
        date_element = new_driver.find_element(By.CSS_SELECTOR, ".gt-start-date .gt-inner")
        event_date_str = date_element.text.strip()
        event_date = datetime.strptime(event_date_str, "%B %d, %Y %I:%M %p")

        if not (start_date_filter <= event_date <= end_date_filter):
            new_driver.quit()
            return None

        # Extract the event title
        event_title_element = new_driver.find_element(By.CSS_SELECTOR, "div.container h1")
        event_title = event_title_element.text.strip()

        event_details = {
            "Venue": venue_name,
            "Title": event_title,
            "Date": event_date.strftime("%Y-%m-%d"),
            "Time": event_date.strftime("%I:%M %p"),
            "Link": event_url,
        }
        new_driver.quit()
        return event_details
    except Exception as e:
        print(f"Error extracting event details - {e}")
        return None


def process_event_batch(event_urls):
    """Process a batch of event URLs."""
    events_data = []
    with ThreadPoolExecutor(max_workers=5) as executor:
        results = executor.map(extract_event_details_from_page, event_urls)
        for result in results:
            if result:
                events_data.append(result)
    return events_data

def remove_duplicates(events_data):
    """Remove duplicate events based on title and date."""
    unique_events = []
    seen = set()
    for event in events_data:
        identifier = (event["Title"], event["Date"])
        if identifier not in seen:
            seen.add(identifier)
            unique_events.append(event)
    return unique_events


def scrape_events_until_august_2025():
    """Scrape all events until August 2025."""
    events_data = []

    current_month = get_current_month_year()
    while current_month and current_month <= datetime(2025, 7, 31):
        try:
            # Start processing only from April 2025
            if current_month >= datetime(2025, 4, 1):
                # Extract event links for the current month
                event_links = driver.find_elements(By.CSS_SELECTOR, "a.fc-day-grid-event")
                event_urls = [link.get_attribute("href") for link in event_links]

                # Process event links in batches of 5
                for i in range(0, len(event_urls), 5):
                    batch = event_urls[i:i+5]
                    batch_results = process_event_batch(batch)
                    events_data.extend(batch_results)

            navigate_to_next_month()
            current_month = get_current_month_year()
        except Exception as e:
            print(f"Error scraping month - {e}")

    # Remove duplicates before returning
    return remove_duplicates(events_data)

def save_events_to_excel(events_data, file_name):
    """Save events to the specified Excel file."""
    events_df = pd.DataFrame(events_data)
    events_df.to_excel(file_name, index=False)
    print(f"Events have been saved to {file_name}.")

def append_events_to_all_venue_events(events_data):
    """Append the events to the 'all_venue_events.xlsx' file."""
    all_venue_events_file = 'all_venue_events.xlsx'

    # Check if the file exists and load existing data
    if os.path.exists(all_venue_events_file):
        all_venue_events = pd.read_excel(all_venue_events_file)
    else:
        all_venue_events = pd.DataFrame()  # Create an empty DataFrame if the file doesn't exist

    # Convert events_data to a DataFrame before appending
    new_events_df = pd.DataFrame(events_data)

    # Append the new data to the existing DataFrame
    all_venue_events = pd.concat([all_venue_events, new_events_df], ignore_index=True)

    # Remove duplicates in the final DataFrame
    all_venue_events.drop_duplicates(subset=["Title", "Date"], inplace=True)

    # Save the updated DataFrame back to the Excel file
    all_venue_events.to_excel(all_venue_events_file, index=False)
    print(f"Events have been appended to {all_venue_events_file}.")

# Start scraping events from Golden 1 Center calendar
driver.get(golden_1_center_url_value)

# Accept cookies if the popup appears
accept_cookies()

# Scrape events starting in April 2025 until August 2025
events_data = scrape_events_until_august_2025()

# Save the scraped events to a local Excel file
save_events_to_excel(events_data, "golden_1_center_events.xlsx")

# Append the events to all_venue_events.xlsx
append_events_to_all_venue_events(events_data)

# Close the driver
driver.quit()
