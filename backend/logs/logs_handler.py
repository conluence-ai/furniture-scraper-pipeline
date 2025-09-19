import logging
from queue import Queue
from datetime import datetime

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
        
def sendLogToFrontend(message, level='info'):
    """Helper function to send custom log messages to frontend"""
    log_entry = {
        'message': message,
        'level': level,
        'timestamp': datetime.now().strftime('%H:%M:%S')
    }
    log_queue.put(log_entry)