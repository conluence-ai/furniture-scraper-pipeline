import os

# Define Folder path and name
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SCRAPED_DIR = os.path.join(BASE_DIR, "scraped_file")
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")


ALLOWED_EXTENSIONS = ['txt', 'csv', 'json', 'xlsx']

# Determine website frameworks for analysis strategy
PAGE_FRAMEWORK = ['vue', 'react', 'angular', 'nuxt', 'next']

# Common furniture-related classes and IDs in root url
FURNITURE_INDICATORS = [
    'product', 'item', 'catalog', 'furniture', 'sofa', 'chair',
    'table', 'collection', 'designer', 'brand', 'category',
    'gallery', 'detail', 'overview', 'series', 'line',
    'model', 'variant', 'sku', 'code'
]

# Selectors to fetch category links
CATEGORY_SELECTORS = [
    'a[href*="category"]', 'a[href*="collection"]', 'a[href*="products"]',
    'a[href*="prodotto"]', 'a[href*="collezione"]', 'a[href*="divani"]',
    'a[href*="poltrone"]', 'a[href*="pouf"]', 'a[href*="sgabello"]',
    'a[href*="panca"]', 'a[href*="tavolo"]', 'a[href*="console"]',
    '.category a', '.collection a', '.product-category a', '.nav a',
    '.menu a', '.navigation a', 'a[class*="category"]', 'a[class*="collection"]',
    'a[href*="product"]', 'a[href*="prodotto"]', 'li a'
]

# Selectors to fetch product links
PRODUCT_SELECTORS = [
    'a[href*="product"]', 'a[href*="prodotto"]', 'a[href*="item"]',
    'a[href*="dettaglio"]', 'a[href*="detail"]', 'a[href*="portfolio"]',
    '.product a', '.product-item a', '.product-list a',
    '.product-thumb a', '.product-tile a', 'li a', 'a',
    '.section-product-list-container a'
]

# Keywords that typically identify product detail pages
PRODUCT_KEYWORDS = ['product/']

# Common non-product endings you want to ignore
COMMON_ENDINGS = {
    "product", "products", "item", "items", "catalog", 
    "shop", "store", "collections", "collection"
    "prodotto", "prodotti", "articolo", "articoli"
}

# Mapping categories
CATEGORY_SYNONYMS = {
    "sofa": ["sofa", "sofas", "divano", "divani"],
    "armchair": ["armchair", "armchairs", "poltrona", "poltrone"],
    "pouf": ["pouf", "pouffe", "ottoman", "ottomans"],
    "stool": ["stool", "stools", "sgabello", "sgabelli"],
    "bench": ["bench", "benches", "panca", "panche"],
    "table": ["table", "tables", "tavolo", "tavoli"],
    "console": ["console", "consoles"],
    "ottoman": ["ottoman", "ottomans", "pouf", "pouffe"]
}

# Filter links based on requested categories or furniture keywords
FURNITURE_KEYWORDS = [
    'sofa', 'collection', 'product', 'furniture', \
    'armchair', 'bookshelf', 'container', 'complement'
]

SELECTORS_TO_TRY = [
    '.product', '.item', 'article', '.content', \
    '[class*="product"]', '[class*="item"]'
]

GENERIC_CONTENT_LINK = ['product', 'item', 'detail']

# Product name selectors (titles/headings)
NAME_SELECTORS = [
    'h1', 'h2', 'h3',
    '.product-title', '.product-name', '.title', '.name',
    '[class*="title"]', '[class*="name"]',
    'meta[property="og:title"]', 'meta[name="title"]'
]

# Description selectors (details, summaries, info blocks)
DESC_SELECTORS = [
    '.description', '.product-description', '.product-info',
    '.details', '.content', '.summary', '.product-details',
    '[class*="description"]', '[class*="details"]', '[class*="info"]',
    'meta[name="description"]', 'meta[property="og:description"]'
]

# Designer / brand selectors
DESIGNER_SELECTORS = [
    '.designer', '.brand', '.author', '.by', '.firma'
    # '[class*="designer"]', '[class*="brand"]', '[class*="firma"]',
    # '[class*="author"]', '[class*="by"]'
]

# Image selectors (supporting lazy loading)
IMAGE_SELECTORS = [
    'img[src]', 'img[data-src]', 'img[data-lazy]', 'img[data-original]', 'img[data-srcset]',
    '.product-image img', '.gallery img', '.image-container img',
    '[class*="image"] img', '[class*="photo"] img', '[class*="gallery"] img'
]

INVALID_IMAGE = ['.svg', 'icon', 'logo', '.gif']