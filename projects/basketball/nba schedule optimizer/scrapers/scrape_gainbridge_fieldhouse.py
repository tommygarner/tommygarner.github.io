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

# Load the Gainbridge Fieldhouse URL from the Excel sheet
venue_events = pd.read_excel('venue_events.xlsx')
gainbridge_fieldhouse_url = venue_events.loc[venue_events['Venue'].str.contains('Gainbridge Fieldhouse', case=False, na=False), 'Website']
gainbridge_fieldhouse_url_value = gainbridge_fieldhouse_url.iloc[0] if not gainbridge_fieldhouse_url.empty else None

if not gainbridge_fieldhouse_url_value:
    print("Gainbridge Fieldhouse URL not found in the Excel sheet.")
    exit()

# Set up Chrome options without headless mode
options = Options()
driver = webdriver.Chrome(options=options)

def get_current_month_year():
    """Extract the current month and year from the header of the calendar."""
    header = driver.find_element(By.CLASS_NAME, 'month_name').text
    month, year = header.split()
    current_month = datetime.strptime(f"{month} {year}", "%B %Y")
    print(f"Current month: {current_month.strftime('%B %Y')}")
    return current_month

def navigate_to_next_month():
    """Click the 'Next' button to navigate to the next month."""
    next_button = driver.find_element(By.CLASS_NAME, 'cal-next')
    next_button.click()
    time.sleep(2)

def extract_event_details(date_element):
    """Extract event details (Title, Date, Time, Link) from an event element."""
    venue = "Gainbridge Fieldhouse"
    try:
        # Extract the event title
        title_element = date_element.find_element(By.CSS_SELECTOR, '.desc h3 a')
        title = title_element.text.strip()

        # Extract the event date (from the aria-label attribute)
        date_str = date_element.get_attribute('aria-label')
        event_date = datetime.strptime(date_str, "%B %d %Y")

        # Ensure the event is within the specified date range
        if not (start_date_filter <= event_date <= end_date_filter):
            return None

        # Extract the event times (showings)
        time_element = date_element.find_element(By.CSS_SELECTOR, '.showings.time')
        times_str = time_element.text.strip() if time_element else "TBA"
        
        # Split multiple times by commas and create multiple rows for the event
        times = [time.strip() for time in times_str.split(',')] if times_str != "TBA" else ["TBA"]

        # Extract the event link
        link = title_element.get_attribute('href')

        # Create a list of events for each time slot
        event_details = []
        for time in times:
            event_details.append({
                'Venue': venue,
                'Title': title,
                'Date': event_date.strftime('%Y-%m-%d'),
                'Time': time,
                'Link': link
            })

        return event_details
    except Exception as e:
        #print(f"Error extracting event details: {e}")
        return None

def extract_events_from_calendar():
    events_data = []

    # Get the current month and year
    current_month = get_current_month_year()

    # Loop through months until the end_date_filter is reached
    while current_month <= end_date_filter:
        print(f"Scraping events for {current_month.strftime('%B %Y')}...")

        # Extract event elements for this month
        date_elements = driver.find_elements(By.CLASS_NAME, 'tl-date')  # Adjust the class for event date elements
        for date_element in date_elements:
            event_details = extract_event_details(date_element)
            if event_details:
                events_data.extend(event_details)  # Add multiple rows if there are multiple times

        # Navigate to next month
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

# Start scraping events from Gainbridge Fieldhouse calendar
driver.get(gainbridge_fieldhouse_url_value)

events_data = extract_events_from_calendar()

# Save the scraped events to Gainbridge Fieldhouse Excel file
save_events_to_excel(events_data, 'gainbridge_fieldhouse_events.xlsx')

# Append the events to all_venue_events.xlsx
append_events_to_all_venue_events(events_data)

# Close the driver
driver.quit()
