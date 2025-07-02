from playwright.sync_api import sync_playwright
from utils.helpers import accept_cookies, extract_categories, is_valid_category, extract_subcategories
from urllib.parse import urlparse
    
def search_category(url: str):
    """
        Open the given URL in the default web browser.
        
        Args:
            url (str): The URL to open.
    """
    brand_domain = urlparse(url).netloc
    
    with sync_playwright() as p:
        # Launch a headless browser
        browser = p.chromium.launch(headless=True)
        
        # Create a new page
        page = browser.new_page()
        page.goto(url)

        # TODO: Add a wait for the page to load completely using selectors/tags
        # Wait for the page
        page.wait_for_timeout(8000)

        # TODO: Accept cookies function need to be implemented further
        # Uncomment the line below if you have a function to accept cookies
        # accept_cookies(page)

        # Extract categories from the page
        categories = extract_categories(page, url)
        valid_categories = [cat for cat in categories if is_valid_category(cat['url'], brand_domain)]

        browser.close()

        return valid_categories
        