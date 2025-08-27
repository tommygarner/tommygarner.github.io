from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import pandas as pd
import time
from datetime import datetime
import os

# Load the Chase Center URL from the Excel sheet
venue_events = pd.read_excel('venue_events.xlsx')
chase_center_url = venue_events.loc[venue_events['Venue'].str.contains('Chase Center', case=False, na=False), 'Website']
chase_center_url_value = chase_center_url.iloc[0] if not chase_center_url.empty else None

if not chase_center_url_value:
    print("Chase Center URL not found in the Excel sheet.")
    exit()

# Define the date range for filtering
start_date = datetime.strptime("2025-04-14", "%Y-%m-%d")
end_date = datetime.strptime("2025-07-31", "%Y-%m-%d")

# Define function to extract event details
def extract_event_details(driver):
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    month_year = soup.select_one(".react-calendar__navigation__label__labelText--from p").text
    print(f"Scraping events for: {month_year}")
    days = driver.find_elements(By.CSS_SELECTOR, ".react-calendar__month-view__days button")
    events = []
    
    for day in days:
        try:
            abbr = day.find_element(By.TAG_NAME, "abbr")
            event_date = abbr.get_attribute("aria-label")
            if month_year.split()[0] not in event_date:
                continue
            day.click()
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.ml-auto.h-full.w-full.lg\\:w-2\\/3")))
            detail_soup = BeautifulSoup(driver.page_source, 'html.parser')
            events_container = detail_soup.select("div.event.m-0.flex.w-full.flex-col")
            for event in events_container:
                venue = "Chase Center"
                title_element = event.select_one("a.mb-6.line-clamp-2.text-lg")
                title = title_element.text.strip().title() if title_element else "Missing"  # Capitalized
                date_time_element = event.select_one("span.mr-1.text-slate-500")
                if date_time_element:
                    date_time_parts = date_time_element.text.strip().split(" - ")
                    raw_date = date_time_parts[0] if len(date_time_parts) == 2 else "Missing"
                    try:
                        date = datetime.strptime(raw_date, "%a, %B %d").strftime("2025-%m-%d")
                    except ValueError:
                        date = "Missing"
                    time = date_time_parts[1] if len(date_time_parts) == 2 else "Missing"
                else:
                    date, time = "Missing", "Missing"
                event_link_element = event.select_one("a.rounded-full.bg-calendar-secondary")
                event_link = f"https://chasecenter.com{event_link_element['href']}" if event_link_element and 'href' in event_link_element.attrs else "Missing"
                events.append({"Venue": venue, "Title": title, "Date": date, "Time": time, "Link": event_link})
        except Exception as e:
            print(f"Error processing day: {e}")
    return month_year, events

# Run three separate passes with browser restarts
all_events = []
seen_events = set()

for pass_num in range(3):  # Three passes
    print(f"Starting pass {pass_num + 1}")
    
    # Start a new browser session
    driver = webdriver.Chrome()
    driver.get(chase_center_url_value)
    time.sleep(5)  # Wait for the page to load

    current_month = ""
    while current_month != "July 2025":
        current_month, current_events = extract_event_details(driver)
        for event in current_events:
            if (
                (event['Title'], event['Date']) not in seen_events
                and event['Title'] != "Missing"
                and event['Date'] != "Missing"
            ):
                event_date = datetime.strptime(event['Date'], "%Y-%m-%d")
                if start_date <= event_date <= end_date:
                    seen_events.add((event['Title'], event['Date']))
                    all_events.append(event)
        driver.find_element(By.CLASS_NAME, "react-calendar__navigation__next-button").click()
        time.sleep(3)

    # Close the browser for this pass
    driver.quit()

# Save unique Chase Center events to chase_center_events.xlsx
df_new = pd.DataFrame(all_events)
df_new.columns = [col.capitalize() for col in df_new.columns]  # Capitalize column names
df_new.to_excel('chase_center_events.xlsx', index=False)
print("Chase Center events saved to 'chase_center_events.xlsx'.")

# Append unique events to all_venue_events.xlsx
all_venue_file = 'all_venue_events.xlsx'
if os.path.exists(all_venue_file):
    df_existing = pd.read_excel(all_venue_file)
    # Filter only events that are not already in the file
    df_existing_set = set(zip(df_existing['Title'], df_existing['Date']))
    new_unique_events = df_new[~df_new.apply(lambda x: (x['Title'], x['Date']) in df_existing_set, axis=1)]
    df_combined = pd.concat([df_existing, new_unique_events], ignore_index=True)
    df_combined.to_excel(all_venue_file, index=False)
    print(f"Chase Center events appended to '{all_venue_file}'.")
else:
    # If the file doesn't exist, create it
    df_new.to_excel(all_venue_file, index=False)
    print(f"New file '{all_venue_file}' created with the events.")
