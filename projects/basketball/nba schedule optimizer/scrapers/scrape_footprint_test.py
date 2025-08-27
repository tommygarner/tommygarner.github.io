import os
import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from datetime import datetime, timedelta

# Load the Footprint Center URL from the Excel sheet
venue_events = pd.read_excel('venue_events.xlsx')
footprint_center_url = venue_events.loc[venue_events['Venue'].str.contains('Footprint Center', case=False, na=False), 'Website']
footprint_center_url_value = footprint_center_url.iloc[0] if not footprint_center_url.empty else None

if not footprint_center_url_value:
    print("Footprint Center URL not found in the Excel sheet.")
    exit()

venue = "Footprint Center"

# Configure Selenium WebDriver
options = Options()
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--disable-gpu")
options.add_argument("--ignore-certificate-errors")
options.add_argument("--log-level=3")  # Suppress ChromeDriver logs

def standardize_date(date_str):
    """Convert date string to YYYY-MM-DD format or handle date ranges."""
    try:
        # Remove the day of the week if present (e.g., "Sat, June 22, 2025" -> "June 22, 2025")
        if "," in date_str and date_str.split(",")[0].strip().isalpha():
            date_str = " ".join(date_str.split(",")[1:]).strip()
        
        # Check for date range (e.g., "June 22-23, 2025")
        if "-" in date_str:
            parts = date_str.split(",")
            year = parts[1].strip()
            month_day_range = parts[0].split("-")
            
            # Extract start and end days
            start_day = month_day_range[0].strip().split()[-1]  # Extract day from the first part
            end_day = month_day_range[1].strip()  # Extract day from the second part

            # Extract month from the first part
            month = month_day_range[0].strip().split()[0]

            # Combine month, day, and year for both start and end
            start_date = datetime.strptime(f"{month} {start_day}, {year}", "%B %d, %Y").strftime("%Y-%m-%d")
            end_date = datetime.strptime(f"{month} {end_day}, {year}", "%B %d, %Y").strftime("%Y-%m-%d")

            return f"{start_date} - {end_date}"

        # Single date (e.g., "June 22, 2025")
        elif "," in date_str:
            return datetime.strptime(date_str, "%B %d, %Y").strftime("%Y-%m-%d")

        # If date_str is not in an expected format, return None
        return None
    except Exception as e:
        print(f"Error standardizing date: {date_str}. Error: {e}")
        return None


def extract_event_details(driver):
    events_data = []
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.css-rep5dz"))
        )
        event_containers = driver.find_elements(By.CSS_SELECTOR, "div.css-rep5dz")

        print(f"Found {len(event_containers)} event containers.")

        for i, event in enumerate(event_containers):
            try:
                ActionChains(driver).move_to_element(event).perform()
                title = event.find_element(By.CSS_SELECTOR, "h6.MuiTypography-root").text.strip()
                date_time_text = event.find_element(By.CSS_SELECTOR, "span.MuiTypography-root.MuiTypography-caption.css-up1egf").text.strip()

                if "|" in date_time_text:
                    date_part, time_part = map(str.strip, date_time_text.split("|"))
                else:
                    date_part, time_part = date_time_text.strip(), None

                date_part = standardize_date(date_part)

                link_element = event.find_element(By.CSS_SELECTOR, "a.MuiCardActionArea-root")
                event_link = link_element.get_attribute("href")
                if event_link.startswith("/"):
                    event_link = f"https://www.footprintcenter.com{event_link}"

                events_data.append({
                    "Venue": venue,
                    "Title": title,
                    "Date": date_part,
                    "Time": time_part,
                    "Link": event_link
                })
            except Exception as e:
                print(f"Error processing event {i+1}: {e}")

    except Exception as e:
        print(f"Error extracting events: {e}")

    return events_data

def navigate_to_next_page(driver):
    try:
        next_button = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "button[aria-label='Go to next page']"))
        )
        # Check if the button is not disabled
        if "Mui-disabled" not in next_button.get_attribute("class"):
            next_button.click()
            print("Navigated to the next page.")
            time.sleep(2)  # Allow time for the next page to load
            return True
        else:
            print("Next page button is disabled. No more pages.")
            return False
    except Exception as e:
        print(f"Error navigating to the next page: {e}")
        return False

