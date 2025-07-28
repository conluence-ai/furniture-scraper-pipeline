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

PAGE_FRAMEWORK = ['vue', 'react', 'angular', 'nuxt', 'next']

FURNITURE_INDICATORS = [
    'product', 'item', 'catalog', 'furniture', 'sofa', 'chair', 
    'table', 'collection', 'designer', 'brand', 'category'
]

LINK_SELECTORS = [
    'a[href*="product"]', 'a[href*="item"]', \
    '.product a', '.item a', 'a[class*="product"]'
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