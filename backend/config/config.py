from typing import List

class WebAnalysis:
    url: str
    requires_js: bool
    framework: str = 'static'
    complexity: str = 'simple'
    recommended_scraper: str = 'requests'
    detected_patterns: List = []