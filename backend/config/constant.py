UPLOAD_FOLDER = 'uploads'

ALLOWED_EXTENSIONS = {'txt', 'csv', 'json', 'xlsx'}

CATEGORIES = ['sofas', 'armchairs']

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

# Constants for link selectors
LINK_SELECTORS = [
    'a[href*="product"]', 'a[href*="item"]', 'a[href*="collection"]', \
    'a[href*="category"]', 'a[href*="furniture"]', 'a[href*="sofa"]', \
    'a[href*="armchair"]', '.product a', '.item a', '.collection a', \
    '.category a', 'a[class*="product"]', 'a[class*="item"]', 'a[class*="collection"]'
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
    'h1', 'h2', '.product-title', '.product-name', '.title', 
    '.name', '[class*="title"]', '[class*="name"]'
]

DESC_SELECTORS = [
    '.description', '.product-description', '.product-info',
    '.details', '.content', '[class*="description"]'
]

DESIGNER_SELECTORS = [
    '.designer', '.brand', '.author', '.by', 
    '[class*="designer"]', '[class*="brand"]'
]