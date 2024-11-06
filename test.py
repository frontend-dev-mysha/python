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
    """Extract product details from the product element."""
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

def save_data_to_csv(products, category, subcategory):
    """Save scraped product data to a CSV file."""
    directory = f"data/{category}/{subcategory}"
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
    href = brand_link.get_attribute('href')
    if href:
        logging.info(f"Navigating to brand page: {href}")
        brand_link.click()
        time.sleep(random.uniform(5, 10))

def scrape_brand_products(page, category_name, subcategory_name, scraped_products):
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
        save_data_to_csv(brand_products, category_name, subcategory_name)
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

    # Re-query brand links after navigating to the brand listing URL
    page.wait_for_selector(Selectors.ALL_BRANDS, timeout=60000)  # Ensure the brand links are loaded
    brand_links = page.query_selector_all(Selectors.ALL_BRANDS)
    
    if not brand_links:
        logging.error("No brand links found on the brand listing page.")
        return

    for i, brand_link in enumerate(brand_links):
        try:
            # Ensure the link is valid by querying it again after waiting for the page to load
            logging.info(f"Navigating to brand page {i+1}")
            page.wait_for_selector(Selectors.BRAND_LINK, timeout=60000)  # Wait for a brand link to be visible
            navigate_to_brand_page(page, brand_link)

            # After navigation, wait for products to load
            scrape_brand_products(page, category_name, subcategory_name, scraped_products)

            # After scraping the brand, navigate directly back to the brand list page using the brand_listing_url
            go_back_to_brands_page(page, brand_listing_url)

            # Re-query brand links after going back to ensure we're working with the updated page
            page.wait_for_selector(Selectors.ALL_BRANDS, timeout=60000)
            brand_links = page.query_selector_all(Selectors.ALL_BRANDS)
            if not brand_links:
                logging.error("Brand links not found after returning to the brand listing page.")
                break

        except Exception as e:
            logging.error(f"An error occurred while processing brand {i+1}: {e}")

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
