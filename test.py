from playwright.sync_api import sync_playwright
import random
import time
import csv
import os
import re
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

class Selectors:
    MAIN_CATEGORY_LINK = "a[href='/electronics/b/?ie=UTF8&node=976419031&ref_=nav_cs_electronics']"
    SUB_CATEGORY = "li#sobe_d_b_ms_7_1 a.sl-sobe-carousel-sub-card-link"
    ALL_BRANDS = "#sobe_d_b_ms_4-carousel-viewport .sl-sobe-carousel-viewport-row ol.sl-sobe-carousel-viewport-row-inner li.sl-sobe-carousel-sub-card a"
    BRAND_LINK = "a.sl-sobe-carousel-sub-card-link img[alt='HP']"
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

def save_data_to_csv(products, category, subcategory,brand_name):
    """Save scraped product data to a CSV file."""
    directory = f"data/{category}/{subcategory}/{brand_name}"
    os.makedirs(directory, exist_ok=True)
    
    csv_file = f"{directory}/products.csv"
    with open(csv_file, mode="a", newline='', encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=["name", "rating", "price"])
        if file.tell() == 0:
            writer.writeheader()
        writer.writerows(products)
    logging.info(f"Data saved to {csv_file}")

def extract_category_and_subcategory(page):
    """Extract the category and subcategory from the page."""
    category_element = page.query_selector(Selectors.MAIN_CATEGORY_LINK)
    category = category_element.inner_text() if category_element else "Unknown Category"

    subcategory_element = page.query_selector(Selectors.SUB_CATEGORY)
    subcategory = subcategory_element.inner_text() if subcategory_element else "Unknown Subcategory"

    
    category = re.sub(r'\s+', ' ', category).strip()
    subcategory = re.sub(r'\s+', ' ', subcategory).strip()
    

    return category, subcategory

def navigate_to_category(page):
    """Navigate to the main category."""
    main_category = page.query_selector(Selectors.MAIN_CATEGORY_LINK)
    if main_category:
        main_category.click()
        logging.info("Navigating to main category")
        time.sleep(random.uniform(2, 5))

def navigate_to_subcategory(page):
    """Navigate to the subcategory."""
    sub_category = page.query_selector(Selectors.SUB_CATEGORY)
    if sub_category:
        sub_category.click()
        logging.info("Navigating to subcategory")
        time.sleep(random.uniform(2, 5))
        # Scroll a few times to load more products
        for _ in range(2):
            page.evaluate("window.scrollBy(0, window.innerHeight);")
            time.sleep(random.uniform(2, 4))

def navigate_to_brand_page(page, brand_link):
    """Navigate to a specific brand's page."""
    try:
        if brand_link.is_visible() and brand_link.is_enabled():
            href = brand_link.get_attribute('href')
            if href:
                logging.info(f"Navigating to brand page: {href}")
                brand_link.click()
                time.sleep(random.uniform(5, 10))
    except Exception as e:
        logging.error(f"Error navigating to brand page: {e}")


def scrape_brand_products(page, category_name, subcategory_name, scraped_products,brand_name):
    """Scrape all products for a specific brand's page."""
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
        save_data_to_csv(brand_products, category_name, subcategory_name,brand_name)
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
        page.wait_for_selector(Selectors.ALL_BRANDS, timeout=60000)
        logging.info("Successfully returned to the brand listing page.")
    except TimeoutError:
        logging.error("Timeout while navigating back to the brand listing page.")

def scrape_all_brands(page, category_name, subcategory_name, scraped_products):
    """Scrape products for all brands in the brand listing page."""
    brand_listing_url = page.url
    logging.info(f"Brand Listing URL: {brand_listing_url}")

    # Track the index of the current brand being processed
    current_brand_index = 0

    while True:
        # Navigate back to the brand listing page and re-fetch the brand links
        page.goto(brand_listing_url, timeout=60000)
        page.wait_for_selector(Selectors.ALL_BRANDS, timeout=60000)
        
        # Retrieve brand links after navigating back to the listing page
        brand_links = page.query_selector_all(Selectors.ALL_BRANDS)
        if not brand_links:
            logging.error("No brand links found on the brand listing page.")
            break

        # Iterate starting from the current brand index
        for i in range(current_brand_index, len(brand_links)):
            brand_link = brand_links[i]
            try:
                # Extract the brand name from the 'alt' attribute of the image inside the anchor tag
                brand_img = brand_link.query_selector("img")
                brand_name = brand_img.get_attribute("alt") if brand_img else None
                
                # If alt attribute is missing or empty, fallback to using the inner text or href
                if not brand_name:
                    brand_name = brand_link.inner_text().strip()  # fallback to inner text
                if not brand_name:
                    brand_name = brand_link.get_attribute("href").split('/')[-1] if brand_link.get_attribute("href") else f"Brand_{i+1}"

                logging.info(f"Processing brand Name: {brand_name}")
                logging.info(f"Navigating to brand page {i + 1}")
                navigate_to_brand_page(page, brand_link)
                scrape_brand_products(page, category_name, subcategory_name, scraped_products,brand_name)

                # After scraping, increment the index and go back to the brand list
                current_brand_index = i + 1  # Move to the next brand
                go_back_to_brands_page(page, brand_listing_url)
                break  # Break to re-fetch brand links with the updated page

            except Exception as e:
                logging.error(f"An error occurred while processing brand {i + 1}: {e}")
                continue  # Continue to the next brand in case of an error

        # If we reach the end of the list, exit the loop
        if current_brand_index >= len(brand_links):
            logging.info("All brands have been processed.")
            break


def scrape_amazon_bestsellers(url):
    """Main function to scrape Amazon bestsellers."""
    # Set to track products already scraped (by name)
    scraped_products = set()

    with sync_playwright() as p:
        browser = p.chromium.launch(args=['--start-maximized'], headless=False)
        context = browser.new_context(user_agent=get_random_user_agent())
        page = context.new_page()

        try:
            page.goto(url, timeout=60000)  # Increased timeout
            time.sleep(random.uniform(2, 5))

            # Navigate to the category page
            navigate_to_category(page)

            # Extract category and subcategory info
            category_name, subcategory_name = extract_category_and_subcategory(page)
            logging.info(f"Category Name: {category_name}, Subcategory Name: {subcategory_name}")

            # Navigate to the subcategory page
            navigate_to_subcategory(page)

            # Scrape products from all brands
            scrape_all_brands(page, category_name, subcategory_name, scraped_products)

        except Exception as e:
            logging.error(f"An error occurred: {e}")
        finally:
            browser.close()

if __name__ == "__main__":
    url = "https://www.amazon.in"
    scrape_amazon_bestsellers(url)