import logging


def validation_logger_setup():
    """
        Set up the logger for validation logs.
        
        This function configures the logging settings for the validation module,
        including the log file name, logging level, format, and date format.
    """
    
    logging.basicConfig(
        filename="logs/scraper_logs.log",
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

logger = logging.getLogger(__name__)