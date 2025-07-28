# Import necessary libraries
import re
import requests
from bs4 import BeautifulSoup
from typing import Dict, List, Any
from logs.loggers import loggerSetup, logger
from config.constant import ANALYSIS, PAGE_FRAMEWORK, FURNITURE_INDICATORS

# Set up logs
loggerSetup()

class WebsiteAnalyzer:
    """Analyzes website structure and determines scraping strategy"""
    
    def __init__(self):
        """
            Initialize the class

            Returns:
                None
        """
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
    
    def analyzeWebsite(self, url: str) -> Dict[str, Any]:
        """
            Analyze website to determine scraping strategy.

            Args:
                url (str): The URL of the website to be analyzed.

            Returns:
                Dict[str, Any]: A dictionary containing configuration details
        """
        try:
            analysis = ANALYSIS
            response = self.session.get(url, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Check for JavaScript frameworks
            scripts = soup.find_all('script')
            for script in scripts:
                script_content = script.string or ''
                script_src = script.get('src', '')
                
                if any(framework in script_content.lower() or framework in script_src.lower() 
                       for framework in PAGE_FRAMEWORK):
                    analysis['requires_js'] = True
                    analysis['recommended_scraper'] = 'playwright'
                    
                    if 'vue' in script_content.lower() or 'vue' in script_src.lower():
                        analysis['framework'] = 'vue'
                    elif 'react' in script_content.lower() or 'react' in script_src.lower():
                        analysis['framework'] = 'react'
                    elif 'angular' in script_content.lower():
                        analysis['framework'] = 'angular'
            
            # Check for common furniture website patterns
            patterns = self._detectFurniturePatterns(soup)
            analysis['detected_patterns'] = patterns
            
            # Determine complexity
            if len(patterns) < 2:
                analysis['complexity'] = 'complex'
            
            logger.info(f"Website analysis for {url}: {analysis}")
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing website {url}: {e}")
            analysis['recommended_scraper'] = 'playwright'  # Default to most robust option
            return analysis
    
    def _detectFurniturePatterns(self, soup: BeautifulSoup) -> List[str]:
        """
            Detect common furniture-related patterns from parsed HTML content.

            Args:
                soup (BeautifulSoup): Parsed HTML content of the page.

            Returns:
                List[str]: A list of detected furniture-related patterns or classes.
        """
        patterns = []
        
        # Common furniture-related classes and IDs
        for indicator in FURNITURE_INDICATORS:
            if soup.find(class_=re.compile(indicator, re.I)) or soup.find(id=re.compile(indicator, re.I)):
                patterns.append(indicator)
        
        return patterns