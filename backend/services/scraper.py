# Import necessary libraries
import os
import json
import logging
from typing import List

# Import local modules
from backend.config.product import Product
from backend.services.processor import UniversalFurnitureScraper
from backend.utils.helpers import isValidUrl, getWebsiteName, exportToExcel, logSummary

# Import constants
from backend.config.constant import SCRAPED_DIR

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler()]
)

# Create a logger for this module
logger = logging.getLogger(__name__)

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
    
async def processSingleInput(data: str, furniture_categories: list[str]) -> str:
    """
        Process a single input which can be a brand name or a URL.
        
        Args:
            data (str): The input data, which can be a brand name or a URL.
            furniture_categories (list[str]): Contains the list of furniture categories.
            
        Returns:
            str: Processed result or error message.
    """
    logger.info(f"Processing single input: {data}")

    # Initialize vairables
    result = ""
    site_url = ""
    website_name = ""
    brand_input = data.strip()

    # Check if the input is a valid URL
    if isValidUrl(brand_input):
        logger.info(f"Input is a valid URL: {brand_input}")

        site_url = brand_input
        website_name = getWebsiteName(site_url)
        
        result = f"Brand Name: {website_name.capitalize()}\n"
        result += f"Official Website: {site_url}\n"

    # If no URL found, return error
    if not site_url:
        logger.error(f"No official website found for {brand_input}.")
        return f"Error: No official website found for {brand_input}."
    
    # Process the URL to extract category information
    try:
        logger.info(f"Extracting product information for {site_url}")

        # Initialize pipeline
        pipeline = FurnitureScrapingPipeline() # without AI
        # # openai_key = "openai-api-key"
        # # pipeline = FurnitureScrapingPipeline(openai_api_key=openai_key)  # with AI

        # Parse categories if it's a string
        if furniture_categories:
            try:
                furniture_categories = json.loads(furniture_categories)
            except json.JSONDecodeError:
                # fallback: treat as single category string
                furniture_categories = [furniture_categories]
        else:
            furniture_categories = []

        res = await pipeline.scrapeAnyWebsite(
            site_url, 
            categories=furniture_categories
        )
        print(res)
        if res:
            logger.info(f"Category information extracted for {site_url}")
            result += "\n" + logSummary(res)

            logger.info(f"Converting the scraped data to Excel file: 'scraped_file/{website_name}.xlsx'")
            exportToExcel(res, os.path.join(SCRAPED_DIR, f"{website_name}.xlsx"))
            logger.info(f"Stored data to Excel file: 'scraped_file/{website_name}.xlsx'")

    except Exception as e:
        logger.error(f"Error processing URL {site_url}: {e}")
        return f"Error processing URL: {e}"

    # Return brand info
    return result