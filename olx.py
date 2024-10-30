from playwright.sync_api import sync_playwright
import time
import random
import os
import csv
import re

def launch_browser(playwright, headless=True):
    browser = playwright.chromium.launch(headless=headless, args=["--disable-blink-features=AutomationControlled"])
    return browser

def navigate_to_page(browser, url):
    page = browser.new_page(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.81 Safari/537.36",
        permissions=["geolocation"]
    )
    page.set_viewport_size({"width": 1280, "height": 800})
    page.goto(url)
    page.wait_for_load_state("networkidle")
    return page

def random_delay(min_delay=1, max_delay=3):
    time.sleep(random.uniform(min_delay, max_delay))

def set_location(page, location):
    try:
        # Wait for the location input to be available
        location_box = page.wait_for_selector("input[autocomplete='location-search']")
        location_box.fill(location)
        random_delay()

        # Wait for the suggestions to appear
        suggestions = page.locator("div._53cb8cc6 div._948d9e0a.b9e631ef._371e9918")
        
        # Get the count of suggestions
        suggestion_count = suggestions.count()
        
        # Check each suggestion until a match is found
        for i in range(suggestion_count):
            suggestion = suggestions.nth(i)
            suggestion_text = suggestion.inner_text()
            
            # If the location matches the suggestion, click it
            if location.lower() in suggestion_text.lower():
                suggestion.click()
                random_delay()
                print(f"Location set to: {suggestion_text}")
                return  # Exit the function after successfully setting the location
        
        # If no match was found after checking all suggestions
        print("No exact location match found.")
        
    except Exception as e:
        print(f"Location setting failed: {e}")


def search_honda_civic(page, search_query, location):
    set_location(page, location)
    try:
        search_box = page.wait_for_selector("input[type='search']")
        search_box.fill(search_query)
        random_delay()
        search_box.press("Enter")
        page.wait_for_load_state("networkidle")
        random_delay()
    except Exception as e:
        print(f"Search failed: {e}")

def collect_ads(page, csv_writer):
    try:
        unique_ads = set()
        while True:
            random_delay()
            ads = page.query_selector_all("li.undefined")
            if not ads:
                print("No more ads found.")
                break

            for ad in ads:
                title = ad.query_selector("h2._941ffa5e").inner_text() if ad.query_selector("h2._941ffa5e") else "No Title"
                price = ad.query_selector("span._1f2a2b47").inner_text() if ad.query_selector("span._1f2a2b47") else "No Price"
                location_text = ad.query_selector("span._77000f35").inner_text() if ad.query_selector("span._77000f35") else "No Location"

                ad_identifier = (title, price, location_text) 
                
                if ad_identifier not in unique_ads:
                    unique_ads.add(ad_identifier) 
                    print(f"Title: {title}, Price: {price}, Location: {location_text}")
                    csv_writer.writerow([title, price, location_text])
                else:
                    print(f"Duplicate ad found: {title}")

            load_more_button = page.locator("button:has-text('Load more')")
            if load_more_button.is_visible():
                load_more_button.click()
                random_delay()
            else:
                print("No more ads to load.")
                break
    except Exception as e:
        print(f"Ad collection failed: {e}")

def run(url, search_query, location):
    search_query_safe = re.sub(r'[<>:"/\\|?*]', '', search_query)
    location_safe = re.sub(r'[<>:"/\\|?*]', '', location)
    cars_dir = f"cars/{location_safe}/{search_query_safe}"
    os.makedirs(cars_dir, exist_ok=True)

    csv_file_path = os.path.join(cars_dir, "ads.csv")
    
    with open(csv_file_path, mode='w', newline='', encoding='utf-8') as csv_file:
        csv_writer = csv.writer(csv_file)
        csv_writer.writerow(["Title", "Price", "Location"])

        with sync_playwright() as playwright:
            browser = launch_browser(playwright, headless=False)
            page = navigate_to_page(browser, url)
            search_honda_civic(page, search_query, location)
            collect_ads(page, csv_writer)
            browser.close()

url = "https://www.olx.com.pk"
search_query = "Honda Civic 2017"
location = "Lahore"
run(url, search_query, location)
