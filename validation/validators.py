import requests
import pandas as pd
from logs.logs import validation_logger_setup, logger
from utils.helpers import safeParseImageUrls

validation_logger_setup()

def isValidUrl(url: str) -> bool:
    """
        Check if the URL is valid and reachable.
  
        Args: url (str): The URL to check.
      
        Returns: True if the URL is valid and reachable, False otherwise.
    """

    try:
        # Send a HEAD request to check if the URL is reachable
        response = requests.head(url, allow_redirects=True, timeout=5)
        return response.status_code == 200
    except:
        return False
    
def isValidImageUrl(url: str) -> bool:
    """
        Check if the URL is a valid image URL.
        
        Args: url (str): The URL to check.
        
        Returns: True if the URL is a valid image URL, False otherwise.
    """

    if not url:
        return False

    blacklist = ["logo", "svg", "icon", "placeholder", "favicon"]

    # Check if the URL ends with a common image file extension
    if any(keyword in url.lower() for keyword in blacklist):
        return False

    return isValidUrl(url)

def validateRow(raw_row: dict) -> dict | None:
    """
        Validate a row of data.
        
        Args:
            raw_row (dict): The row to validate.
        
        Returns:
            dict: The validated row with cleaned image URLs, or None if validation fails.
    """

    logger.info(f"Validating row: {raw_row.get('productName')}")

    # Check for required fields
    name = raw_row.get("productName", "").strip()
    product_url = raw_row.get("productUrl", "")
    image_urls = raw_row.get("imageUrl", [])

    # Validate required fields
    if not name or not product_url or not image_urls:
        logger.warning("Missing required fields: productName, productUrl, or imageUrl")
        return None
    
    # Validate product name
    if not isinstance(name, str):
        logger.warning(f"Invalid product name: {name}")
        return None

    # Validate product URL
    if not isValidUrl(product_url):
        logger.warning(f"Invalid product URL: {product_url}")
        return None
  
    # Validate Image URLs
    if not isinstance(image_urls, list):
        logger.warning(f"imageUrl should be a list, got {type(image_urls).__name__}")
        return None
    
    # Clean image URLs
    cleaned_image_urls = [url for url in image_urls if isValidImageUrl(url)]

    # If no valid image URLs are found, log a warning and return None
    if not cleaned_image_urls:
        logger.warning(f"No valid image URLs found for product: {name}")
        return None
    
    raw_row["imageUrl"] = cleaned_image_urls

    # Validate other fields
    if "designer" in raw_row and not isinstance(raw_row["designer"], str):
        logger.warning(f"Invalid designer name: {raw_row['designer']}")
        return None
  
    if "description" in raw_row and not isinstance(raw_row["description"], str):
        logger.warning(f"Invalid description: {raw_row['description']}")
        return None
    
    return raw_row

def validateData(data: pd.DataFrame) -> list:
    """
        Validate a list of data rows.
        
        Args:
            data (pd.DataFrame): The DataFrame containing the data to validate.
        
        Returns:
            list: A list of validated rows.
    """

    logger.info("Validating data...")

    validated_data = []

    for _, row in data.iterrows():
        try:
            image_urls = safeParseImageUrls(row["imageUrl"])
            row["imageUrl"] = image_urls
        except Exception as e:
            logger.error(f"Error parsing image URLs: {e}")
            row["imageUrl"] = []
    
        # Validate the row
        cleaned_row = validateRow(row)
        if cleaned_row is not None:
            validated_data.append(cleaned_row)
        else:
            logger.warning(f"Row validation failed: {row.to_dict()}")

    logger.info(f"Validation complete. Validated {len(validated_data)} out of {len(data)} rows.")
    
    return validated_data