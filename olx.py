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

def open_login_popup(page):
    page.hover("div._948d9e0a button._37208bb9")
    random_delay()
    page.click("div._948d9e0a button._37208bb9")
    random_delay()

    page.locator("button:has-text('Login with Email')").hover()
    random_delay()
    page.locator("button:has-text('Login with Email')").click()
    random_delay()

def login_with_email(page, email, password):
    page.fill("input[name='email']", email)
    page.fill("input[name='password']", password)
    time.sleep(1)


    page.click("button._91e21052")

def set_location(page, location, max_retries=5, retry_delay=2):
    try:
        location_box = page.wait_for_selector("input[autocomplete='location-search']", timeout=5000)
        
        # clear previous text
        location_box.fill("")
        random_delay()

        # simulate human like typing
        location_box.click()
        for char in location:
            location_box.press(char)
            time.sleep(random.uniform(0.1, 0.3)) 

            # check if any suggestion macthes while typing
            suggestions = page.locator("div._53cb8cc6 div._948d9e0a.b9e631ef._371e9918")
            suggestion_count = suggestions.count()

            if suggestion_count > 0:
                for i in range(suggestion_count):
                    suggestion = suggestions.nth(i)
                    suggestion_text = suggestion.inner_text()
                    
                    if location.lower() in suggestion_text.lower():
                        suggestion.click()
                        random_delay()
                        print(f"Location set to: {suggestion_text}")
                        return 

        # retry => if suggestion not found
        for attempt in range(max_retries):
            print(f"No matching suggestion found on attempt {attempt + 1}. Retrying in {retry_delay} seconds...")
            time.sleep(retry_delay)

            suggestions = page.locator("div._53cb8cc6 div._948d9e0a.b9e631ef._371e9918")
            suggestion_count = suggestions.count()

            if suggestion_count > 0:
                for i in range(suggestion_count):
                    suggestion = suggestions.nth(i)
                    suggestion_text = suggestion.inner_text()
                    
                    if location.lower() in suggestion_text.lower():
                        suggestion.click()
                        random_delay()
                        print(f"Location set to: {suggestion_text}")
                        return  # Exit after selecting the location

        print("Exceeded maximum retries. No matching suggestions found.")
        
    except Exception as e:
        print(f"Location setting failed: {e}")

def search_olx(page, search_query, location):
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

def collect_ads(page, csv_writer, search_query, location):
    try:
        unique_ads = set()
        search_keywords = search_query.lower().split() 

        while True:
            random_delay()
            ads = page.query_selector_all("li[aria-label='Listing'] article._68441e28")
            if not ads:
                print("no more ads found.")
                break

            for ad in ads:
                title = ad.query_selector("h2._941ffa5e").inner_text() if ad.query_selector("h2._941ffa5e") else "No Title"
                price = ad.query_selector("span._1f2a2b47").inner_text() if ad.query_selector("span._1f2a2b47") else "No Price"
                location_text = ad.query_selector("span._77000f35").inner_text() if ad.query_selector("span._77000f35") else "No Location"

                # Filter ads => remove duplicates
                if (any(keyword in title.lower() for keyword in search_keywords) and 
                    location.lower() in location_text.lower()):

                    #unique identifier to prevent duplicates
                    ad_identifier = (title, price, location_text)

                    if ad_identifier not in unique_ads:
                        unique_ads.add(ad_identifier)
                        print(f"Title: {title}, Price: {price}, Location: {location_text}")
                        csv_writer.writerow([title, price, location_text])
                    else:
                        print(f"Duplicate ad found: {title}")

            # click on load more button
            load_more_button = page.locator("button:has-text('Load more')")
            if load_more_button.is_visible():
                load_more_button.click()
                random_delay()
            else:
                print("no more ads to load.")
                break
    except Exception as e:
        print(f"ad collection failed: {e}")

def logout(page):
    page.click("img.d35c6963") 
    time.sleep(1)

    page.click("div:has-text('Logout')") 
    time.sleep(2)
    print("Logout completed.")


def run(url, search_query, location, email, password):
    # Clean up location and search query for directory names
    search_query_safe = re.sub(r'[<>:"/\\|?*]', '', search_query)
    location_safe = re.sub(r'[<>:"/\\|?*]', '', location)

    # Directory structure: location/title (without "cars")
    ads_dir = os.path.join(location_safe, search_query_safe)
    os.makedirs(ads_dir, exist_ok=True)


    # Define the CSV file path within the title subdirectory
    csv_file_path = os.path.join(ads_dir, "ads.csv")
    
    with open(csv_file_path, mode='w', newline='', encoding='utf-8') as csv_file:
        csv_writer = csv.writer(csv_file)
        csv_writer.writerow(["Title", "Price", "Location"])

        with sync_playwright() as playwright:
            browser = launch_browser(playwright, headless=False)
            page = navigate_to_page(browser, url)
            open_login_popup(page)
            login_with_email(page, email, password)
            print("Login completed.")
            search_olx(page, search_query, location)
            collect_ads(page, csv_writer, search_query, location)

            logout(page)

            browser.close()




url = "https://www.olx.com.pk"
email = "kashifsaeed9566@gmail.com"
password = "Kashifsaeed@9566"
search_query = "iphone 12 pro max"
location = "Bahria Town, Lahore"
run(url, search_query, location, email, password)
