import time
from datetime import datetime
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os

# Define the date range for filtering events
start_date_filter = datetime(2025, 4, 14)
end_date_filter = datetime(2025, 7, 31)

# Load the Madison Square Garden URL from the Excel sheet
venue_events = pd.read_excel('venue_events.xlsx')
msg_url = venue_events.loc[venue_events['Venue'].str.contains('Madison Square Garden', case=False, na=False), 'Website']
msg_url_value = msg_url.iloc[0] if not msg_url.empty else None

if not msg_url_value:
    print("Madison Square Garden URL not found in the Excel sheet.")
    exit()

venue = 'Madison Square Garden'
# Set up Chrome options
options = Options()
# Uncomment the next line if debugging dynamically loaded content
# options.add_argument("--headless")
driver = webdriver.Chrome(options=options)

# Function to dismiss popups
def dismiss_obstructions():
    """Dismiss cookie banners or other pop-ups."""
    try:
        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.ID, 'onetrust-banner-sdk'))
        )
        driver.find_element(By.ID, 'onetrust-accept-btn-handler').click()
        print("Dismissed cookie banner.")
    except Exception:
        #print("Cookie banner not found or already dismissed.")
        pass

    try:
        close_button = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(@aria-label, 'Close')]"))
        )
        close_button.click()
        #print("Dismissed popup.")
    except Exception:
        #print("No popup found or already dismissed.")
        pass

# Function to navigate to a specific month
def navigate_to_month(month_name):
    """Navigate to a specific month in the month picker."""
    try:
        # Open the month picker
        picker = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CLASS_NAME, "CalendarEventList_showmonths-picker-wrapper__hVTaE"))
        )
        picker.click()
        #print("Opened month picker.")

        # Select the desired month
        month_element = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, f"//div[@class='ShowMonthsPicker_month__AkiP4']/p[text()='{month_name}']"))
        )
        month_element.click()
        #print(f"Selected {month_name}.")
    except Exception as e:
        #print(f"Error navigating to {month_name}: {e}")
        pass

# Function to extract event details
def extract_event_details(event_card):
    """Extract details from an event card."""
    try:
        # Extract day
        day_element = event_card.find_element(By.CLASS_NAME, "EventCard_day-of-month__tiss0")
        day = day_element.text.strip()

        # Extract month and year
        month_year_element = event_card.find_element(By.CLASS_NAME, "EventCard_month-year__jk8J2")
        month, year = month_year_element.text.split("‘")
        year = f"20{year.strip()}"

        # Extract title
        title_element = event_card.find_element(By.CLASS_NAME, "EventCard_title__4Vkof")
        title = title_element.text.strip()

        # Extract time
        time_element = event_card.find_element(By.CLASS_NAME, "EventCard_showtimes-container__VMcWp")
        time = time_element.text.strip()

        # Extract event link
        link_element = event_card.find_element(By.XPATH, ".//a[contains(@class, 'Button_button__Bw_LG')]")
        event_link = link_element.get_attribute("href")

        # Construct and parse the date
        date_str = f"{day} {month} {year} {time}"
        parsed_datetime = datetime.strptime(date_str, "%d %b %Y %I:%M%p ET")  # Adjust for time zone if necessary

        #return {
            #"Venue": venue,
            #"Title": title,
            #"Date": parsed_datetime.date(),
            #"Time": parsed_datetime.time(),
            #"Link": event_link,
        #}
    except Exception as e:
        print(f"Error extracting event details: {e}")
        return None

# Open the website
driver.get(msg_url_value)
#print(f"Opened {msg_url_value}")
time.sleep(3)

# Dismiss any popups or banners
dismiss_obstructions()

# Months to scrape
months_to_scrape = ["Apr 2025", "May 2025", "Jun 2025", "Jul 2025"]

# List to hold all events
all_events = []

# Venue name
venue_name = "Madison Square Garden"

# Navigate and extract events
for month in months_to_scrape:
    # Navigate to month (update this to match your month picker logic)
    navigate_to_month(month)
    time.sleep(5)  # Wait for events to load

    # Locate all event cards
    event_cards = driver.find_elements(By.CLASS_NAME, "EventCard_card-calendar-mobile__mKfbC")

    #print(f"Found {len(event_cards)} event cards for {month}.")

    for card in event_cards:
        try:
            # Extract date
            day_of_week = card.find_element(By.CLASS_NAME, "EventCard_day-of-week__0fbbn").text.strip()
            day = card.find_element(By.CLASS_NAME, "EventCard_day-of-month__tiss0").text.strip()
            month_year = card.find_element(By.CLASS_NAME, "EventCard_month-year__jk8J2").text.strip()
            event_date_str = f"{day} {month_year.replace('‘', '20')}"  # Convert Apr ‘25 to Apr 2025
            event_date = datetime.strptime(event_date_str, "%d %b %Y")

            # Extract title
            title = card.find_element(By.CLASS_NAME, "EventCard_title-calendar-mobile__ojdRL").text.strip()

            # Extract time
            time_element = card.find_element(By.CLASS_NAME, "EventCard_showtime__fl6Yh").text.strip()
            event_time = datetime.strptime(time_element, "%I:%M%p ET").strftime("%I:%M %p")

            # Extract link
            link = card.find_element(By.CLASS_NAME, "EventCard_calendar-mobile-view__Jcj_q").get_attribute("href")

            # Combine date and time for filtering
            event_datetime = datetime.combine(event_date, datetime.strptime(event_time, "%I:%M %p").time())

            if start_date_filter <= event_datetime <= end_date_filter:
                all_events.append({
                    "Venue": venue_name,
                    "Title": title,
                    "Date": event_date.strftime("%Y-%m-%d"),
                    "Time": event_time,
                    "Link": link,
                })
        except Exception as e:
            print(f"Error extracting event details: {e}")

# Close the driver
driver.quit()
print("Closed the browser.")

# Save results to a DataFrame and output to an Excel file
if all_events:
    events_df = pd.DataFrame(all_events)
    
    # Save to Madison Square Garden specific file
    events_df.to_excel("madison_square_garden_events.xlsx", index=False)
    print("Saved events to 'madison_square_garden_events.xlsx'.")
    
    # Append to all_venue_events.xlsx
    if os.path.exists("all_venue_events.xlsx"):
        # Load the existing master file
        master_df = pd.read_excel("all_venue_events.xlsx")
        # Concatenate the new events to the master DataFrame
        updated_master_df = pd.concat([master_df, events_df], ignore_index=True)
    else:
        # If the master file doesn't exist, use the current events as the master
        updated_master_df = events_df
    
    # Save the updated master DataFrame back to the file
    updated_master_df.to_excel("all_venue_events.xlsx", index=False)
    print("Appended events to 'all_venue_events.xlsx'.")
else:
    print("No events found within the specified date range.")
