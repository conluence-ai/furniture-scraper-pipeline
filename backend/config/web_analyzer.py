# Import necessary libraries
import re
import requests
import logging
from bs4 import BeautifulSoup
from typing import Dict, List, Any

# Import local module
from backend.config.config import WebAnalysis

# Import constants
from backend.config.constant import PAGE_FRAMEWORK, FURNITURE_INDICATORS

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler()]
)

# Create a logger for this module
logger = logging.getLogger(__name__)

class WebsiteAnalyzer:
    """Analyzes website structure and determines scraping strategy"""
    
    def __init__(self):
        """Initialize the class"""
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                          '(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })

    def analyzeWebsite(self, url: str) -> WebAnalysis:
        """Analyze website to determine scraping strategy."""
        logger.info(f"Analyzing website {url} to determine scraping strategy")
        
        analysis: WebAnalysis = {
            'url': url,
            'requires_js': False,
            'framework': 'static',
            'complexity': 'simple',
            'recommended_scraper': 'requests',
            'detected_patterns': []
        }

        try:
            response = self.session.get(url, timeout=10)
            if response.status_code != 200:
                raise ValueError(f"Non-200 response: {response.status_code}")

            soup = BeautifulSoup(response.content, 'html.parser')

            # Step 1: Detect furniture-related patterns
            patterns = self._detectFurniturePatterns(soup)
            analysis['detected_patterns'] = patterns

            # Step 2: Check if product info exists in HTML
            product_elements = []
            for indicator in FURNITURE_INDICATORS:
                product_elements.extend(soup.find_all(class_=re.compile(indicator, re.I)))
                product_elements.extend(soup.find_all(id=re.compile(indicator, re.I)))

            if product_elements:
                # Products exist → static HTML, requests is sufficient
                analysis['requires_js'] = False
                analysis['recommended_scraper'] = 'requests'
                analysis['complexity'] = 'simple'
                analysis['framework'] = 'static'
            else:
                # No products found → likely JS-rendered
                analysis['requires_js'] = True
                analysis['recommended_scraper'] = 'playwright'
                analysis['complexity'] = 'complex'
                analysis['framework'] = 'dynamic'

            # Step 3: Optional framework detection
            scripts = soup.find_all('script')
            for script in scripts:
                script_content = script.string or ''
                script_src = script.get('src', '')
                for fw in PAGE_FRAMEWORK:
                    if fw in script_content.lower() or fw in script_src.lower():
                        analysis['framework'] = fw
                        # Only recommend Playwright if no product elements
                        if not product_elements:
                            analysis['requires_js'] = True
                            analysis['recommended_scraper'] = 'playwright'
                        break

        except Exception as e:
            logger.error(f"Error analyzing website {url}: {e}")
            analysis['requires_js'] = True
            analysis['recommended_scraper'] = 'playwright'
            analysis['framework'] = 'dynamic'
            analysis['complexity'] = 'complex'

        logger.info(f"Website analysis for {url}: {analysis}")
        return analysis

    def _detectFurniturePatterns(self, soup: BeautifulSoup) -> List[str]:
        """Detect common furniture-related patterns from parsed HTML content."""
        patterns = []
        for indicator in FURNITURE_INDICATORS:
            if soup.find(class_=re.compile(indicator, re.I)) or soup.find(id=re.compile(indicator, re.I)):
                patterns.append(indicator)
        return patterns
