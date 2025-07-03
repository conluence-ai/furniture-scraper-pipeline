# Furniture Scraper

A smart and adaptable web scraper for extracting furniture product information from single or multiple websites. Built using **Playwright** and **BeautifulSoup**, it can intelligently navigates through complex website structures to collect data such as product names, list of URLs of product images, designer name of the product, descriptions regarding product, and product URL.

## Features

- **Flexible Input Options** *(Working on it)*
    
    Accepts breand names as:
    
    - A single string (e.g. "Casa Magna" or "https://www.casamagna.eu")
    - A list of brand names
    - A file input (`.csv`, `.xlsx`, or `.json`)


- **Smart Link Parsing** *(Working on it)*

    Navigates through main categories, subcategories, and dynamically loaded content to reach product-level pages.

- **Duplicate Detection** - 
- **Pagination Support** - 
- **Rate Limiting & Page Load Handling**
    
    Built in delays and waits to accomodate slow-loading pages and avoid triggering anti-bot systems.

## Requirements

- Python 3.8+
- [Playwright](https://palywright.dev/python)
- Chromium browser (automatically installed via Playwright)

## Installation

1. Clone the repository:
    ```bash
        git checkout https://github.com/conluence-ai/furniture-scraper-pipeline.git
        cd funiture-scraper-pipeline
    ```

2. Install required dependencies:
    ```bash
        pip install -r requirements.txt
    ```

3. Install Playwright browsers (first-time only):
    ```bash
        playwright install
    ```