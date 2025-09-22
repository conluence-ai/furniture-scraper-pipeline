# Import necessary libraries
import re
import time
import requests
import logging
from bs4 import BeautifulSoup
from dataclasses import asdict
from urllib.parse import urlparse, urljoin
from typing import List

# Import local module
from backend.config.product import Product
from backend.config.config import ProductScraped
from backend.utils.helpers import isValidImageSrc
from backend.config.content_extractor import AIContentExtractor

# Import constant
from backend.config.constant import (
    CATEGORY_SELECTORS,
    CATEGORY_SYNONYMS,
    PRODUCT_SELECTORS,
    PRODUCT_KEYWORDS,
    NAME_SELECTORS,
    DESC_SELECTORS,
    DESIGNER_SELECTORS,
    COMMON_ENDINGS
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler()]
)

# Create a logger for this module
logger = logging.getLogger(__name__)

# Global variables
seen_links = set()

class StaticScraper:
    """ Scrapes structured data from static HTML pages using requests and BeautifulSoup. """
    
    def __init__(self, use_ai: bool = True, openai_api_key: str = None):
        """ Initialize the class """
        self.ai_extractor = AIContentExtractor(use_openai=bool(openai_api_key), openai_api_key=openai_api_key)
        self.use_ai = use_ai

        # Scraper for simple sites
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
    
    async def scrapeWithRequests(self, base_url: str, categories: List[str], max_products: int) -> List[Product]:
        """
            Scrape product data from furniture website URL based on given categories using requests for simple sites.

            Args:
                base_url (str): The URL of the website to scrape
                categories (List[str], optional): A list of category names or URLs to target for scraping
                                                If None, all available categories will be scraped
                max_products (int, optional): The maximum number of products to scrape per category

            Returns:
                List[Product]: A lists of Product objects scraped from each category
        """
        results = []
        
        try:
            # Find category URLs from the main page based on selected categories
            category_urls = self._discoverCategoryUrlsRequests(base_url, categories)

            # Return of the category doesn't match
            if not category_urls:
                logger.info("No category URLs found. No results to scrape.")
                return []
            
            category_products = []

            # For each category, discover product URLs and scrape them
            for cat, urls in category_urls.items():
                if not urls:
                    logger.warning(f"No URLs found for category '{cat}', skipping.")
                    continue

                logger.info(f"Processing category '{cat}' with {len(urls)} URL(s).")
                
                for url in urls:
                    try:
                        # Get product URLs from this category page
                        product_urls = self._discoverProductUrlsRequests(url)
                        
                        if not product_urls:
                            logger.warning(f"No product found at {url} for category {cat}. Skipping URL.")
                            continue

                        logger.info(f"Found {len(product_urls)} product URLs at {url} for category: {cat}")
                
                        # Scrape each product
                        for _, product_url in enumerate(product_urls):
                            try:
                                response = self.session.get(product_url, timeout=10)
                                
                                if self.use_ai:
                                    product = self.ai_extractor.extractProductInfo(response.text, product_url)

                                    if product:
                                        product.furnitureType = str(cat).title()
                                        results.append(asdict(product))

                                        logger.info(f"Scraped product: {product.productName}")
                                
                                time.sleep(2)  # Rate limiting
                        
                            except Exception as e:
                                logger.error(f"Error processing product {product_url}: {e}")
                                continue
                    except Exception as e:
                        logger.error(f"Error processing category URL {url}: {e}")
                        continue
                    
        except Exception as e:
            logger.error(f"Error scraping {base_url}: {e}")
        
        return results

    def _discoverCategoryUrlsRequests(self, base_url: str, categories: List[str] = None) -> dict:
        """
        Discover category URLs from the main page and map them to the selected categories.
        Each category can have multiple URLs if multiple links match.

        Args:
            base_url (str): The base URL of the website.
            categories (List[str]): List of categories to find. If None, all known categories are returned.

        Returns:
            Dict[str, List[str]]: Mapping from category name to list of URLs.
        """
        category_urls = {}
        seen_links = set()
        base_domain = urlparse(base_url).netloc.lower()

        try:
            response = self.session.get(base_url, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')

            found_links = []
            for selector in CATEGORY_SELECTORS:
                for link in soup.select(selector):
                    href = link.get('href')
                    text = link.get_text().strip().lower()
                    if href:
                        full_url = urljoin(base_url, href)
                        if full_url and full_url not in seen_links:
                            seen_links.add(full_url)
                            found_links.append((full_url, text))

            logger.info(f"Found {len(found_links)} links:")

            # Determine which categories to match
            if categories:
                keywords_per_category = {}
                for cat in categories:
                    cat_lower = cat.lower()
                    keywords_per_category[cat_lower] = CATEGORY_SYNONYMS.get(cat_lower, [cat_lower])
            else:
                keywords_per_category = CATEGORY_SYNONYMS

            # Initialize dict with empty lists
            for cat in keywords_per_category.keys():
                category_urls[cat] = []

            # Match URLs to categories (substring matching)
            for url, text in found_links:
                if base_domain not in url.lower():
                    continue
                for cat, keywords in keywords_per_category.items():
                    for keyword in keywords:
                        if keyword.lower() in url.lower() or keyword.lower() in text:
                            if url not in category_urls[cat]:
                                category_urls[cat].append(url)
                            break  # Stop checking other keywords for this category

            # Fallback: if a category has no matching URL, include base URL
            for cat in list(category_urls.keys()):
                if not category_urls[cat]:
                    del category_urls[cat]

            logger.info(f"Discovered category URLs: {category_urls}")
            return category_urls

        except Exception as e:
            logger.error(f"Error discovering categories from {base_url}: {e}")
            fallback = {cat.lower(): [base_url] for cat in categories} if categories else {k: [base_url] for k in CATEGORY_SYNONYMS}
            return fallback

    def _isProductUrl(self, url: str) -> bool:
        """Check if URL slug looks like a product detail page."""
        parsed = urlparse(url)
        path_parts = [p for p in parsed.path.strip("/").split("/") if p]

        if not path_parts:
            return False

        last_part = path_parts[-1].lower()

        # Filter out URLs that end in common category words
        for words in COMMON_ENDINGS:
            if words in last_part.lower():
                return False

        # Ensure last part has some length and is not just numeric (optional rule)
        if len(last_part) < 3:
            return False
        if last_part.isdigit():
            return False

        return True

    def _discoverProductUrlsRequests(self, base_url: str) -> List[str]:
        """
            Discover product URLs from the main page using requests.

            Args:
                base_url (str): The base URL of the website to scan for product links.

            Returns:
                List[str]: A List of product URL found.
        """
        product_urls = []
        seen_links = set()
        
        try:
            response = self.session.get(base_url, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')

            # Get base domain (for filtering)
            base_domain = urlparse(base_url).netloc

            for selector in PRODUCT_SELECTORS:
                links = soup.select(selector)
                for link in links:
                    href = link.get('href')
                    text = link.get_text().strip().lower()

                    if not href:
                        continue

                    # Build absolute URL
                    full_url = urljoin(base_url, href)
                    parsed_full = urlparse(full_url)

                    # Only allow same-domain links
                    if parsed_full.netloc != "" and base_domain not in parsed_full.netloc:
                        continue
                        
                    # Run product URL check
                    if full_url not in seen_links and self._isProductUrl(full_url):
                        seen_links.add(full_url)
                        product_urls.append(full_url)
                        logger.info(f"Product link found: {text} -> {full_url}")
            
            logger.info(f"Discovered {len(product_urls)} product URLs")
            return product_urls
            
        except Exception as e:
            logger.error(f"Error discovering categories from {base_url}: {e}")
            return {'all': base_url}  # Fallback to base URL
        
    def extractProductInfo(self, soup: BeautifulSoup, text: str, url: str) -> ProductScraped:
        """
            Extract product information using heuristic patterns and HTML structure patterns.

            Args:
                soup (Beautiful): Parsed HTML content of the page.
                text (str): The visible text extracted from the HTML page, used for pattern matching.
                url (str): The URL of the page being processed, used for context or fallback.
            
            Returns:
                Optional[Dict]: A dictionary containing product attributes, or None if no data found.
        """
        result: ProductScraped = {
            'productName': '',
            'description': '',
            'productUrl': url,
            'designerName': '',
            'imageUrls': [],
            'furnitureType': ''
        }

        product_name = ""
        
        # Extract name (usually in h1, h2, or title-like classes)
        for selector in NAME_SELECTORS:
            element = soup.select_one(selector)
            if element and element.get_text().strip():
                product_name = element.get_text().strip()
                result['productName'] = element.get_text().strip().title()
                break
        
        # Extract description
        for selector in DESC_SELECTORS:
            element = soup.select_one(selector)
            if element and element.get_text().strip():
                result['description'] = element.get_text().strip()
                break
        
        text_lower = text.lower()

        # Extract designer
        for selector in DESIGNER_SELECTORS:
            element = soup.select_one(selector)
            if element and element.get_text().strip():
                result['designerName'] = element.get_text().strip()
                break

        if not result['designerName']:
            match = re.search(r"design(?:ed)? by ([\w\s]+)", text_lower, re.IGNORECASE)
            if match:
                result['designerName'] = match.group(1).title()
        
        # Extract images
        image_urls = []
        img_elements = soup.find_all('img')
        for img in img_elements:
            src = img.get('src') or img.get('data-src') or img.get('data-lazy')

            product_name = result['productName'].split(" ")[0]
            if src and isValidImageSrc(src, product_name):
                full_url = urljoin(url, src)
                image_urls.append(full_url)
        
        result['imageUrls'] = image_urls
        return result if result['productName'] else None