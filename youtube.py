import csv
import random
import logging
import time
from playwright.sync_api import sync_playwright

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

class Selectors:
    SEARCH_BAR = "#search-input input"
    SEARCH_BUTTON = "#search-icon-legacy"
    FILTER_BUTTON = "#filter-button"
    CHANNEL_FILTER = "a#endpoint[href*='EgIQAg%253D%253D']"  # Channel filter
    CHANNEL_CONTAINER = "#contents ytd-channel-renderer"
    CHANNEL_NAME = "#channel-title"  # Channel name selector for each result
    CHANNEL_SUBSCRIBER_COUNT = "#metadata subscribers #video-count"  # Subscriber count selector
    CHANNEL_DESCRIPTION = "#description"  # Channel description selector
    CHANNEL_AVATAR = "#avatar img"  # Avatar image selector

# Function to generate random user agents
def get_random_user_agents():
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Gecko/20100101 Firefox/89.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36",
        "Mozilla/5.0 (Linux; Android 10; Pixel 3 XL) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Mobile Safari/537.36",
    ]
    return random.choice(user_agents)

# Function to perform a search
def search_bar(page):
    try:
        # Locate the search bar
        search_input = page.wait_for_selector(Selectors.SEARCH_BAR, timeout=5000)
        logging.info("Search bar found!")

        # Clear any pre-filled text in the search bar
        search_input.click()  
        page.keyboard.press("Control+A")  
        page.keyboard.press("Backspace") 

        # Mimic human typing
        query = "Playwright tutorial"  # Replace with desired query
        for char in query:
            search_input.type(char, delay=random.uniform(100, 300))  # Typing delay
        logging.info("Query typed into search bar.")

        # Locate and click the search button
        search_button = page.wait_for_selector(Selectors.SEARCH_BUTTON, timeout=5000)
        search_button.click()
        logging.info("Search button clicked!")

        # Wait for the search results to load (adjust the sleep time as needed)
        time.sleep(random.uniform(3, 6))  # Simulate human-like delay after clicking the search button

        return True
    except Exception as e:
        logging.error(f"Error in search_bar function: {e}")
        return False

# Function to simulate faster human-like scrolling with random speed and delay
def fast_scroll(page, scroll_delay_range=(1, 2), scroll_increment_range=(100, 500)):
    try:
        logging.info("Starting faster scroll...")
        scroll_increment = random.randint(*scroll_increment_range)  # Randomize scroll amount
        page.evaluate(f"window.scrollBy(0, {scroll_increment})")  # Scroll vertically
        logging.info(f"Scrolled by {scroll_increment} pixels.")
        time.sleep(random.uniform(*scroll_delay_range))  # Random delay between scrolls
    except Exception as e:
        logging.error(f"Error in fast_scroll function: {e}")

# Function to click the "Filter" button
def filter_for_channels(page):
    try:
        # Locate and click the Filter button
        filter_button = page.wait_for_selector(Selectors.FILTER_BUTTON, timeout=5000)
        logging.info("Filter button found!")
        filter_button.click()
        logging.info("Filter button clicked!")
        time.sleep(random.uniform(2, 4))  # Wait for filter options to load
        return True
    except Exception as e:
        logging.error(f"Error in filter_for_channels function: {e}")
        return False

# Function to apply the "Channel" filter
def select_channel_filter(page):
    try:
        # Locate and click the Channel filter
        channel_filter = page.wait_for_selector(Selectors.CHANNEL_FILTER, timeout=5000)
        logging.info("Channel filter found!")
        channel_filter.click()
        logging.info("Channel filter applied!")
        return True
    except Exception as e:
        logging.error(f"Error in select_channel_filter function: {e}")
        return False

