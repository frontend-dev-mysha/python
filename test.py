from playwright.sync_api import sync_playwright
import random
import time
import csv
import os
import re

class Selectors:
    MAIN_CATEGORY_LINK = "a[href='/electronics/b/?ie=UTF8&node=976419031&ref_=nav_cs_electronics']"
    SUB_CATEGORY = "li#sobe_d_b_ms_7_1 a.sl-sobe-carousel-sub-card-link"
    BRAND_LINK = "a.sl-sobe-carousel-sub-card-link img[alt='HP']"
    ALL_ITEMS = ".s-main-slot .s-result-item"
    NAME_OF_ITEM = "h2.a-size-mini span"
    RATING_OF_ITEM = "span[aria-label*='out of 5 stars']"
    PRICE_OF_ITEM = ".a-price .a-offscreen"
    NEXT_BUTTON = ".s-pagination-next.s-pagination-button"
    CATEGORY_NAME = ".s-navigation-item"  # Assuming this contains category names
    SUBCATEGORY_NAME = ".s-breadcrumb .a-breadcrumb"  # Adjust based on actual structure


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
    
    return {
        "name": name,
        "rating": rating,
        "price": price,
    }

def save_data_to_csv(products, category, subcategory):
    # Create directory structure
    directory = f"data/{category}/{subcategory}"
    os.makedirs(directory, exist_ok=True)
    
    # Save data to CSV
    csv_file = f"{directory}/products.csv"
    with open(csv_file, mode="a", newline='', encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=["name", "rating", "price"])
        if file.tell() == 0:  # Write header if file is empty
            writer.writeheader()
        writer.writerows(products)
    print(f"Data saved to {csv_file}")

def extract_category_and_subcategory(page):
    # Try to find the category name
    category_element = page.query_selector(Selectors.CATEGORY_NAME)
    category = category_element.inner_text() if category_element else "Unknown Category"

    # Try to find the subcategory name
    subcategory_elements = page.query_selector_all(Selectors.SUBCATEGORY_NAME)
    subcategory = subcategory_elements[-1].inner_text() if subcategory_elements else "Unknown Subcategory"

    # Clean up category and subcategory names
    category = re.sub(r'\s+', ' ', category).strip()
    subcategory = re.sub(r'\s+', ' ', subcategory).strip()
    
    return category, subcategory

def scrape_amazon_bestsellers(url):
    with sync_playwright() as p:
        browser = p.chromium.launch(args=['--start-maximized'], headless=False)
        context = browser.new_context(user_agent=get_random_user_agent())
        page = context.new_page()

        try:
            page.goto(url)
            time.sleep(random.uniform(2, 5))

            # Navigate to main category
            main_category = page.query_selector(Selectors.MAIN_CATEGORY_LINK)
            if main_category:
                main_category.click()
                print("Navigating to main category")
                time.sleep(random.uniform(2, 5))

            # Extract category and subcategory from the page
            category_name, subcategory_name = extract_category_and_subcategory(page)
            print(f"Category Name: {category_name}, Subcategory Name: {subcategory_name}")

            # Navigate to subcategory
            sub_category = page.query_selector(Selectors.SUB_CATEGORY)
            if sub_category:
                sub_category.click()
                print("Navigating to subcategory")
                time.sleep(random.uniform(2, 5))

                # Scroll to load more products
                for _ in range(5):  # Scroll a few times to load more products
                    page.evaluate("window.scrollBy(0, window.innerHeight);")
                    time.sleep(random.uniform(2, 4)) 
            
            # Select brand
            brand_link = page.query_selector(Selectors.BRAND_LINK)
            if brand_link:
                brand_link.click()
                print("Navigating to brand page")
                time.sleep(random.uniform(5, 10))

            # Start scraping products with pagination
            products = []
            while True:
                product_elements = page.query_selector_all(Selectors.ALL_ITEMS)
                
                for product in product_elements:
                    product_info = extract_product_info(product)
                    products.append(product_info)
                    print(product_info)
                
                # Save data after each page to avoid losing progress
                save_data_to_csv(products, category_name, subcategory_name)
                products = []  # Clear list after saving

                # Check for the presence of the Next button
                next_button = page.query_selector(Selectors.NEXT_BUTTON)
                if next_button and next_button.is_enabled():
                    next_button.click()
                    print("Navigating to next page")
                    page.wait_for_load_state('networkidle')
                    time.sleep(random.uniform(2, 5))
                else:
                    print("No more pages to navigate.")
                    break

        except Exception as e:
            print(f"An error occurred: {e}")
        finally:
            browser.close()

if __name__ == "__main__":
    url = "https://www.amazon.in"
    scrape_amazon_bestsellers(url)
