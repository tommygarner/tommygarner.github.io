import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime, timedelta
import time
from bs4 import BeautifulSoup
from webdriver_manager.chrome import ChromeDriverManager  # Import webdriver-manager
import openpyxl  # Import openpyxl to handle existing Excel files
from concurrent.futures import ThreadPoolExecutor  # Import ThreadPoolExecutor for concurrent execution
import os
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"  # Suppress TensorFlow warnings

def get_united_center_link():
    """Retrieve the United Center link from the venue_events.xlsx file."""
    try:
        df = pd.read_excel("venue_events.xlsx")  # Load the existing file
        united_center_link = df.loc[df['Venue'] == 'United Center', 'Website'].values[0]  # Assuming the link is in the 'Website' column
        return united_center_link
    except FileNotFoundError:
        return None
    except IndexError:
        return None

def scrape_event_details(event_link):
    """Scrape the date, time, and title from the event detail page."""
    options = webdriver.ChromeOptions()
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--allow-insecure-localhost')
    options.add_argument('--disable-web-security')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-logging')
    options.add_argument('--log-level=3')
    options.add_argument('--remote-debugging-port=0')

    caps = DesiredCapabilities.CHROME.copy()
    caps['goog:loggingPrefs'] = {'browser': 'OFF', 'performance': 'OFF'}

    options.set_capability('goog:loggingPrefs', {'browser': 'OFF', 'performance': 'OFF'})

    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.get(event_link)

    # Wait for the event details to load
    try:
        # Wait for the page to load
        WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.eventHeroDetails")))
    except Exception as e:
        print(f"Error loading event details: {e}")
        driver.quit()
        return []

    # Parse the page source with BeautifulSoup
    html_content = driver.page_source
    soup = BeautifulSoup(html_content, 'html.parser')

    # Extract individual events from the page
    event_details = []
    event_sections = soup.find_all('div', class_='eventHeroDetails')  # Adjust class if needed

    for event_section in event_sections:
        # Extract event title
        title_div = event_section.find('h1', class_='hdng')
        title = title_div.find('strong').text.strip() if title_div else "Title not found"

        # Extract ticket link
        ticket_link_element = event_section.find('a', id="CT_PageTop_1_hypDetailTicket")
        ticket_link = ticket_link_element['href'] if ticket_link_element else "No ticket link available"

        # Extract dates and times
        date_time_div = event_section.find('div', class_='eventDateTime')
        if date_time_div:
            # Extract start date and time
            start_date_span = date_time_div.find('span', class_='dateFont')
            start_date_str = start_date_span.find('strong').text.strip() if start_date_span else "Date not found"
            start_time = (
                start_date_span.find_all('br')[1].previous_sibling.strip()
                if start_date_span and len(start_date_span.find_all('br')) > 1
                else "Time not available"
            )

            # Parse start date
            start_date = datetime.strptime(start_date_str, '%B %d, %Y')

            # Check for multi-day events (end date)
            end_date_div = date_time_div.find('div', id="CT_PageTop_1_divEndDate")
            if end_date_div:
                end_date_span = end_date_div.find('span', class_='dateFont')
                end_date_str = end_date_span.find('strong').text.strip() if end_date_span else None
                end_date = datetime.strptime(end_date_str, '%B %d, %Y') if end_date_str else start_date
            else:
                end_date = start_date

            # Generate all dates for the event
            current_date = start_date
            while current_date <= end_date:
                event_details.append({
                    "date": current_date.strftime('%B %d, %Y'),
                    "time": start_time,
                    "title": title,
                    "ticket_link": ticket_link
                })
                current_date += timedelta(days=1)

    driver.quit()
    return event_details

def scrape_united_center_events():
    # Get the United Center link
    united_center_url = get_united_center_link()
    if not united_center_url:
        return []

    # Define the base URL for constructing full event links
    base_url = "https://www.unitedcenter.com"

    # Initialize the WebDriver using webdriver-manager
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service)
    driver.get(united_center_url)

    # Initialize variables
    events = []
    seen_events = set()  # Track unique events

    # Define the date range for filtering
    start_date = datetime.strptime("2025-04-14", '%Y-%m-%d')
    end_date = datetime.strptime("2025-07-31", '%Y-%m-%d')

    while True:
        try:
            # Wait for the month/year header to load
            WebDriverWait(driver, 20).until(EC.visibility_of_element_located((By.CSS_SELECTOR, "h1.title")))
            month_year_element = driver.find_element(By.CSS_SELECTOR, "h1.title")
            month_year = month_year_element.text.strip().upper()

            # Stop scraping if we reach August 2025
            if month_year == "AUGUST 2025":
                break

            # Scrape events for April through July
            if month_year in ["APRIL 2025", "MAY 2025", "JUNE 2025", "JULY 2025"]:
                html_content = driver.page_source
                soup = BeautifulSoup(html_content, 'html.parser')

                # Extract event links
                event_items = soup.find_all('a', class_='eventLink')
                event_links = []
                for event_item in event_items:
                    event_link = event_item['href']
                    full_event_link = base_url + event_link
                    event_links.append(full_event_link)

                # Open event links with ThreadPoolExecutor
                with ThreadPoolExecutor(max_workers=5) as executor:
                    event_details = list(executor.map(scrape_event_details, event_links))

                # Process scraped details
                for link, event_dates in zip(event_links, event_details):
                    for event in event_dates:
                        event_day = event["date"]
                        event_time = event["time"]
                        event_title = event["title"]
                        event_date = datetime.strptime(event_day, '%B %d, %Y')

                        if start_date <= event_date <= end_date:
                            # Create a unique identifier
                            event_key = (event_title, event_day, event_time)
                            if event_key not in seen_events:
                                seen_events.add(event_key)
                                events.append({
                                    'Venue': 'United Center',
                                    'Title': event_title,
                                    'Date': event_day,
                                    'Time': event_time,
                                    'Link': link
                                })

            # Navigate to the next month
            next_button = driver.find_element(By.XPATH, "//img[@alt='Next']")
            next_button.click()
            time.sleep(2)

        except Exception as e:
            print(f"Error during scraping: {e}")
            break

    driver.quit()
    return events


# Example usage
united_center_events = scrape_united_center_events()
if not united_center_events:
    print("No events were scraped.")
else:
    # Format the Date column to YYYY-MM-DD
    for event in united_center_events:
        event['Date'] = datetime.strptime(event['Date'], '%B %d, %Y').strftime('%Y-%m-%d')

    # Save the events to a new Excel file
    df_new = pd.DataFrame(united_center_events)
    df_new.to_excel("united_center_events.xlsx", index=False)  # Save to a new Excel file
    print(f"Events saved to united_center_events.xlsx.")

    target_file = "all_venue_events.xlsx"
    if os.path.exists(target_file):
        # Load the existing data
        df_existing = pd.read_excel(target_file)
        
        # Append new events to existing data
        df_combined = pd.concat([df_existing, df_new], ignore_index=True)
        
        # Remove duplicates if necessary
        df_combined = df_combined.drop_duplicates(subset=['Title', 'Date', 'Time'], keep='first')
        
        # Save the updated data back to the target file
        df_combined.to_excel(target_file, index=False)
        print(f"United Center events added to {target_file}.")
    else:
        # If the target file doesn't exist, create it with the new events
        df_new.to_excel(target_file, index=False)
        print(f"{target_file} not found. A new file was created with United Center events.")