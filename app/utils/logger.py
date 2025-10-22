
import logging
import sys

# Configuração básica e direta
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('app.log', encoding='utf-8')
    ]
)

# Logger global
logger = logging.getLogger('chatbot_payroll')
logger.info("✅ Logger inicializado")