# Handles:
# - Loading category and product pages
# - Waiting for the page to load
# - Returning raw HTML

from playwright.sync_api import sync_playwright

def fetch_page(url: str, wait_for_selector: str | None) -> str:
    """
    Fetches the HTML content of a given URL using Playwright.

    Args:
        url (str): The URL of the page to fetch.
        wait_for_selector (str, optional): A CSS selector to wait for before returning the page content. Defaults to None.

    Returns:
        str: The HTML content of the page.
    """

    with sync_playwright() as p:
        # Launch a headless browser
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url)

        # Wait for the specified selector if provided
        if wait_for_selector:
            page.wait_for_selector(wait_for_selector)

        # Get the HTML content of the page
        html = page.content()

        # Close the browser
        browser.close()
        return html
