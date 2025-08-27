import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime
import time
from bs4 import BeautifulSoup
from webdriver_manager.chrome import ChromeDriverManager  # Import webdriver-manager
import openpyxl  # Import openpyxl to handle existing Excel files

def format_title(title):
    """Format the title to have capitalized first letters for each word."""
    return ' '.join(word.capitalize() for word in title.split())

def format_date(date_str):
    """Convert date from 'MMM DD, YYYY' to 'YYYY-MM-DD'."""
    return datetime.strptime(date_str, '%b %d, %Y').strftime('%Y-%m-%d')

def format_time(time_str):
    """Format time to 'HH:MM am/pm'."""
    time_str = time_str.strip()
    if time_str.startswith('-'):
        time_str = time_str[1:].strip()  # Remove leading dash
    return datetime.strptime(time_str, '%I:%M %p').strftime('%I:%M %p')

def scrape_spectrum_events():
    # Initialize the WebDriver using webdriver-manager
    service = Service(ChromeDriverManager().install())  # Automatically installs the chromedriver
    driver = webdriver.Chrome(service=service)
    driver.get("https://www.spectrumcentercharlotte.com/events")  # Update with the actual URL

    # Initialize variables
    events = []

    # Define the date range for filtering
    start_date = datetime.strptime("2025-04-14", '%Y-%m-%d')
    end_date = datetime.strptime("2025-07-31", '%Y-%m-%d')

    while True:
        try:
            # Wait for the calendar header to load and get the month/year from the last box
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "h2.m-venueframework__header-text")))
            month_year_elements = driver.find_elements(By.CSS_SELECTOR, "h2.m-venueframework__header-text")
            month_year = month_year_elements[-1].text.strip()  # Get the text from the last header element
            print(f"Scraping events for: {month_year}")

            # Check if the month_year is July 2025, and break if so
            if month_year == "July 2025":
                print("Reached the end of the scraping period (July 2025). Stopping.")
                break

            # Wait for the event items to load
            time.sleep(2)  # Allow time for events to load

            # Get the page source and parse it with BeautifulSoup
            html_content = driver.page_source
            soup = BeautifulSoup(html_content, 'html.parser')

            # Extract event information
            event_items = soup.find_all('div', class_='event_item_wrapper')
            if not event_items:
                print(f"No event items found for {month_year}.")  # More specific message
            
            for event_item in event_items:
                date_str = event_item.find('span', class_='dt').text.strip()
                event_time = event_item.find('span', class_='time').text.strip()  # Renamed variable
                title = event_item.find('h3').text.strip()
                link = event_item.find('a', title="More Info")['href']
                
                # Format the date and check if it falls within the specified range
                event_date = datetime.strptime(date_str, '%b %d, %Y')
                if start_date <= event_date <= end_date:
                    events.append({
                        'Venue': 'Spectrum Center',  # Add venue
                        'Title': format_title(title),  # Format title
                        'Date': format_date(date_str),  # Format date
                        'Time': format_time(event_time),  # Format time
                        'Link': link  # Use the extracted link
                    })

            # Wait for the next button to be clickable
            next_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, "cal-next")))
            driver.execute_script("arguments[0].scrollIntoView(true);", next_button)  # Scroll into view
            time.sleep(0.5)  # Short wait to ensure visibility
            driver.execute_script("arguments[0].click();", next_button)  # Use JavaScript to click
            time.sleep(3)  # Increased wait time for the next month to load

        except Exception as e:
            print(f"Error navigating to the next month: {e}")
            break

    driver.quit()
    return events

# Example usage
spectrum_events = scrape_spectrum_events()
if not spectrum_events:
    print("No events to add to all_venue_events.xlsx.")
else:
    # Load the existing workbook
    try:
        workbook = openpyxl.load_workbook("all_venue_events.xlsx")  # Load the existing file
        df_existing = pd.read_excel("all_venue_events.xlsx")  # Read existing data into a DataFrame
    except FileNotFoundError:
        # If the file does not exist, create a new DataFrame
        df_existing = pd.DataFrame()

    # Create a DataFrame from the new events list
    df_new = pd.DataFrame(spectrum_events)

    # Concatenate the existing DataFrame with the new events
    df_combined = pd.concat([df_existing, df_new], ignore_index=True)

    # Save the combined DataFrame back to the existing Excel file
    df_combined.to_excel("all_venue_events.xlsx", index=False)  # Save to the same file without the index
    print(f"Events appended to all_venue_events.xlsx.")