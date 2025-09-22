# Import necessary libraries
import requests
import logging
from backend.config.product import Product
from typing import List

# Import local module
from backend.config.web_analyzer import WebsiteAnalyzer
from backend.services.static_scrape import StaticScraper
from backend.services.dynamic_scrape import DynamicScraper
from backend.config.content_extractor import AIContentExtractor

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
        # define classes
        self.analyzer = WebsiteAnalyzer()
        self.staticScraper = StaticScraper()
        self.dynamicScraper = DynamicScraper()
        self.ai_extractor = AIContentExtractor(use_openai=bool(openai_api_key), openai_api_key=openai_api_key)

        # initialize constants
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
            return await self.dynamicScraper.scrapeWithPlaywright(base_url, categories, max_products)
        else:
            logger.info(f"Scrapping using Requests")
            return await self.staticScraper.scrapeWithRequests(base_url, categories, max_products)