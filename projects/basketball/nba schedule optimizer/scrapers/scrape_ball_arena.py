import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time
import re
from datetime import datetime
import os

# Set up Selenium WebDriver (no headless mode)
options = webdriver.ChromeOptions()
driver = webdriver.Chrome(options=options)

def scrape_ball_arena():
    # Read the Excel file
    venue_file = "venue_events.xlsx"
    venues = pd.read_excel(venue_file)
    
    # Filter for Ball Arena
    venue_row = venues[venues['Venue'] == "Ball Arena"]
    if venue_row.empty:
        print("Ball Arena not found in venue_events.xlsx.")
        return
    
    # Extract the URL from the Website column
    url = venue_row.iloc[0]['Website']
    print(f"Scraping events for Ball Arena from {url}")
    
    scrape_venue_events(url)

def scrape_venue_events(url):
    driver.get(url)
    time.sleep(3)
    
    events = []
    seen_events = set()  # To track unique events
    start_date = datetime.strptime("2025-04-14", "%Y-%m-%d")
    end_date = datetime.strptime("2025-07-31", "%Y-%m-%d")
    
    while True:
        # Wait for the calendar month element to be visible
        try:
            current_month_element = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "span.fc-header-title h2"))
            )
            current_month = current_month_element.text.strip()
            print(f"Scraping events for: {current_month}")
        except Exception as e:
            print(f"Error locating the calendar month: {e}")
            break
        
        # Stop if the scraper reaches AUGUST 2025
        if current_month.upper() == "AUGUST 2025":
            print("Reached AUGUST 2025. Stopping scraping.")
            break
        
        # Parse events on the page
        soup = BeautifulSoup(driver.page_source, "html.parser")
        event_elements = soup.select("a.fc-event")
        #print(f"Found {len(event_elements)} events on the current page.")
        
        for event in event_elements:
            try:
                # Extract title
                title_element = event.select_one("span.fc-event-title")
                if not title_element:
                    continue
                title = title_element.text.strip()
                
                # Extract time
                time_element = event.select_one("span.fc-event-time")
                if not time_element:
                    continue
                time_text = time_element.text.strip()
                
                # Normalize time to match datetime format
                if time_text[-1].lower() == 'p':
                    time_text = time_text.replace('p', 'pm')
                elif time_text[-1].lower() == 'a':
                    time_text = time_text.replace('a', 'am')
                
                # Extract link and date from URL
                link = event.get("href", "No Link")
                date_match = re.search(r"(\d{2}-\d{2}-\d{4})", link)
                if not date_match:
                    continue
                event_date_str = date_match.group(0)
                event_date = datetime.strptime(event_date_str, "%m-%d-%Y").strftime("%Y-%m-%d")
                
                # Combine date and normalized time
                try:
                    event_datetime = datetime.strptime(f"{event_date} {time_text}", "%Y-%m-%d %I:%M%p")
                except ValueError:
                    continue
                
                # Filter by date range
                if not (start_date <= event_datetime <= end_date):
                    continue
                
                # Format time
                event_time = event_datetime.strftime("%I:%M%p")
                
                # Check if the event is unique
                event_identifier = (title, event_datetime.strftime("%Y-%m-%d"), event_time)
                if event_identifier in seen_events:
                    continue  # Skip duplicates
                seen_events.add(event_identifier)
                
                # Append valid events
                events.append({
                    "Venue": "Ball Arena",
                    "Title": title,
                    "Date": event_datetime.strftime("%Y-%m-%d"),
                    "Time": event_time,
                    "Link": link
                })
            except Exception as e:
                print(f"Error parsing event: {e}")
                continue
        
        # Try to navigate to the next month
        next_button = driver.find_elements(By.CSS_SELECTOR, "span.fc-button-next")
        if not next_button or "fc-state-disabled" in next_button[0].get_attribute("class"):
            print("No more months to navigate.")
            break
        
        next_button[0].click()
        time.sleep(3)
    
    # Convert the events list to a DataFrame
    events_df = pd.DataFrame(events)
    
    # Save to ball_arena_events.xlsx
    save_to_excel(events_df, "ball_arena_events.xlsx")

def save_to_excel(events_df, output_file):
    # Save to the venue-specific file
    events_df.to_excel(output_file, index=False)
    print(f"Data saved to {output_file}. Total unique events: {len(events_df)}")
    
    # Append to the master file
    master_file = "all_venue_events.xlsx"
    try:
        # Load existing data from the master file
        if os.path.exists(master_file):
            master_df = pd.read_excel(master_file)
        else:
            master_df = pd.DataFrame()
        
        # Combine the existing and new data
        combined_df = pd.concat([master_df, events_df]).drop_duplicates(
            subset=["Venue", "Title", "Date", "Time"], keep="first"
        )
        
        # Save the updated master file
        combined_df.to_excel(master_file, index=False)
        print(f"Data appended to {master_file}. Total unique events in master: {len(combined_df)}")
    except Exception as e:
        print(f"Error updating master file: {e}")


# Execute the scraper for Ball Arena
if __name__ == "__main__":
    try:
        scrape_ball_arena()
    finally:
        driver.quit()
