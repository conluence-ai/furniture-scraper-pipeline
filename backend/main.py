# Import necessary libraries
import io
import os
import asyncio
import json
import logging
import zipfile
import pandas as pd
from flask_cors import CORS
from urllib.parse import urlparse
from flask import Flask, request, jsonify, Response, send_from_directory, send_file

# Import local modules
from backend.services.scraper import processSingleInput
from backend.logs.logs_handler import SSELogHandler, sendLogToFrontend, log_queue

# Import constants
from backend.config.constant import (
    SCRAPED_DIR,
    UPLOAD_DIR,
    PRICE_UPLOAD
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler()]
)

# Create a logger for this module
logger = logging.getLogger(__name__)

# Initialize flask app
app = Flask(__name__, static_folder="../frontend", static_url_path="/")
CORS(app)  # Enable CORS for all routes

# Configuration
app.config['UPLOAD_FOLDER'] = UPLOAD_DIR
app.config['PRICE_LISTINGS'] = PRICE_UPLOAD

# Create directory if it doesn't exist
os.makedirs(SCRAPED_DIR, exist_ok=True)
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(PRICE_UPLOAD, exist_ok=True)
        
# Add SSE handler to logger
sse_handler = SSELogHandler()
sse_handler.setFormatter(logging.Formatter('%(message)s'))
logging.getLogger().addHandler(sse_handler) 

# Health check endpoint
@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({"status": "healthy"}), 200

# Main scraper process endpoint
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

        # Handle price listing file upload
        price_file = request.files.get("priceListingFile")
        price_filename = None
        if price_file:
            price_filename = price_file.filename
            save_path = os.path.join(app.config["PRICE_LISTINGS"], price_filename)
            price_file.save(save_path)
            logger.info(f"Price listing file saved at {save_path}")
        
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
        
        elif input_type == 'file':
            file = request.files.get('file')
            if not file:
                return jsonify({"success": False, "error": "File is required"}), 400

            file_path = os.path.join(app.config["UPLOAD_FOLDER"], file.filename)
            file.save(file_path)
            logger.info(f"Uploaded input file saved at {file_path}")

            print(file_path)
            # Load file depending on extension
            if file.filename.endswith(".csv"):
                df = pd.read_csv(file_path)
            elif file.filename.endswith(".xlsx"):
                df = pd.read_excel(file_path)
            else:
                return jsonify({"success": False, "error": "Unsupported file type"}), 400

            print('this is working till here') 
            if "URL" not in df.columns:
                return jsonify({"success": False, "error": "File must contain a 'url' column"}), 400

            furniture_categories = request.form.get('categories')
            print('this is working till here', furniture_categories)

            sendLogToFrontend("Processing started for file input", "info")

            print('after log to frontend')

            results = []
            for url in df["URL"].dropna().unique():
                try:
                    logger.info(f"Processing {url}")
                    res = asyncio.run(processSingleInput(url, furniture_categories))
                    results.append({"url": url, "result": res})
                except Exception as e:
                    logger.error(f"Error scraping {url}: {e}")
                    results.append({"url": url, "error": str(e)})

            result = results

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

# Download scraped file
@app.route("/download/scraped", methods=["POST"])
def download_file():
    print('Inside download scraped data')

    # Check if file is re-sent in request (for file input case)
    if "file" in request.files:
        file = request.files["file"]
        print(file)
        # Save temporarily
        file_path = os.path.join(app.config["UPLOAD_FOLDER"], file.filename)
        file.save(file_path)

        # Load file
        if file.filename.endswith(".csv"):
            df = pd.read_csv(file_path)
        elif file.filename.endswith((".xlsx", ".xls")):
            df = pd.read_excel(file_path)
        else:
            return jsonify({"error": "Unsupported file type"}), 400

        if "URL" not in df.columns:
            return jsonify({"error": "File must contain a 'url' column"}), 400

        # Extract domain names from urls
        domains = []
        for url in df["URL"].dropna().unique():
            try:
                hostname = urlparse(url).hostname or ""
                parts = hostname.split(".")
                if len(parts) > 1:
                    domains.append(parts[-2])  # e.g. www.brand.com -> brand
            except Exception as e:
                print(f"Error parsing url {url}: {e}")

        domains = list(set(domains))  # unique brands
        print("Extracted brands:", domains)

        # Zip scraped files for these brands
        memory_file = io.BytesIO()
        with zipfile.ZipFile(memory_file, "w") as zf:
            for brand in domains:
                file_path = os.path.join(SCRAPED_DIR, f"{brand}.xlsx")
                if os.path.exists(file_path):
                    zf.write(file_path, arcname=f"{brand}.xlsx")
        memory_file.seek(0)

        return send_file(
            memory_file,
            as_attachment=True,
            download_name="scraped_data.zip",
            mimetype="application/zip"
        )

    data = request.get_json(silent=True) or {}
    brand = data.get("brand", "scraped_data")

    file_path = os.path.join(SCRAPED_DIR, f"{brand}.xlsx")
    if not os.path.exists(file_path):
        return {"error": f"File not found for {brand}"}, 404
    try:
        return send_file(file_path, as_attachment=True)
    except FileNotFoundError:
        return jsonify({"error": f"No file found for {brand}"}), 404
    
# @app.route("/download/merged", methods=["POST"])
# def download_merged():
#     try:
#         data = request.get_json()
#         price_filename = data.get("price_filename")

#         if not price_filename:
#             return jsonify({"error": "No price listing file provided"}), 400

#         # Build path for uploaded price listing
#         price_path = os.path.join(app.config["PRICE_LISTINGS"], price_filename)
#         if not os.path.exists(price_path):
#             return jsonify({"error": f"Price listing file {price_filename} not found"}), 404

#         # ✅ Call your merge function here
#         merged_path = merge(price_path)  # make sure merge() returns the output path

#         return send_file(merged_path, as_attachment=True)

    except Exception as e:
        return jsonify({"error": f"Failed to merge: {str(e)}"}), 500

# Serve index.html
@app.route("/")
def serve_index():
    return send_from_directory(os.path.join(app.root_path, "..", "frontend"), "index.html")

if __name__ == '__main__':
    logger.info("Starting Flask server...")
    logger.info("Frontend should be accessible at: http://localhost:8001")
    logger.info("API endpoints:")
    logger.info("  GET  / - Home page")
    logger.info("  POST /process - Process form data")
    
    app.run(debug=True, host='0.0.0.0', port=8001)
