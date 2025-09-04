# Import necessary libraries
import os
import asyncio
import json
import logging
from queue import Queue
from flask_cors import CORS
from threading import Thread
from datetime import datetime
from flask import Flask, request, jsonify, Response
from logs.loggers import loggerSetup, logger
from services.scraper import FurnitureScrapingPipeline
from config.constant import UPLOAD_FOLDER, CATEGORIES, SCRAPED_FOLDER
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
os.makedirs(SCRAPED_FOLDER, exist_ok=True)

# Global log queue for real-time streaming
log_queue = Queue()

class SSELogHandler(logging.Handler):
    """Custom logging handler that sends logs to the SSE queue"""
    
    def emit(self, record):
        try:
            log_entry = {
                'message': self.format(record),
                'level': self.get_log_level(record.levelno),
                'timestamp': datetime.now().strftime('%H:%M:%S')
            }
            log_queue.put(log_entry)
        except Exception:
            self.handleError(record)
    
    def get_log_level(self, levelno):
        if levelno >= logging.ERROR:
            return 'error'
        elif levelno >= logging.WARNING:
            return 'warning'
        elif levelno >= logging.INFO:
            return 'info'
        else:
            return 'info'
        
# Add SSE handler to logger
sse_handler = SSELogHandler()
sse_handler.setFormatter(logging.Formatter('%(message)s'))
logger.addHandler(sse_handler)

def sendLogToFrontend(message, level='info'):
    """Helper function to send custom log messages to frontend"""
    log_entry = {
        'message': message,
        'level': level,
        'timestamp': datetime.now().strftime('%H:%M:%S')
    }
    log_queue.put(log_entry)

async def processSingleInput(data: str, furniture_categories: list[str]) -> str:
    """
        Process a single input which can be a brand name or a URL.
        
        Args:
            data (str): The input data, which can be a brand name or a URL.
            furniture_categories (list[str]): Contains the list of furniture categories.
            
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
        # openai_key = "openai-api-key"
        # pipeline = FurnitureScrapingPipeline(openai_api_key=openai_key)  # with AI
        
        res = await pipeline.scrapeAnyWebsite(
            site_url, 
            categories=furniture_categories
        )
        logger.info(f"Category information extracted for {site_url}")

        result += "\n" + logSummary(res[0])

        logger.info(f"Converting the scraped data to Excel file: 'scraped_files/{website_name}.xlsx'")
        exportToExcel(res[0], f'scraped_file/{website_name}')
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

@app.route('/logs')
def streamLogs():
    """Server-Sent Events endpoint for real-time logs"""
    def generate():
        try:
            while True:
                try:
                    # Get log entry from queue (blocking with timeout)
                    log_entry = log_queue.get(timeout=30)
                    yield f"data: {json.dumps(log_entry)}\n\n"
                except:
                    # Send heartbeat to keep connection alive
                    yield f"data: {json.dumps({'message': '', 'level': 'heartbeat', 'timestamp': ''})}\n\n"
        except GeneratorExit:
            # Client disconnected, safely exit generator
            print("Client disconnected from logs stream")
            return
    
    return Response(generate(), mimetype='text/event-stream', headers={
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
        'Access-Control-Allow-Origin': '*',
    })

@app.route('/process', methods=['POST'])
def processData():
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
            funiture_categories = request.form.get('categories')
            if not data:
                logger.error("Empty data provided for single input processing.")
                return jsonify({
                    "success": False,
                    "error": "Single input data is required"
                }), 400
            sendLogToFrontend("Processing started", "info")
            result = asyncio.run(processSingleInput(data, funiture_categories))
                        
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
    logger.info("Frontend should be accessible at: http://localhost:8000")
    logger.info("API endpoints:")
    logger.info("  GET  / - Home page")
    logger.info("  POST /process - Process form data")
    
    app.run(debug=True, host='0.0.0.0', port=8000)
