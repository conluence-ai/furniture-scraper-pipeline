import re
import time
import ast
from googlesearch import search
from urllib.parse import urljoin, urlparse

def is_valid_url(url: str) -> bool:
    """
        Check if the given URL is valid.
        
        Args:
            url (str): The URL to check.
            
        Returns:
            bool: True if the URL is valid, False otherwise.
    """
    parsed_url = urlparse(url)
    return bool(parsed_url.scheme and parsed_url.netloc)

def search_official_website(company_name: str) -> str:
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

        return ""
    except Exception as e:
        print(f"Error searching for {company_name}: {e}")
        return ""

# TODO: Function is incomplete, need to implement cookie acceptance logic 
def accept_cookies(page):
    """
        Accept cookies on the page if a cookie banner is present.
        
        Args:
            page: The Playwright page object.
    """

    print("Checking for cookie banner...")

    # TODO: Create dictionary of possible cookie banner texts 
    possible_texts = [
        "Accept Cookies", "Accept All Cookies", "Accept", "Accept All",
        "Allow Cookies", "Allow All"
        "Cookie Consent", "Cookie Policy",
        "I Agree", "Yes, I Agree", "I Understand", "Agree",
        "Got it", "OK", "I Consent"
    ]

    # Check for common cookie banner text in the page content
    try:
        buttons = page.query_selector_all("button, [role='button'], input[type='submit']")
        count = buttons.count()
        for i in count:
            try: 
                button = buttons.nth(i)
                text = button.inner_text(timeout=1000).strip()
                if any(re.search(rf'\b{text_variant}\b', text, re.IGNORECASE) for text_variant in possible_texts):
                    print(f"Accepting cookies: {text}")
                    button.click(timeout=1000)
                    time.sleep(1)
                    return
            except Exception as e:
                continue

    except Exception as e:
        pass

    for label in possible_texts:
        try:
            # Try to find a button with the label text
            if page.locator(f"text='{label}'").is_visible(timeout=1000):
                print(f"Clicking cookie text match: {label}")
                page.locator(f"text='{label}'").click(timeout=1000)
                time.sleep(1)
                return
        except Exception as e:
            continue

    print("No cookie banner found or no action taken.")

def extract_categories(page, url):
    """
        Extract categories from the page.
        
        Args:
            page: The Playwright page object.
            url (str): The URL of the page.
            
        Returns:
            list: A list of dictionaries containing category names and URLs.
    """
    links = page.locator("a")
    category_links = []
    seen = set()

    for i in range(links.count()):
        try:
            link = links.nth(i)
            text = link.inner_text().strip()
            href = link.get_attribute("href")

            if not href or href.startswith("#") or "javascript:" in href:
                continue
            
            full_url = urljoin(url, href)

            if full_url in seen:
                continue

            # TODO: Create dictionary of possible category keywords (It can also have direct category names)
            if re.search(r"(category|collection|furniture|products|collections?|catalog|shop|sofas|armchairs|chairs)\b", href, re.IGNORECASE):
                category_links.append({"name": text, "url": full_url})
                seen.add(full_url)
        
        except Exception as e:
            continue

    return category_links

def is_valid_category(url: str, brand_domain: str) -> bool:
    """
        Check if the given URL is a valid category URL.
        
        Args:
            url (str): The URL to check.
            brand_domain (str): The domain of the brand's official website.
            
        Returns:
            bool: True if the URL is a valid category, False otherwise.
    """

    parsed_url = urlparse(url)

    if brand_domain not in parsed_url.netloc:
        return False

    # TODO: Create dictionary of invalid keywords
    # Check for common invalid keywords in the URL
    invalid_keywords = [
        "download", "press", "news", "events", "blog", "contact", "about", "privacy", "terms", "legal", "new"
    ]

    if any(re.search(rf'\b{keyword}\b', url, re.IGNORECASE) for keyword in invalid_keywords):
        return False

    # TODO: Create dictionary of allowed keywords
    # Check for common allowed keywords in the URL
    allowed_keywords = [
        'sofas', 'sofa', 'armchairs', 'armchair', 'modular-sofas', 'modular-sofa', 'pouffes', 'pouffe', 'ottomans', 'ottoman', 'recliner', 'recliners', 'chairs', 'chair', 'seating', 'lounge', 'benches', 'bench', 'stools', 'stool'
    ]

    return any(re.search(rf'\b{keyword}\b', url, re.IGNORECASE) for keyword in allowed_keywords)

# TODO: Function is incomplete, need to extract subcategories from a category page
def extract_subcategories(page, category_url):
    """
        Extract subcategories from a category page.
        
        Args:
            page: The Playwright page object.
            category_url (str): The URL of the category page.
            
        Returns:
            list: A list of dictionaries containing subcategory names and URLs.
    """

    page.goto(category_url)    
    subcategories = []
    links = page.locator("a")
    seen = set()

    for i in range(links.count()):
        try:
            link = links.nth(i)
            # text = link.inner_text().strip()
            href = link.get_attribute("href")
            
            # if not text or not href:
            #     continue
            if not href:
                continue

            full_url = urljoin(category_url, href)

            if full_url in seen or "#" in href or "javascript:" in href:
                continue
                        # if re.search(r"(product)\b", text, re.IGNORECASE):
            seen.add(full_url)
            subcategories.append({"url": full_url})
        
        except:
            continue
    
    return subcategories
    
def toCamelCase(s: str) -> str:
    """
        Convert a string to CamelCase format.
        
        Args:
            s (str): The string to convert.
        
        Returns: 
            str: The CamelCase formatted string.
    """

    parts = re.split(r"[\s_]", s)
    return parts[0].lower() + "".join(word.capitalize() for word in parts[1:])

def safeParseImageUrls(value: str) -> list:
    """
        Safely parse a string representation of a list of image URLs.
        
        Args:
            value (str): The string to parse.
        
        Returns:
            list: A list of image URLs if parsing is successful, otherwise an empty list.
    """

    if isinstance(value, list):
        return value
    
    try:
        return ast.literal_eval(value)
    except:
        return []