def extract_channel_details(page):
    try:
        # Add a wait for channel containers to load properly after the filter is applied
        page.wait_for_selector(Selectors.CHANNEL_CONTAINER, timeout=10000)  # Wait for channel containers to appear
        logging.info("Channel containers found!")
        
        # Try selecting the correct container for channels
        channel_containers = page.query_selector_all(Selectors.CHANNEL_CONTAINER)
        if not channel_containers:
            logging.warning("No channel containers found.")
        
        channel_details = []

        # Iterate through each container to extract channel details
        for container in channel_containers:
            # Look for a more accurate channel name element inside the container
            channel_name = container.query_selector(Selectors.CHANNEL_NAME) or container.query_selector("div.ytd-channel-renderer #text")  # Fallback selector
            title = channel_name.text_content().strip() if channel_name else "No title"
            
            # Get additional channel information (subscribers, description, avatar)
            subscriber_count = container.query_selector(Selectors.CHANNEL_SUBSCRIBER_COUNT)
            description = container.query_selector(Selectors.CHANNEL_DESCRIPTION)
            avatar = container.query_selector(Selectors.CHANNEL_AVATAR)

            subscribers = subscriber_count.text_content().strip() if subscriber_count else "No subscriber info"
            desc = description.text_content().strip() if description else "No description"
            avatar_url = avatar.get_attribute('src') if avatar else "No avatar"

            # Logging the extracted channel name and details
            channel_details.append({
                "title": title,
                "subscribers": subscribers,
                "description": desc,
                "avatar": avatar_url,
            })
            logging.info(f"Extracted details for channel: {title}")

        return channel_details
    except Exception as e:
        logging.error(f"Error in extract_channel_details: {e}")
        return []

# Function to save the extracted details to a CSV file
def save_to_csv(channel_details, filename="channel_details.csv"):
    try:
        # Define the header for the CSV file
        fieldnames = ["title", "subscribers", "description", "avatar"]
        
        # Open the CSV file in write mode
        with open(filename, mode="w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            
            # Write the header
            writer.writeheader()
            
            # Write the data rows
            for detail in channel_details:
                writer.writerow(detail)
        
        logging.info(f"Channel details saved to {filename}")
    except Exception as e:
        logging.error(f"Error saving to CSV: {e}")

# Function to continuously scroll and collect channels
def scroll_and_collect_channels(page, max_scrolls=10, scroll_delay_range=(1, 2), scroll_increment_range=(100, 500)):
    all_channel_details = []
    channels_collected = 0

    for _ in range(max_scrolls):
        # Perform scrolling and extract channel details
        fast_scroll(page, scroll_delay_range, scroll_increment_range)
        
        # Extract and collect channel details after scrolling
        new_channel_details = extract_channel_details(page)
        if new_channel_details:
            all_channel_details.extend(new_channel_details)
            channels_collected += len(new_channel_details)
            logging.info(f"Loaded more channels: {channels_collected} new channels.")
        else:
            logging.info("No new channels loaded, stopping the scroll.")
            break

        # Check if the page is still loading more channels
        if len(new_channel_details) == 0:
            logging.info(f"No more new channels found. Total channels collected: {channels_collected}")
            break
        
        time.sleep(random.uniform(2, 4))  # Sleep before next scroll
        
    return all_channel_details

# Main function to control the workflow
def main_youtube_scraper(url):
    with sync_playwright() as p:
        # Launch the browser
        browser = p.chromium.launch(headless=False)  # Set to True for headless mode
        context = browser.new_context(user_agent=get_random_user_agents())
        page = context.new_page()

        try:
            logging.info(f"Visiting: {url}")
            page.goto(url, timeout=60000)  # Open YouTube
            time.sleep(random.uniform(2, 5))  # Wait for the page to load

            # Perform search operation
            if search_bar(page):
                # Apply filters and select "Channels"
                if filter_for_channels(page):
                    if select_channel_filter(page):
                        # Scrape channels continuously while scrolling
                        all_channel_details = scroll_and_collect_channels(page)

                        # Save the data to a CSV file
                        save_to_csv(all_channel_details)
        except Exception as e:
            logging.error(f"An error occurred: {e}")
        finally:
            logging.info("Closing browser.")
            browser.close()

# Call the main function with YouTube URL
if __name__ == "__main__":
    main_youtube_scraper("https://www.youtube.com/")
