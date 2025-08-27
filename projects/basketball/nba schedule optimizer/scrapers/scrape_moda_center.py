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

# Load the Moda Center URL from the Excel sheet
venue_events = pd.read_excel('venue_events.xlsx')
moda_center_url = venue_events.loc[venue_events['Venue'].str.contains('Moda Center', case=False, na=False), 'Website']
moda_center_url_value = moda_center_url.iloc[0] if not moda_center_url.empty else None

if not moda_center_url_value:
    print("Moda Center URL not found in the Excel sheet.")
    exit()

# Define the venue name
venue_name = "Moda Center"

# Configure Selenium WebDriver
options = Options()
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
driver = webdriver.Chrome(options=options)

def standardize_date(month, day, year="2025"):
    """Convert month, day, and year into YYYY-MM-DD format."""
    try:
        full_date = f"{month} {day}, {year}"
        return datetime.strptime(full_date, "%b %d, %Y").strftime("%Y-%m-%d")
    except Exception as e:
        print(f"Error standardizing date: {full_date}. Error: {e}")
        return None

def scrape_events():
    """Scrape events from the Moda Center website."""
    events_data = []

    # Load the Moda Center page
    driver.get(moda_center_url_value)

    # Select the Moda Center from the dropdown
    dropdown_menu = driver.find_element(By.CSS_SELECTOR, ".dd-venue-toggle")
    dropdown_menu.click()
    moda_option = driver.find_element(By.LINK_TEXT, "Moda Center")
    moda_option.click()
    time.sleep(2)  # Wait for events to load

    # Find all event cards
    event_cards = driver.find_elements(By.CSS_SELECTOR, ".event-card")
    print(f"Found {len(event_cards)} event cards.")

    for card in event_cards:
        try:
            # Extract the date
            date_month = card.find_element(By.CSS_SELECTOR, ".date-box .box-month").text.strip()
            date_day = card.find_element(By.CSS_SELECTOR, ".date-box .box-day").text.strip()
            event_date = standardize_date(date_month, date_day)

            # Skip events outside the filter range
            if not event_date or not (start_date_filter <= datetime.strptime(event_date, "%Y-%m-%d") <= end_date_filter):
                continue

            # Extract the event title
            title = card.find_element(By.CSS_SELECTOR, ".card-who").text.strip()

            # Extract the event time
            time_element = card.find_element(By.CSS_SELECTOR, ".card-date-block .card-date-time")
            event_time = time_element.text.strip() if time_element else "TBD"

            # Extract the event link
            event_link = card.find_element(By.CSS_SELECTOR, "a.card-info").get_attribute("href")

            # Append the event data
            events_data.append({
                "Venue": venue_name,
                "Title": title,
                "Date": event_date,
                "Time": event_time,
                "Link": event_link,
            })
        except Exception as e:
            print(f"Error processing event card: {e}")

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

# Main script execution
if __name__ == "__main__":
    try:
        events_data = scrape_events()

        # Save the scraped events to a file
        save_events_to_excel(events_data, "moda_center_events.xlsx")

        # Append the events to the consolidated file
        append_events_to_all_venue_events(events_data)
    finally:
        driver.quit()
