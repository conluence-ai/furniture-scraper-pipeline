import os

# Define Folder path and name
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SCRAPED_DIR = os.path.join(BASE_DIR, "scraped_file")
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")


ALLOWED_EXTENSIONS = ['txt', 'csv', 'json', 'xlsx']

CATEGORIES = ['sofa', 'armchairs']

ANALYSIS = {
    'url': str,
    'requires_js': False,
    'framework': 'static',
    'complexity': 'simple',
    'recommended_scraper': 'requests',
    'detected_patterns': []
}

# PAGE_FRAMEWORK = ['vue', 'react', 'angular', 'nuxt', 'next']
PAGE_FRAMEWORK = ['vue']

# Common furniture-related classes and IDs
FURNITURE_INDICATORS = [
    'product', 'item', 'catalog', 'furniture', 'sofa', 'chair',  \
    'table', 'collection', 'designer', 'brand', 'category'
]

# Enhanced selectors for category links
CATEGORY_SELECTORS = [
    'a[href*="category"]', 'a[href*="collection"]', 'a[href*="products"]', \
    'a[href*="sofa"]', 'a[href*="armchair"]', '.category a', '.collection a', \
    '.product-category a', '.nav a', '.menu a', '.navigation a', \
    'a[class*="category"]', 'a[class*="collection"]', 'a[href*="product"]'
]

# Filter links based on requested categories or furniture keywords
FURNITURE_KEYWORDS = [
    'sofa', 'collection', 'product', 'furniture', \
    'armchair', 'bookshelf', 'container', 'complement'
]

SELECTORS_TO_TRY = [
    '.product', '.item', 'article', '.content', \
    '[class*="product"]', '[class*="item"]'
]

PRODUCT_SELECTORS = [
    'a[href*="product"]', 'a[href*="item"]', 'a[href*="furniture"]', \
    '.product-link', '.item-link', '.product a', '.item a', \
    'a[class*="product"]', 'a[class*="item"]'
]

GENERIC_CONTENT_LINK = ['product', 'item', 'detail']

PRODUCT_RESULT = {
    'productName': '',
    'description': '',
    'productUrl': '',
    'designerName': '',
    'imageUrls': [],
    'category': ''
}

NAME_SELECTORS = [
    'h1', 'h2', '.product-title', '.product-name', '.title', \
    '.name', '[class*="title"]', '[class*="name"]'
]

DESC_SELECTORS = [
    '.description', '.product-description', '.product-info', \
    '.details', '.content', '[class*="description"]'
]

# DESIGNER_SELECTORS = [
#     '.designer', '.brand', '.author', '.by', \
#     '[class*="designer"]', '[class*="brand"]'
# ]

DESIGNER_SELECTORS = ['.designer']

# Extract images with better handling for lazy-loaded images
IMAGE_SELECTORS = [
    'img[src]', 'img[data-src]', 'img[data-lazy]', 'img[data-original]',
    '.product-image img', '.gallery img', '.image-container img',
    '[class*="image"] img', '[class*="photo"] img'
]

INVALID_IMAGE = ['.svg', 'icon', 'logo', '.gif']