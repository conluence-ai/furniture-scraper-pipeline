# Furniture Scraper

A smart, adaptable and AI-driven web scraper for extracting furniture product information from single or multiple furniture websites. Built using Playwright and BeautifulSoup, it can intelligently navigates through complex website structures to collect: 
- Product names
- List of product image URLs
- Designer name
- Descriptions
- Product URL

## Features

- **Flexible Input Options:** Accepts brand names as:
    
    - A single string (e.g. "Casa Magna" or "https://www.casamagna.eu")
    - A list of brand names
    - A file input (`.csv`, `.xlsx`, or `.json`)

- **Universal Compatibility:** Works with any furniture website without manual configuration.

- **Smart Link Parsing:** Navigates through main categories, subcategories, and dynamically loaded content to reach product-level pages.

- **AI-Powered Extraction:** Automatically understands page structure and extracts product data.

- **Zero Configuration:** No need to write CSS selectors for each website.

- **Web Interface:** Easy to use Vue.js frontend with Flask backend.

- **Rate Limiting & Page Load Handling:** Built in delays and waits to accomodate slow-loading pages and avoid triggering anti-bot systems.

## Architecture

```sh
    Frontend (Vue.js) -> Backend (Flask) -> Scraping Pipeline (Python)
```

- **Frontend:** `index.html` - Vue.js interface for inputting websites and viewing results.
- **Backend:** Flask API that connects the frontend to the scraping pipeline.
- **Pipeline:** Universal scraper that handles any furniture website.

## Requirements

### Python Dependencies

```txt
# Core scraping 
requests
beautifulsoup4
playwright

# AI and NLP
openai
transformers

# Async and utilities
asyncio
python-dotenv

# Web framework
flask
flask-cors
```
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

## Running the Application

1. Start the Flask backend

    ```python
    python ./backend/scraper.py
    ```

2. Open the frontend

    ```txt
    Open index.html in your browser
    ```

## Usage

### Web Interface

1. Open `index.html` in your browser
2. Select the desired input type
3. Enter furniture website
4. Click "Start Scraping"

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