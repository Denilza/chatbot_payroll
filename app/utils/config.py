import os
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

class Settings:
    """Configurações da aplicação"""
    
    # LLM
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    LLM_MODEL: str = os.getenv("LLM_MODEL", "gpt-3.5-turbo")
    LLM_BASE_URL: Optional[str] = os.getenv("LLM_BASE_URL")
    
    # Web Search (Opcional)
    SERPER_API_KEY: str = os.getenv("SERPER_API_KEY", "")
    
    # App
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    MAX_CONVERSATION_HISTORY: int = int(os.getenv("MAX_CONVERSATION_HISTORY", "10"))
    
    # Paths
    DATA_DIR: str = "data"
    PAYROLL_FILE: str = "payroll.csv"

settings = Settings()