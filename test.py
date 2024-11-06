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

def save_data_to_csv(products, category, subcategory):
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
    # Extract category name from MAIN_CATEGORY_LINK
    category_element = page.query_selector(Selectors.MAIN_CATEGORY_LINK)
    category = category_element.inner_text() if category_element else "Unknown Category"

    # Extract subcategory name from SUB_CATEGORY
    subcategory_element = page.query_selector(Selectors.SUB_CATEGORY)
    subcategory = subcategory_element.inner_text() if subcategory_element else "Unknown Subcategory"
    
    # Clean up category and subcategory names (remove extra spaces, etc.)
    category = re.sub(r'\s+', ' ', category).strip()
    subcategory = re.sub(r'\s+', ' ', subcategory).strip()
    
    return category, subcategory

def scrape_amazon_bestsellers(url):
    # Set to track products already scraped (by name)
    scraped_products = set()

    with sync_playwright() as p:
        browser = p.chromium.launch(args=['--start-maximized'], headless=False)
        context = browser.new_context(user_agent=get_random_user_agent())
        page = context.new_page()

        try:
            page.goto(url, timeout=60000)  # Increased timeout
            time.sleep(random.uniform(2, 5))

            # Navigate to main category
            main_category = page.query_selector(Selectors.MAIN_CATEGORY_LINK)
            if main_category:
                main_category.click()
                logging.info("Navigating to main category")
                time.sleep(random.uniform(2, 5))

            category_name, subcategory_name = extract_category_and_subcategory(page)
            logging.info(f"Category Name: {category_name}, Subcategory Name: {subcategory_name}")

            # Navigate to subcategory
            sub_category = page.query_selector(Selectors.SUB_CATEGORY)
            if sub_category:
                sub_category.click()
                logging.info("Navigating to subcategory")
                time.sleep(random.uniform(2, 5))

                # Scroll a few times to load more products
                for _ in range(5):
                    page.evaluate("window.scrollBy(0, window.innerHeight);")
                    time.sleep(random.uniform(2, 4))

            # Select brand (optional)
            brand_link = page.query_selector(Selectors.BRAND_LINK)
            if brand_link:
                brand_link.click()
                logging.info("Navigating to brand page")
                time.sleep(random.uniform(5, 10))

            products = []
            while True:
                # Ensure products are loaded before scraping
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
                    
                    products.append(product_info)
                    scraped_products.add(product_info["name"])  # Add product name to set to avoid duplicates
                    logging.info(f"Scraped product: {product_info}")

                # Save data after scraping the current page
                save_data_to_csv(products, category_name, subcategory_name)
                products = []

                # Wait for the next button and click it if available
                next_button = page.query_selector(Selectors.NEXT_BUTTON)
                if next_button and next_button.is_enabled():
                    logging.info("Navigating to next page...")
                    next_button.click()

                    logging.info("Page loaded, scraping next page...")
                    time.sleep(random.uniform(3, 5))  # Adding a small delay before scraping again
                else:
                    logging.info("No more pages to navigate.")
                    break

        except Exception as e:
            logging.error(f"An error occurred: {e}")
        finally:
            browser.close()

if __name__ == "__main__":
    url = "https://www.amazon.in"
    scrape_amazon_bestsellers(url)