def scrape_all_pages(driver):
    all_events = []  # Store all events from all pages
    page_number = 1

    while True:
        print(f"Scraping page {page_number}...")
        # Extract events on the current page
        current_page_events = extract_event_details(driver)
        all_events.extend(current_page_events)

        # Navigate to the next page
        if not navigate_to_next_page(driver):
            break  # Exit the loop if the next page is not available
        page_number += 1

    return all_events

def filter_events(events, start_date, end_date):
    """Filter events to include only those between start_date and end_date."""
    filtered_events = []
    start_date_obj = datetime.strptime(start_date, "%Y-%m-%d")
    end_date_obj = datetime.strptime(end_date, "%Y-%m-%d")

    for event in events:
        event_date = event.get("Date")
        if event_date:
            # Handle date ranges
            if " - " in event_date:
                start, end = event_date.split(" - ")
                start_obj = datetime.strptime(start, "%Y-%m-%d")
                end_obj = datetime.strptime(end, "%Y-%m-%d")

                # Include if any part of the range overlaps the filter range
                if start_obj <= end_date_obj and end_obj >= start_date_obj:
                    filtered_events.append(event)
            else:
                # Single date
                event_date_obj = datetime.strptime(event_date, "%Y-%m-%d")
                if start_date_obj <= event_date_obj <= end_date_obj:
                    filtered_events.append(event)

    return filtered_events


def process_date_range_events(driver, events):
    updated_events = []
    for event in events:
        date = event["Date"]
        if " - " in date:  # Check for a date range
            print(f"Processing date range: {date}")
            event_link = event["Link"]
            
            # Split the range into start and end dates
            start_date_str, end_date_str = date.split(" - ")
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d")
            
            if event_link:
                # Open the event link in a new window
                driver.execute_script(f"window.open('{event_link}', '_blank');")
                driver.switch_to.window(driver.window_handles[-1])
                
                try:
                    # Wait for the page to load
                    WebDriverWait(driver, 10).until(
                        EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.MuiPaper-root"))
                    )
                    
                    # Find all specific times in the event page
                    specific_time_elements = driver.find_elements(By.CSS_SELECTOR, "p.MuiTypography-root.MuiTypography-h6.css-1lvr273")
                    specific_times = [el.text.split("|")[1].strip() for el in specific_time_elements]
                    
                    # Map each date in the range to the corresponding time
                    current_date = start_date
                    time_index = 0
                    while current_date <= end_date:
                        if time_index < len(specific_times):
                            specific_time = specific_times[time_index]
                            updated_events.append({
                                "Venue": event["Venue"],
                                "Title": event["Title"],
                                "Date": current_date.strftime("%Y-%m-%d"),
                                "Time": specific_time,
                                "Link": event["Link"]
                            })
                            time_index += 1
                        current_date += timedelta(days=1)
                except Exception as e:
                    print(f"Error loading event link {event_link}: {e}")
                finally:
                    # Close the new window and switch back to the main page
                    driver.close()
                    driver.switch_to.window(driver.window_handles[0])
            else:
                print(f"No link available for event with range: {event}")
        else:
            # If not a date range, simply append the event
            updated_events.append(event)
    return updated_events

def append_to_excel(filename, data):
    """Append the processed events to an existing Excel file."""
    try:
        # Check if the file exists
        if os.path.exists(filename):
            # Load existing data
            existing_data = pd.read_excel(filename)
            # Append new data
            updated_data = pd.concat([existing_data, pd.DataFrame(data)], ignore_index=True)
        else:
            # If the file doesn't exist, create it with the new data
            updated_data = pd.DataFrame(data)

        # Save to the Excel file
        updated_data.to_excel(filename, index=False)
        print(f"Appended events to {filename} successfully!")
    except Exception as e:
        print(f"Error appending to Excel: {e}")

# Main flow integration
if __name__ == "__main__":
    driver = webdriver.Chrome(options=options)
    driver.get(footprint_center_url_value)

    try:
        # Scrape all pages
        events = scrape_all_pages(driver)

        # Filter for the desired date range
        filtered_events = filter_events(events, "2025-04-14", "2025-07-31")

        # Process date range events
        final_events = process_date_range_events(driver, filtered_events)

        # Save detailed events to a local file
        pd.DataFrame(final_events).to_excel("footprint_center_events.xlsx", index=False)

        # Append these events to the master file
        append_to_excel("all_venue_events.xlsx", final_events)

        print("Scraping, processing, and appending complete!")
    finally:
        driver.quit()
