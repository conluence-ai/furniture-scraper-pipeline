# Import necessary libraries
import time
import asyncio
import requests
from bs4 import BeautifulSoup
from typing import Dict, List
from urllib.parse import urljoin
from config.product import Product
from logs.loggers import loggerSetup, logger
from utils.helpers import discoverCategoryUrls
from config.web_analyzer import WebsiteAnalyzer
from config.content_extractor import AIContentExtractor
from config.playwright_scraper import PlaywrightScraper
from config.constant import LINK_SELECTORS, CATEGORY_SELECTORS, FURNITURE_KEYWORDS

# Set up logs
loggerSetup()

# Global variables
seen_links = set()

class UniversalFurnitureScraper:
    """Universal scraper that can handle any furniture website"""
    
    def __init__(self, use_ai: bool = True, openai_api_key: str = None):
        """
            Initialize the class

            Args:
                use_ai (bool, optional): Whether to enable AI-related functionality. Defaults to True.
                openai_api_key (str, optional): The API key used to authenticate with OpenAI service.

            Returns:
                None
        """
        self.analyzer = WebsiteAnalyzer()
        self.ai_extractor = AIContentExtractor(use_openai=bool(openai_api_key), openai_api_key=openai_api_key)
        self.playwright_scraper = None
        self.use_ai = use_ai
        
        # Scraper for simple sites
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
    
    async def scrapeWebsite(self, base_url: str, categories: List[str] = None, max_products: int = None) -> List[Product]:
        """
            Scrape product data from furniture website URL based on given categories.

            Args:
                base_url (str): The URL of the website to scrape
                categories (List[str], optional): A list of category names or URLs to target for scraping
                                                If None, all available categories will be scraped
                max_products (int, optional): The maximum number of products to scrape per category

            Returns:
                List[Product]: A lists of Product objects scraped from each category
        """
        logger.info(f"Starting universal scrape of {base_url}")
        
        # Analyze website
        analysis = self.analyzer.analyzeWebsite(base_url)
        
        # Choose scraping strategy based on wesite complexity
        if analysis['requires_js']:
            logger.info(f"Scrapping using Playwright")
            return None
            # return await self._scrapeWithPlaywright(base_url, categories, max_products)
        else:
            logger.info(f"Scrapping using Requests")
            return await self._scrapeWithRequests(base_url, categories, max_products)
    
    async def _scrapeWithPlaywright(self, base_url: str, categories: List[str], max_products: int = None) -> Dict[str, List[Product]]:
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
                category_urls = await discoverCategoryUrls(base_url, categories)
            else:
                category_urls = {'all': base_url}
            
            for category, category_url in category_urls.items():
                logger.info(f"Scraping category: {category}")
                
                # Discover product URLs
                product_urls = await self.playwright_scraper.discoverProducts(category_url, category)
                
                # Limit products per category
                product_urls = product_urls[:max_products // len(category_urls)]
                
                products = []
                for product_url in product_urls:
                    try:
                        # Get page content
                        html_content = await self.playwright_scraper.scrapePage(product_url)
                        
                        if html_content and self.use_ai:
                            # Extract product info using AI
                            product = self.ai_extractor.extractProductInfo(html_content, product_url)
                            if product:
                                product.category = category
                                products.append(product)
                        
                        # Rate limiting
                        await asyncio.sleep(1)
                        
                    except Exception as e:
                        logger.error(f"Error processing product {product_url}: {e}")
                        continue
                
                results = products
                logger.info(f"Scraped {len(products)} products from {category}")
            
            return results
            
        finally:
            await self.playwright_scraper.cleanup()
    
    async def _scrapeWithRequests(self, base_url: str, categories: List[str], max_products: int) -> List[Product]:
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
            # Find category URLs from the main page
            category_urls = self._discoverCategoryUrlsRequests(base_url, categories)


            # For each category, discover product URLs and scrape them
            for category_name, category_url in category_urls.items():
                logger.info(f"Processing category: {category_name} - {category_url}")
                
                category_products = []
                
                # Get product URLs from this category page
                product_urls = self._discoverProductUrlsRequests(category_url)
                logger.info(f"Found {len(product_urls)} product URLs in category: {category_name}")
                
                # Scrape each product
                for product_url in product_urls:
                    try:
                        response = self.session.get(product_url, timeout=10)
                        
                        if self.use_ai:
                            product = self.ai_extractor.extractProductInfo(response.text, product_url)
                            if product:
                                product.category = category_name
                                category_products.append(product)
                                logger.info(f"Successfully scraped product: {product.productName}")
                        
                        time.sleep(1)  # Rate limiting
                        
                    except Exception as e:
                        logger.error(f"Error processing product {product_url}: {e}")
                        continue
                
                results.append(category_products)
                logger.info(f"Completed category {category_name}: {len(category_products)} products")
            
        except Exception as e:
            logger.error(f"Error scraping {base_url}: {e}")
        
        return results

    def _discoverCategoryUrlsRequests(self, base_url: str, categories: List[str] = None) -> Dict[str, str]:
        """
            Discover category URLs from the main page using requests.

            Args:
                base_url (str): The base URL of the website to scan for category links.
                categories (List[str]): A list of category names to look for in the page.
                                    If None, all links may be considered.

            Returns:
                Dict[str, str]: A dictionary mapping each found category to its corresponding URL.
        """
        category_urls = {}
        
        try:
            response = self.session.get(base_url, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            found_links = []

            for selector in CATEGORY_SELECTORS:
                links = soup.select(selector)
                for link in links:
                    href = link.get('href')
                    text = link.get_text().strip().lower()
                    if href:
                        full_url = urljoin(base_url, href)
                        if full_url and full_url not in seen_links:
                            seen_links.add(full_url)
                            found_links.append((full_url, text))
                            logger.info(f"Category link found: {text} -> {full_url}")
            
            if categories:
                # Filter by requested categories
                for url, text in found_links:
                    for category in categories:
                        if text in category.lower() or category.lower() in url.lower():
                            category_urls[category] = url
                            break
            else:
                # Auto-detect furniture categories
                for url, text in found_links:
                    for keyword in FURNITURE_KEYWORDS:
                        if keyword in text or keyword in url.lower():
                            # Use the keyword as category name
                            category_name = keyword
                            if text and len(text) < 50:  # Use link text if reasonable
                                category_name = text.replace(' ', '_')
                            category_urls[category_name] = url
                            break
            
            # If no specific categories found, use the main product links
            if not category_urls:
                for url, text in found_links:
                    if any(word in url.lower() for word in ['product', 'collection', 'catalog']):
                        category_urls[text or 'products'] = url
            
            logger.info(f"Discovered {len(category_urls)} category URLs: {list(category_urls.keys())}")
            return category_urls
            
        except Exception as e:
            logger.error(f"Error discovering categories from {base_url}: {e}")
            return {'all': base_url}  # Fallback to base URL
        

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

            for selector in CATEGORY_SELECTORS:
                links = soup.select(selector)
                for link in links:
                    href = link.get('href')
                    text = link.get_text().strip().lower()
                    if href:
                        full_url = urljoin(base_url, href)
                        if full_url and full_url not in seen_links:
                            seen_links.add(full_url)
                            product_urls.append(full_url)
                            logger.info(f"Product link found: {text} -> {full_url}")
            
            logger.info(f"Discovered {len(product_urls)} product URLs")
            return product_urls
            
        except Exception as e:
            logger.error(f"Error discovering categories from {base_url}: {e}")
            return {'all': base_url}  # Fallback to base URL