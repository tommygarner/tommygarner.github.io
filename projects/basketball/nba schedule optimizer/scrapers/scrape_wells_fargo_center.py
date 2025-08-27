import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime
import os

# Define the date range for filtering events
start_date_filter = datetime(2025, 4, 14)
end_date_filter = datetime(2025, 7, 31)

# Load the Wells Fargo Center URL from the Excel sheet
venue_events = pd.read_excel('venue_events.xlsx')
wells_fargo_center_url = venue_events.loc[venue_events['Venue'].str.contains('Wells Fargo Center', case=False, na=False), 'Website']
wells_fargo_center_url_value = wells_fargo_center_url.iloc[0] if not wells_fargo_center_url.empty else None

if not wells_fargo_center_url_value:
    print("Wells Fargo Center URL not found in the Excel sheet.")
    exit()

# Define the venue name
venue_name = "Wells Fargo Center"

# Configure Selenium WebDriver
options = Options()
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--disable-gpu")
options.add_argument("--disable-webgl")
options.add_argument("--disable-software-rasterizer")
options.add_argument("--ignore-certificate-errors")
options.add_argument("--log-level=3")  # Suppress ChromeDriver logs
driver = webdriver.Chrome(options=options)

def switch_to_calendar_view():
    """Locate and click the 'Calendar' button to switch to calendar view."""
    try:
        # Ensure all obstructions (cookie banners, overlays, etc.) are dismissed
        dismiss_obstructions()

        # Locate the 'Calendar' button
        calendar_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "button.toggle.calendar"))
        )

        # Check if already in calendar view
        aria_pressed = calendar_button.get_attribute("aria-pressed")
        if aria_pressed == "false":  # 'false' means not in calendar view yet
            calendar_button.click()
            time.sleep(2)  # Allow the page to load
            print("Switched to calendar view.")
        else:
            print("Already in calendar view.")
    except Exception as e:
        print(f"Error locating or clicking the 'Calendar' button: {e}")


        
def dismiss_obstructions():
    """Dismiss cookie banners or other obstructions on the page."""
    try:
        # Handle cookie banners
        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.ID, "onetrust-banner-sdk"))
        )
        accept_button = driver.find_element(By.ID, "onetrust-accept-btn-handler")
        accept_button.click()
        print("Cookie banner dismissed.")
    except Exception:
        print("No cookie banner found or already dismissed.")

    try:
        # Handle other possible overlays
        overlay = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CLASS_NAME, "onetrust-pc-dark-filter"))
        )
        driver.execute_script("arguments[0].style.display = 'none';", overlay)
        print("Overlay dismissed.")
    except Exception:
        print("No overlay found or already dismissed.")

def get_current_month_year():
    """Extract the current month and year from the calendar header."""
    try:
        header = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".ch_calendar-header .month_name"))
        ).text
        current_month = datetime.strptime(header, "%B %Y")
        return current_month
    except Exception as e:
        print(f"Error extracting current month and year: {e}")
        return None


def navigate_to_next_month():
    """Click the 'Next' button to navigate to the next month."""
    try:
        next_button = driver.find_element(By.CSS_SELECTOR, '.ch_calendar-header .cal-next')
        next_button.click()
        time.sleep(2)  # Allow the page to load
    except Exception as e:
        print(f"Error navigating to the next month: {e}")

def extract_events_from_calendar():
    """Scrape events from the calendar view."""
    events_data = []
    processed_events = set()  # Track processed events to avoid duplicates

    # Get the current month and year
    current_month_year = get_current_month_year()
    if not current_month_year:
        return events_data

    # Loop through months until the end_date_filter is reached
    while current_month_year and current_month_year <= end_date_filter:
        try:
            # Locate all day elements with events
            day_elements = driver.find_elements(By.CSS_SELECTOR, ".ch_calendar-day.hasEvent")

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
                            event_title = item.find_element(By.CSS_SELECTOR, ".desc h3 a").text.strip()
                            event_time = item.find_element(By.CSS_SELECTOR, ".showings.time").text.strip()
                            event_link = item.find_element(By.CSS_SELECTOR, ".desc h3 a").get_attribute("href")

                            # Create a unique event identifier
                            unique_event = (event_title, event_date.strftime("%Y-%m-%d"))

                            if unique_event in processed_events:
                                print(f"Duplicate event detected: {event_title} on {event_date.strftime('%Y-%m-%d')}")
                                continue

                            processed_events.add(unique_event)  # Mark event as processed

                            # Append event details to the list
                            events_data.append({
                                "Venue": venue_name,
                                "Title": event_title,
                                "Date": event_date.strftime("%Y-%m-%d"),
                                "Time": event_time,
                                "Link": event_link,
                            })
                        except Exception as e:
                            print(f"Error processing event item: {e}")
                except Exception as e:
                    print(f"Error processing day element: {e}")
        except Exception as e:
            print(f"Error processing month: {e}")

        # Navigate to the next month
        navigate_to_next_month()
        current_month_year = get_current_month_year()

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

# Start scraping events from Wells Fargo Center calendar
# Start the driver and navigate to the website
driver.get(wells_fargo_center_url_value)

# Dismiss obstructions and switch to calendar view
switch_to_calendar_view()

# Proceed with extracting events
events_data = extract_events_from_calendar()

# Save the scraped events to Wells Fargo Center Excel file
save_events_to_excel(events_data, 'wells_fargo_center_events.xlsx')

# Append the events to all_venue_events.xlsx
append_events_to_all_venue_events(events_data)

# Close the driver
driver.quit()
