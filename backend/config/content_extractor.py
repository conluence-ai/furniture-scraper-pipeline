# Import necessary libraries
import re
import json
import openai
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from typing import Dict, Optional
from transformers import pipeline
from backend.config.product import Product
from backend.utils.helpers import isValidImageSrc
import logging

from backend.config.config import ProductScraped
from backend.config.constant import NAME_SELECTORS, DESC_SELECTORS, DESIGNER_SELECTORS

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler()]
)

# Create a logger for this module
logger = logging.getLogger(__name__)

class AIContentExtractor:
    """Uses AI to extract structured data from web pages"""
    
    def __init__(self, use_openai: bool = False, openai_api_key: str = None):
        """
            Initialize the class

            Args:
                use_openai (bool, optional): Flag indicating whether to use OpenAI analysis. Defaults to False.
                openai_api_key (str, optional): The API key used to authenticate with OpenAI services.

            Returns:
                None
        """
        self.use_openai = use_openai
        if use_openai and openai_api_key:
            openai.api_key = openai_api_key
        
        # Initialize local NLP model for fallback
        try:
            self.nlp_pipeline = pipeline("text-classification", model="distilbert-base-uncased")
        except:
            self.nlp_pipeline = None
    
    def extractProductInfo(self, html_content: str, url: str) -> ProductScraped:
        """
            Extract product information from given HTML using AI.

            Args:
                html_content (str): The raw HTML content of the product page.
                url (str): The URL of the product page.

            Returns:
                Optional[Product]: A Product object containing extracted information, or None of extraction fails or content not found.
        """
        if self.use_openai:
            return self._extractWithOpenAI(html_content, url)
        else:
            return self._extractWithLocalAI(html_content, url)
    
    def _extractWithOpenAI(self, html_content: str, url: str) -> Optional[Product]:
        """
            Extract product information from given HTML using OpenAI GPT.

            Args:
                html_content (str): The raw HTML content of the product page.
                url (str): The URL of the product page.

            Returns:
                Optional[Product]: A Product object containing extracted information, or None of extraction fails or content not found.
        """
        try:
            prompt = f"""
            Extract furniture product information from this HTML content:
            
            {html_content[:4000]}  # Limit content length
            
            Please extract and return a JSON object with these fields:
            - name: Product name
            - description: Product description
            - designer: Designer name
            - furnitureType: Product category (sofa, chair, table, etc.)
            - imageUrls: Lists of image URLs of the product
            
            Return only valid JSON.
            """
            
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1000
            )
            
            result = json.loads(response.choices[0].message.content)
            
            return Product(
                productName=result.get('name', ''),
                description=result.get('description', ''),
                productUrl=url,
                designerName=result.get('designer', ''),
                imageUrls=result.get('imageUrls', ''),
                furnitureType=result.get('furnitureType', ''),
            )
            
        except Exception as e:
            logger.error(f"OpenAI extraction failed: {e}")
            return None
    
    def _extractWithLocalAI(self, html_content: str, url: str) -> extractProductInfo:
        """
            Extract product information from given HTML using local heuristics.

            Args:
                html_content (str): The raw HTML content of the product page.
                url (str): The URL of the product page.

            Returns:
                Optional[Product]: A Product object containing extracted information, or None of extraction fails or content not found.
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
        
        text = soup.get_text()
        
        # Use heuristics to extract information
        product_info = self._extractWithHeuristics(soup, text, url)
        
        if product_info:
            return Product(**product_info)
        
        return None
    
    def _extractWithHeuristics(self, soup: BeautifulSoup, text: str, url: str) -> ProductScraped:
        """
            Extract product information using heuristic patterns and HTML structure patterns.

            Args:
                soup (Beautiful): Parsed HTML content of the page.
                text (str): The visible text extracted from the HTML page, used for pattern matching.
                url (str): The URL of the page being processed, used for context or fallback.
            
            Returns:
                ProductScraped: A dictionary containing product attributes, or None if no data found.
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