# Import necessary libraries
import os
import asyncio
import json
import logging
from flask_cors import CORS
from flask import Flask, request, jsonify, Response, send_from_directory, send_file

# Import local modules
from backend.services.scraper import processSingleInput
from backend.logs.logs_handler import SSELogHandler, sendLogToFrontend, log_queue

# Import constants
from backend.config.constant import SCRAPED_DIR, UPLOAD_DIR

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

# Create directory if it doesn't exist
os.makedirs(SCRAPED_DIR, exist_ok=True)
os.makedirs(UPLOAD_DIR, exist_ok=True)
        
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
    data = request.get_json()
    brand = data.get("brand", "scraped_data")
    print('Download for brand', brand)


    file_path = os.path.join(SCRAPED_DIR, f"{brand}.xlsx")  # adjust your file path logic
    print('File path: ', file_path)
    if not os.path.exists(file_path):
        return {"error": f"File not found for {brand}"}, 404
    try:
        return send_file(file_path, as_attachment=True)
    except FileNotFoundError:
        return jsonify({"error": f"No file found for {brand}"}), 404

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
