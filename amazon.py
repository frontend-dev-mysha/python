from playwright.sync_api import sync_playwright
import random
import time
import logging
import csv
import os

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

class Selectors:
    MAIN_CATEGORY_LINK = "a[href='/electronics/b/?ie=UTF8&node=976419031&ref_=nav_cs_electronics']"
    ALL_SUBCATEGORIES = "#sobe_d_b_ms_7-carousel-viewport .sl-sobe-carousel-viewport-row ol.sl-sobe-carousel-viewport-row-inner li.sl-sobe-carousel-sub-card a"
    ALL_BRANDS = [
        "#sobe_d_b_ms_4-carousel-viewport .sl-sobe-carousel-viewport-row ol.sl-sobe-carousel-viewport-row-inner li.sl-sobe-carousel-sub-card a",
        "#sobe_d_b_ms_8-carousel-viewport .sl-sobe-carousel-viewport-row ol.sl-sobe-carousel-viewport-row-inner li.sl-sobe-carousel-sub-card a",
        "#sobe_d_b_ms_14-carousel-viewport .sl-sobe-carousel-viewport-row ol.sl-sobe-carousel-viewport-row-inner li.sl-sobe-carousel-sub-card a"
    ]
    ALL_ITEMS = ".s-main-slot .s-result-item"
    NAME_OF_ITEM = "h2.a-size-mini span"
    RATING_OF_ITEM = "span[aria-label*='out of 5 stars']"
    PRICE_OF_ITEM = ".a-price .a-offscreen"
    NEXT_BUTTON = ".s-pagination-next.s-pagination-button"

def get_random_user_agent():
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Gecko/20100101 Firefox/89.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36",
        "Mozilla/5.0 (Linux; Android 10; Pixel 3 XL) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Mobile Safari/537.36",
    ]
    return random.choice(user_agents)

def extract_product_info(product):
    name = product.query_selector(Selectors.NAME_OF_ITEM).inner_text() if product.query_selector(Selectors.NAME_OF_ITEM) else "No Name"
    rating = product.query_selector(Selectors.RATING_OF_ITEM).get_attribute("aria-label") if product.query_selector(Selectors.RATING_OF_ITEM) else "No Rating"
    price = product.query_selector(Selectors.PRICE_OF_ITEM).inner_text() if product.query_selector(Selectors.PRICE_OF_ITEM) else "No Price"
    
    # Exclude products with no price
    if price == "No Price":
        return None  # Skip this product
    
    return {
        "name": name,
        "rating": rating,
        "price": price,
    }

def save_data_to_csv(products):
    """Save scraped product data to a CSV file."""
    directory = f"data/"
    os.makedirs(directory, exist_ok=True)
    
    csv_file = f"{directory}/products.csv"
    with open(csv_file, mode="a", newline='', encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=["name", "rating", "price"])
        if file.tell() == 0:
            writer.writeheader()
        writer.writerows(products)
    logging.info(f"Data saved to {csv_file}")

def navigate_to_main_category(page):
    main_category_link = page.query_selector(Selectors.MAIN_CATEGORY_LINK)
    if main_category_link:
        main_category_link.click()
        time.sleep(random.uniform(2, 5)) 
    else:
        logging.warning("Main category link not found!")

def navigate_to_brand(page, brand,index):
    brand.click()
    time.sleep(random.uniform(3, 5))
    page.wait_for_load_state("load", timeout=60000)
    time.sleep(random.uniform(2, 5)) 

