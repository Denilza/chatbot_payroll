import logging
import sys
from .config import settings

def setup_logger():
    """Configura o logger da aplicação"""
    
    logging.basicConfig(
        level=getattr(logging, settings.LOG_LEVEL),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('app.log', encoding='utf-8')
        ]
    )
    
    return logging.getLogger(__name__)

logger = setup_logger()