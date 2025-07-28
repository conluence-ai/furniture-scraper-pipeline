# Import necessary libraries
import time
import asyncio
import requests
from bs4 import BeautifulSoup
from typing import Dict, List
from urllib.parse import urljoin
from config.product import Product
from config.constant import LINK_SELECTORS
from logs.loggers import loggerSetup, logger
from utils.helpers import discoverCategoryUrls
from config.web_analyzer import WebsiteAnalyzer
from config.content_extractor import AIContentExtractor
from config.playwright_scraper import PlaywrightScraper

# Set up logs
loggerSetup()

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
            return await self._scrapeWithPlaywright(base_url, categories, max_products)
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
            response = self.session.get(base_url, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find product links
            product_links = []
            
            for selector in LINK_SELECTORS:
                links = soup.select(selector)
                for link in links:
                    href = link.get('href')
                    if href:
                        full_url = urljoin(base_url, href)
                        if full_url not in product_links:
                            product_links.append(full_url)
            
            # Limit products
            product_links = product_links[:max_products]
            
            products = []
            for product_url in product_links:
                try:
                    response = self.session.get(product_url, timeout=10)
                    
                    if self.use_ai:
                        product = self.ai_extractor.extractProductInfo(response.text, product_url)
                        if product:
                            products.append(product)
                    
                    time.sleep(1)  # Rate limiting
                    
                except Exception as e:
                    logger.error(f"Error processing product {product_url}: {e}")
                    continue
            
            results = products
            
        except Exception as e:
            logger.error(f"Error scraping {base_url}: {e}")
        
        return results
    