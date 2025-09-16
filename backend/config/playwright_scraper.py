# Import necessary libraries
from typing import List
import logging
from urllib.parse import urljoin
from playwright.async_api import async_playwright
from backend.config.constant import SELECTORS_TO_TRY, PRODUCT_SELECTORS, GENERIC_CONTENT_LINK

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler()]
)

# Create a logger for this module
logger = logging.getLogger(__name__)

class PlaywrightScraper:
    """Handles JavaScript-heavy websites using Playwright"""
    
    def __init__(self, headless: bool = True):
        """
            Initialize the class

            Args:
                headless (bool, optional): Whether to run browser in headless mode. Default is True.

            Returns:
                None
        """
        self.headless = headless
        self.browser = None
        self.context = None
    
    async def setup(self):
        """
            Initialize Playwright browser instance.

            Returns:
                None
        """
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=self.headless)
        self.context = await self.browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
    
    async def scrapePage(self, url: str, wait_for_selector: str = None) -> str:
        """
            Scrape the HTML content of a single page, including content rendered via JavaScript.

            Args:
                url (str): The URL of the page to scrape.
                wait_for_selector (str, optional): A CSS selector to wait for before scraping.
            
            Returns:
                str: The HTML content of the page as a string.
        """
        page = await self.context.new_page()
        
        try:
            await page.goto(url, wait_until='networkidle')
            
            # Wait for specific selector if provided
            if wait_for_selector:
                await page.wait_for_selector(wait_for_selector, timeout=10000)
            else:
                # Wait for common product-related selectors
                for selector in SELECTORS_TO_TRY:
                    try:
                        await page.wait_for_selector(selector, timeout=3000)
                        break
                    except:
                        continue
            
            # Additional wait for dynamic content
            await page.wait_for_timeout(2000)
            
            content = await page.content()
            return content
            
        except Exception as e:
            logger.error(f"Error scraping {url}: {e}")
            return ""
        finally:
            await page.close()
    
    async def discoverProducts(self, url: str, category: str = None) -> List[str]:
        """
            Discover product URLs from a given category page

            Args:
                url (str): The URL of the category page to scrape.
                category (str, optional): The name of the category.

            Returns:
                List[str]: A list of product URLs found on the category page.
        """
        page = await self.context.new_page()
        product_urls = []
        
        try:
            await page.goto(url, wait_until='networkidle')
            await page.wait_for_timeout(3000)
            
            # Try to find product links
            for selector in PRODUCT_SELECTORS:
                try:
                    links = await page.query_selector_all(selector)
                    for link in links:
                        href = await link.get_attribute('href')
                        if href:
                            full_url = urljoin(url, href)
                            if full_url not in product_urls:
                                product_urls.append(full_url)
                    
                    if product_urls:
                        break
                except:
                    continue
            
            # If no specific product links found, try generic links
            if not product_urls:
                all_links = await page.query_selector_all('a')
                for link in all_links:
                    href = await link.get_attribute('href')
                    if href and any(keyword in href.lower() for keyword in GENERIC_CONTENT_LINK):
                        full_url = urljoin(url, href)
                        product_urls.append(full_url)
            
            logger.info(f"Found {len(product_urls)} product URLs from {url}")
            return product_urls  # Limit to avoid overwhelming
            
        except Exception as e:
            logger.error(f"Error discovering products from {url}: {e}")
            return []
        finally:
            await page.close()
    
    async def cleanup(self):
        """
            Clean up browser resources used during scraping.

            Closes the browser to free up system resources.
        """
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if hasattr(self, 'playwright'):
            await self.playwright.stop()