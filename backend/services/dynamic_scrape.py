# Import necessary libraries
import re
import asyncio
import requests
import logging
from urllib.parse import urlparse
from bs4 import BeautifulSoup
from dataclasses import asdict
from urllib.parse import urljoin
from typing import List, Dict, Optional

# Import local module
from backend.config.product import Product
from backend.config.config import ProductScraped
from backend.utils.helpers import isValidImageSrc
from backend.utils.helpers import isProductImage
from backend.config.content_extractor import AIContentExtractor
from backend.config.playwright_scraper import PlaywrightScraper

# Import constant
from backend.config.constant import (
    CATEGORY_SELECTORS,
    CATEGORY_SYNONYMS,
    PRODUCT_SELECTORS,
    PRODUCT_KEYWORDS,
    NAME_SELECTORS,
    DESC_SELECTORS,
    DESIGNER_SELECTORS,
    FURNITURE_KEYWORDS,
    IMAGE_SELECTORS
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

class DynamicScraper:
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
    
    async def scrapeWithPlaywright(self, base_url: str, categories: List[str], max_products: int = None) -> Dict[str, List[Product]]:
        """
            Scrape product data from furniture website URL based on given categories using Playwright for JavaScript-heavy sites.

            Args:
                base_url (str): The URL of the website to scrape
                categories (List[str], optional): A list of category names or URLs to target for scraping
                                                If None, all available categories will be scraped
                max_products (int, optional): The maximum number of products to scrape per category

            Returns:
                List[Product]: A lists of Product objects scraped from each category
        """
        self.playwright_scraper = PlaywrightScraper()
        await self.playwright_scraper.setup()
        
        try:
            results = []
            
            # Discover category pages or use base URL
            if categories:
                category_urls = await self._discoverCategoryUrlsPlaywright(base_url, categories)
            else:
                category_urls = [base_url]
            
            for category_url in category_urls:
                logger.info(f"Scraping category: {category_url}")
                
                category = ""

                for cat in categories:
                    if cat.lower() in category_url.lower():
                        category = cat

                # Discover product URLs
                product_urls = await self.playwright_scraper.discoverProducts(category_url, category)
                
                # Limit products per category
                if len(category_urls) > 1:
                    product_urls = product_urls[:max_products // len(category_urls)]
                else:
                    product_urls = product_urls[:max_products]
                
                products = []
                for product_url in product_urls:
                    try:
                        # Get page content with playwright
                        html_content = await self.playwright_scraper.scrapePage(product_url)
                        
                        if html_content and self.use_ai:
                            # Extract product info using AI
                            product = self._extractProductInfoPlaywright(html_content, product_url, category)
                            if product:
                                product_dict = asdict(product)
                                products.append(product_dict)
                                logger.info(f"Successfully scraped product: {product.name}")
                        
                        # Rate limiting
                        await asyncio.sleep(1)
                        
                    except Exception as e:
                        logger.error(f"Error processing product {product_url}: {e}")
                        continue
                
                results.append(products)
                logger.info(f"Scraped {len(products)} products from {category}")
            
            return results
            
        finally:
            await self.playwright_scraper.cleanup()

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
            for url, text in found_links:
                print(f"URL: {url}, text: '{text}'")

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


    def _discoverProductUrlsRequests(self, base_url: str) -> List[str]:
        """
            Discover product URLs from the main page using requests.

            Args:
                base_url (str): The base URL of the website to scan for product links.

            Returns:
                List[str]: A List of product URL found.
        """
        product_urls = []
        
        try:
            response = self.session.get(base_url, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')

            for selector in PRODUCT_SELECTORS:
                links = soup.select(selector)
                for link in links:
                    href = link.get('href')
                    text = link.get_text().strip().lower()
                    if href:
                        full_url = urljoin(base_url, href)
                        
                        if full_url and full_url not in seen_links and any(kw in full_url.lower() for kw in PRODUCT_KEYWORDS):
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
    
    async def _discoverCategoryUrlsPlaywright(self, base_url: str, categories: List[str] = None) -> List[str]:
        """
            Discover category URLs from the main page using playwright.

            Args:
                base_url (str): The base URL of the website to scan for product links.
                categories (List[str], optional): A list of category names to search for.

            Returns:
                List[str]: A List of product URL found.
        """
        category_urls = []
        page = await self.playwright_scraper.context.new_page()
        
        try:
            await page.goto(base_url, wait_until='networkidle')
            await page.wait_for_timeout(3000)  # Wait for dynamic content
            
            # Get all links after JavaScript execution
            links = await page.evaluate('''
                () => {
                    const allLinks = [];
                    const linkElements = document.querySelectorAll('a[href]');
                    
                    linkElements.forEach(link => {
                        const href = link.href;
                        const text = link.textContent.trim().toLowerCase();
                        const classList = Array.from(link.classList).join(' ').toLowerCase();
                        
                        if (href && text) {
                            allLinks.push({
                                url: href,
                                text: text,
                                classes: classList
                            });
                        }
                    });
                    
                    return allLinks;
                }
            ''')
            
            logger.info(f"Found {len(links)} links via Playwright from {base_url}")
            
            if categories:
                # Filter by requested categories
                for link_data in links:
                    url, text = link_data['url'], link_data['text']
                    for category in categories:
                        if (category.lower() in text or 
                            category.lower() in url.lower() or
                            any(keyword in text for keyword in FURNITURE_KEYWORDS if keyword in category.lower())):
                            category_urls.append(url)
                            logger.info(f"Category found: {category} -> {url}")
                            break
            else:
                # Auto-detect furniture categories
                for link_data in links:
                    url, text = link_data['url'], link_data['text']
                    for keyword in FURNITURE_KEYWORDS:
                        if (keyword in text or keyword in url.lower()):
                            category_name = keyword
                            if text and len(text) < 50:
                                category_name = text.replace(' ', '_')
                            category_urls.append(url)
                            logger.info(f"Auto-detected category: {category_name} -> {url}")
                            break
            
            # Fallback: if no categories found, try navigation menu
            if not category_urls:
                nav_links = await page.evaluate('''
                    () => {
                        const navSelectors = ['nav a', '.navigation a', '.menu a', '.navbar a', '.header a'];
                        const navLinks = [];
                        
                        navSelectors.forEach(selector => {
                            const elements = document.querySelectorAll(selector);
                            elements.forEach(el => {
                                if (el.href && el.textContent.trim()) {
                                    navLinks.push({
                                        url: el.href,
                                        text: el.textContent.trim().toLowerCase()
                                    });
                                }
                            });
                        });
                        
                        return navLinks;
                    }
                ''')
                
                for link_data in nav_links:
                    url, text = link_data['url'], link_data['text']
                    if any(keyword in text or keyword in url.lower() for keyword in ['product', 'collection', 'catalog']):
                        category_urls.append(url)
            
            logger.info(f"Discovered {len(category_urls)} category URLs: {list(category_urls.keys())}")
            return category_urls if category_urls else [base_url]
            
        except Exception as e:
            logger.error(f"Error discovering categories from {base_url}: {e}")
            return [base_url]
        finally:
            await page.close()

    async def _extractProductInfoPlaywright(self, html_content: str, product_url: str, category: str) -> Optional[Product]:
        """
            Extract product information from Playwright-rendered content.

            Args:
                html_content (str): The raw HTML content of the product page.
                product_url (str): The URL of the product page.
                category (str): A category name to search for.

            Returns:
                Optional[Product]: A Product object containing extracted information, or None of extraction fails or content not found.
        """
        
        # If AI is available, use it first
        if self.use_ai:
            try:
                product = self.ai_extractor.extractProductInfo(html_content, product_url)
                if product:
                    product.furnitureType = category
                    return product
            except Exception as e:
                logger.debug(f"AI extraction failed, falling back to heuristics: {e}")
        
        # Fallback to enhanced heuristic extraction for dynamic content
        return await self._extractWithPlaywrightHeuristics(html_content, product_url, category)
    
    async def _extractWithPlaywrightHeuristics(self, html_content: str, product_url: str, category: str) -> Optional[Product]:
        """Enhanced heuristic extraction for Playwright-rendered content"""
        """
            Extract product information using heuristic patterns for Playwright-rendered conten.

            Args:
                html_content (str): The raw HTML content of the product page.
                product_url (str): The URL of the product page.
                category (str): A category name to search for.
            
            Returns:
                Optional[Dict]: A dictionary containing product attributes, or None if no data found.
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
        
        result: ProductScraped = {
            'productName': '',
            'description': '',
            'productUrl': product_url,
            'designerName': '',
            'imageUrls': [],
            'furnitureType': category
        }
        
        # Extract name
        for selector in NAME_SELECTORS:
            element = soup.select_one(selector)
            if element and element.get_text().strip():
                result['name'] = element.get_text().strip()
                break
        
        # Extract description
        for selector in DESC_SELECTORS:
            element = soup.select_one(selector)
            if element and element.get_text().strip():
                desc_text = element.get_text().strip()
                # Skip if description is too short or looks like a title
                if len(desc_text) > 20 and desc_text.lower() != result['name'].lower():
                    result['description'] = desc_text
                    break
        
        # Extract designer
        for selector in DESIGNER_SELECTORS:
            element = soup.select_one(selector)
            if element and element.get_text().strip():
                designer_text = element.get_text().strip()
                # Clean up common prefixes
                designer_text = re.sub(r'^(by|design by|designer:?|brand:?)\s*', '', designer_text, flags=re.IGNORECASE)
                result['designer'] = designer_text
                break
        
        found_images = set()
        for selector in IMAGE_SELECTORS:
            img_elements = soup.select(selector)
            for img in img_elements:
                # Try multiple attributes for image source
                src = (img.get('src') or img.get('data-src') or 
                      img.get('data-lazy') or img.get('data-original'))
                
                if src:
                    # Convert relative URLs to absolute
                    full_url = urljoin(product_url, src)
                    
                    # Filter out non-product images
                    if isProductImage(src, img.get('alt', '')):
                        found_images.add(full_url)
        
        result['image_urls'] = list(found_images)
        
        # Return product if we have at least a name
        if result['name']:
            return Product(**result)
        
        return None