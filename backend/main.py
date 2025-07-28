# Import necessary libraries
import os
import asyncio
from flask_cors import CORS
from flask import Flask, request, jsonify
from logs.loggers import loggerSetup, logger
from config.constant import UPLOAD_FOLDER, CATEGORIES
from services.scraper import FurnitureScrapingPipeline
from utils.helpers import isValidUrl, getWebsiteName, searchOfficialWebsite, exportToExcel, logSummary

# Set up logs
loggerSetup()

# Initialize flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Configuration
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Create upload directory if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

async def processSingleInput(data: str) -> str:
    """
        Process a single input which can be a brand name or a URL.
        
        Args:
            data (str): The input data, which can be a brand name or a URL.
            
        Returns:
            str: Processed result or error message.
    """
    logger.info(f"Processing single input: {data}")

    # Initialize vairables
    result = ""
    site_url = ""
    website_name = ""
    brand_input = data.strip()

    # Check if the input is a valid URL
    if isValidUrl(brand_input):
        logger.info(f"Input is a valid URL: {brand_input}")

        site_url = brand_input
        website_name = getWebsiteName(site_url)
        
        result = f"Brand Name: {website_name.capitalize()}\n"
        result += f"Official Website: {site_url}\n"
    else:
        logger.info(f"Searching for official website of company: {brand_input}")

        site_url = searchOfficialWebsite(brand_input)
        website_name = getWebsiteName(site_url)
        
        logger.info(f"Official website found: {site_url}")
        
        result = f"Brand Name: {brand_input}\n"
        result += f"Official Website: {site_url}\n"

    # If no URL found, return error
    if not site_url:
        logger.error(f"No official website found for {brand_input}.")
        return f"Error: No official website found for {brand_input}."
    
    # Process the URL to extract category information
    try:
        logger.info(f"Extracting product information for {site_url}")

        # Initialize pipeline
        pipeline = FurnitureScrapingPipeline() # without AI
        # pipeline = FurnitureScrapingPipeline(openai_api_key="openai_key")  # with AI
        
        res = await pipeline.scrapeAnyWebsite(
            site_url, 
            categories=CATEGORIES
        )

        logger.info(f"Category information extracted for {site_url}")
        
        result += "\n" + logSummary(res)

        logger.info(f"Converting the scraped data to Excel file: 'scraped_files/{website_name}.xlsx'")
        exportToExcel(res, f'scraped_file/{website_name}')
        logger.info(f"Stored data to Excel file: 'scraped_files/{website_name}.xlsx'")

    except Exception as e:
        logger.error(f"Error processing URL {site_url}: {e}")
        return f"Error processing URL: {e}"

    # Return brand info
    return result
    
@app.route('/', methods=['GET'])
def home():
    """Home route for testing"""
    return jsonify({
        "message": "Flask backend is running!",
        "endpoints": {
            "GET /": "This endpoint",
            "POST /process": "Process form data"
        }
    })

@app.route('/process', methods=['POST'])
def process_data():
    """Main processing endpoint"""
    try:
        input_type = request.form.get('inputType')
        
        if not input_type:
            return jsonify({
                "success": False,
                "error": "Input type is required"
            }), 400
        
        result = ""
        
        # Process based on input type
        if input_type == 'single':
            data = request.form.get('data')
            if not data:
                logger.error("Empty data provided for single input processing.")
                return jsonify({
                    "success": False,
                    "error": "Single input data is required"
                }), 400
            result = asyncio.run(processSingleInput(data))
                        
        else:
            return jsonify({
                "success": False,
                "error": "Invalid input type"
            }), 400
        
        return jsonify({
            "success": True,
            "result": result,
            "input_type": input_type
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Server error: {str(e)}"
        }), 500
    
if __name__ == '__main__':
    logger.info("Starting Flask server...")
    logger.info("Frontend should be accessible at: http://localhost:5000")
    logger.info("API endpoints:")
    logger.info("  GET  / - Home page")
    logger.info("  POST /process - Process form data")
    
    app.run(debug=True, host='0.0.0.0', port=5000)