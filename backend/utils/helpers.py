# Import necessary libraries
import pandas as pd
from typing import List, Dict
from googlesearch import search
from urllib.parse import urlparse
from logs.loggers import loggerSetup, logger
from config.constant import ALLOWED_EXTENSIONS

# Set up logs
loggerSetup()

def allowedFile(filename: str) -> bool:
    """
        Check if the uploaded file has an allowed extention.

        Args:
            filename (str): The name of the uploaded file

        Returns:
            bool: True if the file extension is allowed, False otherwise
    """
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def isValidUrl(url: str) -> bool:
    """
        Check if the given URL is valid.
        
        Args:
            url (str): The URL to check.
            
        Returns:
            bool: True if the URL is valid, False otherwise.
    """
    if not url:
        logger.error("Empty URL provided for validation.")
        return False

    parsed_url = urlparse(url)
    return bool(parsed_url.scheme and parsed_url.netloc)

def searchOfficialWebsite(company_name: str) -> str:
    """
        Search for the official website of a company using Google search.
        
        Args:
            company_name (str): The name of the company to search for.
            
        Returns:
            str: The URL of the official website if found, otherwise an empty string.
    """
    query = f"{company_name} official site"

    try:
        # Use the search function from googlesearch to find the official website
        result_iterator = search(query, stop=1, pause=1)
        results = list(result_iterator)

        if results:
            return results[0]

        logger.warning(f"No official website found for {company_name}.")
        return ""
    except Exception as e:
        logger.error(f"Error searching for {company_name}: {e}")
        return ""
    
def getWebsiteName(url: str) -> str:
    """
        Extract the website name from a given URL.

        Args:
            url (str): The URL string.

        Returns:
            str: Website name.
    """
    netloc = urlparse(url).netloc
    if netloc.startswith("www."):
        netloc = netloc[4:]
    
    return netloc.split('.')[0]

def discoverCategoryUrls(base_url: str, categories: List[str]) -> Dict[str, str]:
    """
        Generate a mapping of category names to their corresponding URLs based on base URL.

        Args:
            base_url (str): The base URL of the website.
            categories (List[str]): A list of category names.

        Returns:
            Dict[str, str]: A dictionary mapping each category to the base URL.
    """
    # This could be enhanced with AI to automatically find category pages
    # For now, return base URL for all categories
    return {category: base_url for category in categories}
    
def exportToExcel(results: List, filename: str):
    """
        Export the scraped product data to Excel file.

        Args:
            results (List): A list of data containing product details
            filename: The desired name (with or without path) for the output Excel file.
            
        Returns:
            None
    """
    # Convert results to data frame
    df = pd.DataFrame(results)

    # Convert DataFrame to Excel
    df.to_excel(f"{filename}.xlsx", index=False, engine="openpyxl")
    
def logSummary(results: List) -> str:
    """
        Print a summary of scraping results.
    
        Args:
            results (List): A list of scraped product data

        Returns:
            str: Summary of scraping results
    """
    logger.info("\n" + "="*60)
    logger.info("FURNITURE SCRAPING SUMMARY")
    logger.info("="*60)

    summary = ""
        
    df = pd.DataFrame(results)
    categories = df['category'].unique()
        
    for cat in categories:            
        count = len(df[df['category'] == cat])
        summary += f"\n  {cat}: {count} products"
        logger.info(f"  {cat}: {count} products")
        
    summary += f"\nTOTAL: {len(results)} products"
    logger.info(f"TOTAL: {len(results)} products")
    logger.info("="*60)

    return summary