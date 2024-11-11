from playwright.sync_api import sync_playwright
import random
import time
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

class Selectors:
    MAIN_CATEGORY_LINK = "a[href='/electronics/b/?ie=UTF8&node=976419031&ref_=nav_cs_electronics']"
    ALL_SUBCATEGORIES = "#sobe_d_b_ms_7-carousel-viewport .sl-sobe-carousel-viewport-row ol.sl-sobe-carousel-viewport-row-inner li.sl-sobe-carousel-sub-card a"
    ALL_BRANDS_1 = "#sobe_d_b_ms_4-carousel-viewport .sl-sobe-carousel-viewport-row ol.sl-sobe-carousel-viewport-row-inner li.sl-sobe-carousel-sub-card a"
    ALL_BRANDS_2 = "#sobe_d_b_ms_8-carousel-viewport .sl-sobe-carousel-viewport-row ol.sl-sobe-carousel-viewport-row-inner li.sl-sobe-carousel-sub-card a"
    ALL_BRANDS_3 = "#sobe_d_b_ms_14-carousel-viewport .sl-sobe-carousel-viewport-row ol.sl-sobe-carousel-viewport-row-inner li.sl-sobe-carousel-sub-card a"
    ALL_BRANDS_4 = "#sobe_d_b_ms_8-carousel-viewport .sl-sobe-carousel-viewport-row ol.sl-sobe-carousel-viewport-row-inner li.sl-sobe-carousel-sub-card a"

def get_random_user_agent():
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Gecko/20100101 Firefox/89.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36",
        "Mozilla/5.0 (Linux; Android 10; Pixel 3 XL) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Mobile Safari/537.36",
    ]
    return random.choice(user_agents)

def navigate_to_main_category(page):
    main_category_link = page.query_selector(Selectors.MAIN_CATEGORY_LINK)
    if main_category_link:
        main_category_link.click()
        time.sleep(random.uniform(2, 5)) 
    else:
        logging.warning("Main category link not found!")

def navigate_to_brand(page, brand,index):
    brand.click()
    time.sleep(random.uniform(3, 5))  # Wait for the subcategory to load
    page.wait_for_load_state("load", timeout=60000)
    time.sleep(random.uniform(2, 5)) 
    
def scrape_all_brands(page):
    # List of selectors for the brand sections
    brand_selectors = [
        Selectors.ALL_BRANDS_1,
        Selectors.ALL_BRANDS_2,
        Selectors.ALL_BRANDS_3,
        Selectors.ALL_BRANDS_4
    ]
    
    # Iterate over the selectors and scrape brands from each section
    for selector in brand_selectors:
        # Get all brands from the current selector
        all_brands = page.query_selector_all(selector)
        
        if not all_brands:
            logging.warning(f"No brands found for selector {selector}.")
            continue

        logging.info(f"Found {len(all_brands)} brands using selector {selector}.")
        
        # Iterate through each brand in the current list
        for index, brand in enumerate(all_brands):
            # Navigate to the brand page
            navigate_to_brand(page, brand, index)
            
            # Go back to the subcategory overview page after processing
            page.go_back()
            
            # Wait for the page to reload and ensure the DOM is stable
            # Wait until the selector (brands list) is visible again, indicating page has loaded
            page.wait_for_selector(selector, state='visible')
            
            # Add a short delay to make sure the page is stable
            time.sleep(random.uniform(3, 5))  # Sleep to allow the page to reload
            
            # Re-query the brand list to get fresh element handles
            all_brands = page.query_selector_all(selector)
            
            # Safely select the brand and click it
            try:
                brand = all_brands[index]  # Re-fetch the element
                brand.click()  # Perform the click
            except Exception as e:
                logging.error(f"Error while interacting with brand {index}: {e}")

def navigate_to_subcategory(page, sub_category, index):
    sub_category.click()
    time.sleep(random.uniform(3, 5))  # Wait for the subcategory to load
    page.wait_for_load_state("load", timeout=60000)
    time.sleep(random.uniform(2, 5)) 
    
    # Now scrape brands for this subcategory
    scrape_all_brands(page)
    time.sleep(random.uniform(2, 5))

def scrap_all_sub_categories(page):
    # Get all subcategories listed in the main category
    all_sub_categories = page.query_selector_all(Selectors.ALL_SUBCATEGORIES)
    if not all_sub_categories:
        logging.warning("No subcategories found.")
        return

    logging.info(f"Found {len(all_sub_categories)} subcategories.")
    
    # Iterate through each subcategory
    for index in range(len(all_sub_categories)):
        sub_category = all_sub_categories[index]
        
        # Navigate to the subcategory page
        navigate_to_subcategory(page, sub_category, index)

        # Go back to the subcategory overview page after processing
        page.go_back()
        time.sleep(random.uniform(3, 5))  # Allow time for the page to reload
        
        # Refresh the list of subcategories after going back to ensure it's up to date
        all_sub_categories = page.query_selector_all(Selectors.ALL_SUBCATEGORIES)

def scrape_amazon_bestsellers(url):
    with sync_playwright() as p:
        browser = p.chromium.launch(args=['--start-maximized'], headless=False)
        context = browser.new_context(user_agent=get_random_user_agent())
        page = context.new_page()

        try:
            logging.info(f"Visiting: {url}")
            page.goto(url, timeout=60000) 
            time.sleep(random.uniform(2, 5))

            # Navigate to the main category and scrape subcategories
            navigate_to_main_category(page)
            scrap_all_sub_categories(page)

        except Exception as e:
            logging.error(f"An error occurred: {e}")
        finally:
            browser.close()

if __name__ == "__main__":
    url = "https://www.amazon.in"
    scrape_amazon_bestsellers(url)
