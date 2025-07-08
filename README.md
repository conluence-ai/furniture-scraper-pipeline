# Furniture Scraper

A smart and adaptable web scraper for extracting furniture product information from single or multiple websites. Built using **Playwright** and **BeautifulSoup**, it can intelligently navigates through complex website structures to collect: 
- Product names
- List of product image URLs
- Designer name
- Descriptions
- Product URL

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

## Input Options

The scraper accepts various forms of inputs to start the scraping process:

- **Single Brand Name or Official URL**

    Provide a single brand name or official website url:

    ```python
        "Casa Magna" or "https://www.casamagna.eu"
    ```

- **Multiple Brand Names or URLs**

    A list of brand names or official URLs can be passed to process multiple websites

    ```python
        ["Cassina", "Casa Magna"] or ["https://www.cassina.com/en", "https://www.casamagna.eu"]
    ```

- **File Input**

    Read brand names or official URLs from a file:
    
    - `.csv` (column: `brand` or `url`)
    - `.json` (key: `brand` or `url`)
    - `.xlsx` (sheet with a column: `brand` or `url`)


## Input File Format

The scraper supports multiple file formats for batch input. Each file should clearly indicate whether you are passing **brand names** or **official website URLs**

### Supported Formats

1. **CSV / Excel (`.csv`, `.xlsx`)**

- Must contain **one of the following column headers**:
    - `brand` -> when input is a company name (e.g., `"Casa Magna"`)
    - `url` -> when input is the official website (e.g., `"https://www.casamagna.eu"`)

    Example (`brands.csv` or `brands.xlsx`)

    | brand |
    | :- |
    | Cassina |
    | Casa Magna |

    or

    | url |
    | :- |
    | https://www.cassina.com/en |
    | https://www.casamagna.eu |

2. **JSON (`.json`)** 

- Must contain a signle top-level key: either `brand` or `url`.

**Example using brand names**:

```json
    {
        "brand": ["Cassina", "Casa Magna"]
    }
```

**Example using URLs**:

```json
    {
        "url": ["https://www.cassina.com/en", "https://www.casamagna.eu"]
    }
```

## How to Choose?

- Use `brand` when you want the scraper to **automatically discover** the website.
- Use `url` when you **already have** the official website(s) and want to skip discovery.

## Data Validation

After scraping, product rows go through a validation layer to ensure clean and usable data:

- **Product URL**: Checked to ensure it is valid and reachable (status 200).
- **Image URL**: 
    
    - Skips images that are `None`, `svg` or `logos`.
    - If invalid URLs exist, they are removed from the list.
- Row missing essential fields like Product Name or Product Url are skipped

## Merging with Price Listing Data

If you have an existing pricing sheet, you can merge it with the scraped data:

- Merging is done on **Product Name** and **Furniture Type**
- A fuzzy match is applied to the `Product Name` and `Furniture Type`
- You can configure whether price data or scraped data takes precedence during merge

## Logging

The scraper generates logs during processing:

- **Logs include**:

    - Validation 
    - Merging Files

- **Log Files**: Logs are saved to `logs/scraper_log.txt`