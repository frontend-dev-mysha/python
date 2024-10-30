from playwright.sync_api import sync_playwright
import time
import random

def launch_browser(playwright, headless=True):
    return playwright.chromium.launch(headless=headless, args=["--disable-blink-features=AutomationControlled"])


def navigate_to_page(browser, url):
    page = browser.new_page(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.81 Safari/537.36")
    page.set_viewport_size({"width": 1280, "height": 800})
    page.goto(url)
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
    time.sleep(2)

def search_honda_civic(page,search_query,location):
    search_box = page.locator("input[type='search']") 
    search_box.fill(search_query)
    random_delay()

    location_box=page.locator("input:has-text('Location or Compound)")
    location_box.fill(location)
    
    search_button = page.locator("button.bb5acd8e")
    search_button.click()
    random_delay()

def logout(page):
    page.click("img.d35c6963") 
    time.sleep(1)

    page.click("div:has-text('Logout')") 
    time.sleep(2)
    print("Logout completed.")

def run(url, email, password,search_query,location):
    with sync_playwright() as playwright:
        browser = launch_browser(playwright, headless=False)
        page = navigate_to_page(browser, url)
        open_login_popup(page)
        login_with_email(page, email, password)
        print("Login completed.")
        search_honda_civic(page,search_query,location)

    
        logout(page)

        browser.close()

url = "https://www.olx.com.pk"
email = "kashifsaeed9566@gmail.com"
password = "Kashifsaeed@9566"
search_query="Honda civic 2017"
location="Lahore"
run(url, email, password,search_query,location)
