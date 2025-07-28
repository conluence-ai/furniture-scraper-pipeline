import logging

def loggerSetup():
    """
        Set up the logger for logs.
        
        This function configures the logging settings for the module,
        including the log file name, logging level, format, and date format.
    """
    
    logging.basicConfig(
        filename="backend/logs/scraper_logs.log",
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

logger = logging.getLogger(__name__)