import logging
import sys
from logging.handlers import RotatingFileHandler
import os

def setup_logging():
    log_dir = 'logs'
    os.makedirs(log_dir, exist_ok=True)
    
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_format = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(console_format)
    
    file_handler = RotatingFileHandler(
        f'{log_dir}/robotcem.log',
        maxBytes=10*1024*1024,
        backupCount=5
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(console_format)
    
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    return logger