def scrape_brand_products(page, scraped_products):
    brand_products = []
    while True:
        product_elements = page.query_selector_all(Selectors.ALL_ITEMS)
        if not product_elements:
            logging.warning("No products found on this page.")
            break

        for product in product_elements:
            product_info = extract_product_info(product)
            
            if product_info is None:
                continue  # Skip products with no price

            # Check for duplicates based on product name
            if product_info["name"] in scraped_products:
                logging.info(f"Duplicate product found: {product_info['name']}, skipping.")
                continue
            
            brand_products.append(product_info)
            scraped_products.add(product_info["name"])  # Add product name to set to avoid duplicates
            logging.info(f"Scraped product: {product_info}")

        # Save brand-specific data
        save_data_to_csv(brand_products)
        brand_products = []

        # Check if there's a "Next" button for pagination
        next_button = page.query_selector(Selectors.NEXT_BUTTON)
        if next_button and next_button.is_enabled():
            logging.info("Navigating to next page...")
            next_button.click()
            logging.info("Page loaded, scraping next page...")
            time.sleep(random.uniform(3, 5))  
        else:
            logging.info("No more pages to navigate.")
            break

def go_back_to_brands_page(page, brand_listing_url):
    """Navigate directly to the brand list page and wait for brand links to load."""
    logging.info("Returning to the brand list after scraping products.")
    try:
        # Navigate directly to the brand listing page
        logging.info(f"Navigating back to the brand listing URL: {brand_listing_url}")
        page.goto(brand_listing_url, timeout=60000)  # Go to the saved brand listing URL
        
        # Wait for the brand links to load (page must be loaded fully before interacting with it)
        page.wait_for_selector(Selectors.ALL_BRANDS[0], timeout=60000)  # Check first brand selector in list
        logging.info("Successfully returned to the brand listing page.")
    except TimeoutError:
        logging.error("Timeout while navigating back to the brand listing page.")
    except Exception as e:
        logging.error(f"An unexpected error occurred while returning to the brand listing page: {e}")

def scrape_all_brands(page, scraped_products):
    for selector in Selectors.ALL_BRANDS:
        brand_listing_url = page.url  # Save the initial brand listing page URL
        logging.info(f"Brand Listing URL: {brand_listing_url}")

        try:
            all_brands = page.query_selector_all(selector)
            if not all_brands:
                logging.warning(f"No brands found for selector {selector}.")
                continue

            logging.info(f"Found {len(all_brands)} brands using selector {selector}.")

            for index in range(len(all_brands)):
                # Re-fetch the list of brands each time after navigating back to brand list page
                go_back_to_brands_page(page, brand_listing_url)
                all_brands = page.query_selector_all(selector)

                if index >= len(all_brands):
                    logging.warning(f"Brand index {index} out of range after re-fetching.")
                    break
                
                brand = all_brands[index]
                
                # Navigate to the brand page
                navigate_to_brand(page, brand, index)
                scrape_brand_products(page, scraped_products)
                
                # Log the navigation
                logging.info(f"Finished scraping for brand {index}, returning to brand list.")
        
        except Exception as e:
            logging.error(f"An error occurred while processing brands for selector {selector}: {e}")

def navigate_to_subcategory(page, sub_category, index, scraped_products):
    sub_category.click()
    time.sleep(random.uniform(3, 5))  # Wait for the subcategory to load
    page.wait_for_load_state("load", timeout=60000)
    time.sleep(random.uniform(2, 5)) 
    
    # Now scrape brands for this subcategory
    scrape_all_brands(page,scraped_products)
    time.sleep(random.uniform(2, 5))

def scrap_all_sub_categories(page,scraped_products):
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
        navigate_to_subcategory(page, sub_category, index,scraped_products)

        # Go back to the subcategory overview page after processing
        page.go_back()
        time.sleep(random.uniform(3, 5))  # Allow time for the page to reload
        
        # Refresh the list of subcategories after going back to ensure it's up to date
        all_sub_categories = page.query_selector_all(Selectors.ALL_SUBCATEGORIES)

def scrape_amazon_bestsellers(url):
    scraped_products = set()
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
            scrap_all_sub_categories(page,scraped_products)
            scrape_all_brands(page, scraped_products)

        except Exception as e:
            logging.error(f"An error occurred: {e}")
        finally:
            browser.close()

if __name__ == "__main__":
    url = "https://www.amazon.in"
    scrape_amazon_bestsellers(url)