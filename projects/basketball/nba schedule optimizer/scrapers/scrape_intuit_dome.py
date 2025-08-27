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

# Load the Intuit Dome URL from the Excel sheet
venue_events = pd.read_excel('venue_events.xlsx')
intuit_dome_url = venue_events.loc[venue_events['Venue'].str.contains('Intuit Dome', case=False, na=False), 'Website']
intuit_dome_url_value = intuit_dome_url.iloc[0] if not intuit_dome_url.empty else None

if not intuit_dome_url_value:
    print("Intuit Dome URL not found in the Excel sheet.")
    exit()

# Define the venue name
venue_name = "Intuit Dome"

# Configure Selenium WebDriver
options = Options()
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
driver = webdriver.Chrome(options=options)

driver.get(intuit_dome_url_value)
time.sleep(5)  # Allow the page to load

# Initialize an empty list to store event data
events_data = []

# Find event sections
try:
    event_sections = driver.find_elements(By.CLASS_NAME, "EventCollection_eventCard__SXqEa")
    
    for event_card in event_sections:
        try:
            # Extract event title
            event_title = event_card.find_element(By.CLASS_NAME, "_title_57ljr_325").text
            
            # Extract date and time
            date_time_text = event_card.find_element(By.CLASS_NAME, "_date_koyy9_13").text
            date_time_parts = date_time_text.split(" / ")
            date_text = date_time_parts[0].split(", ")[1].strip()
            time_text = date_time_parts[1].strip()
            
            # Convert date to YYYY-MM-DD format
            event_date_obj = datetime.strptime(date_text, "%b %d").replace(year=datetime.now().year)
            event_date = event_date_obj.strftime("%Y-%m-%d")
            
            # Filter events based on date range
            if start_date_filter <= event_date_obj <= end_date_filter:
                # Extract ticket link
                ticket_link = event_card.find_element(By.TAG_NAME, "a").get_attribute("href")
                
                # Append event data to the list
                events_data.append({
                    "Venue": venue_name,
                    "Title": event_title,
                    "Date": event_date,
                    "Time": time_text,
                    "Link": ticket_link
                })
        except Exception as e:
            print(f"Error parsing event card: {e}")
except Exception as e:
    print(f"Error finding event sections: {e}")

# Close the browser
driver.quit()

# Save the data to `intuit_dome_events.xlsx`
if events_data:
    df = pd.DataFrame(events_data)
    intuit_output_file = "intuit_dome_events.xlsx"
    df.to_excel(intuit_output_file, index=False)
    print(f"Scraping complete. Data saved to {intuit_output_file}.")
    
    # Append to `all_venue_events.xlsx`
    all_venue_file = "all_venue_events.xlsx"
    if os.path.exists(all_venue_file):
        existing_data = pd.read_excel(all_venue_file)
        combined_data = pd.concat([existing_data, df], ignore_index=True)
    else:
        combined_data = df
    
    # Save updated data back to `all_venue_events.xlsx`
    combined_data.to_excel(all_venue_file, index=False)
    print(f"Events appended to {all_venue_file}.")
else:
    print("No events found within the specified date range.")
