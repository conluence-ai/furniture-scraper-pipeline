# Import necessary libraries
from typing import List
from config.product import Product
from services.processor import UniversalFurnitureScraper

class FurnitureScrapingPipeline:
    """
        Enhanced pipeline for universal furniture scraping
    """
    
    def __init__(self, openai_api_key: str = None):
        """
            Initialize the class

            Args:
                openai_api_key (str, optional): The API key used to authenticate with OpenAI service.

            Returns:
                None
        """
        self.universal_scraper = UniversalFurnitureScraper(openai_api_key=openai_api_key)
    
    async def scrapeAnyWebsite(self, website_url: str, categories: List[str] = None, max_products: int = None) -> List[Product]:
        """
            Scrape product data from furniture website URL based on given categories.

            Args:
                website_url (str): The URL of the website to scrape
                categories (List[str], optional): A list of category names or URLs to target for scraping
                                                If None, all available categories will be scraped
                max_products (int, optional): The maximum number of products to scrape per category

            Returns:
                List[Product]: A lists of Product objects scraped from each category
        """
        return await self.universal_scraper.scrapeWebsite(website_url, categories, max_products)
    