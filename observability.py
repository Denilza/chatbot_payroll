import uuid
from datetime import datetime
from typing import Dict, Any
import logging

logger = logging.getLogger('chatbot_payroll')

class Observability:
    def __init__(self, app_name: str = "chatbot_payroll"):
        self.app_name = app_name
        logger.info(f"🔍 Observabilidade inicializada para {app_name}")
    
    def log_interaction(self, 
                       session_id: str,
                       user_input: str, 
                       response: str, 
                       response_time: float,
                       status: str = "success",
                       tokens_used: int = 0,
                       guardrail_metadata: Dict[str, Any] = None):
        
        interaction_id = str(uuid.uuid4())[:8]
        
        if status == "success":
            log_message = f"✅ SUCCESS | Sessão: {session_id} | Tempo: {response_time:.2f}s"
            logger.info(log_message)
        elif status == "blocked":
            motivo = guardrail_metadata.get('failed_checks', ['unknown']) if guardrail_metadata else ['unknown']
            log_message = f"🚫 BLOCKED | Sessão: {session_id} | Motivo: {', '.join(motivo)}"
            logger.warning(log_message)
        else:
            log_message = f"❌ ERROR | Sessão: {session_id}"
            logger.error(log_message)
        
        return interaction_id
    
  
    def log_guardrail_trigger(self,
                             session_id: str,
                             guardrail_type: str,
                             user_input: str,
                             details: Dict[str, Any]):
        
        trigger_id = str(uuid.uuid4())[:8]
        motivo = ', '.join(details.get('failed_checks', ['unknown']))
        
        log_message = f"🛡️ GUARDRAIL | Tipo: {guardrail_type} | Motivo: {motivo}"
        logger.warning(log_message)
        
        return trigger_id
