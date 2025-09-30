from openai import OpenAI
from typing import List, Dict, Any, Optional
from ..utils.config import settings
from ..utils.logger import logger

class LLMService:
    def __init__(self):
        self.client = OpenAI(
            api_key=settings.OPENAI_API_KEY,
            base_url=settings.LLM_BASE_URL
        )
        self.model = settings.LLM_MODEL
    
    def generate_response(self, messages: List[Dict[str, str]]) -> str:
        """Gera resposta do LLM"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.1,
                max_tokens=500
            )
            
            return response.choices[0].message.content.strip()
        
        except Exception as e:
            logger.error(f"Erro ao chamar LLM: {e}")
            return "Desculpe, ocorreu um erro ao processar sua mensagem."
    
    def extract_intent(self, user_message: str) -> Dict[str, Any]:
        """Extrai intenção da mensagem do usuário"""
        payroll_keywords = [
            'salário', 'folha', 'pagamento', 'líquido', 'bruto', 'desconto',
            'INSS', 'IRRF', 'bônus', 'competência', 'recebi', 'holerite'
        ]
        
        message_lower = user_message.lower()
        
        # Verifica se é sobre folha de pagamento
        is_payroll_related = any(keyword in message_lower for keyword in payroll_keywords)
        
        return {
            "is_payroll_related": is_payroll_related,
            "requires_web_search": not is_payroll_related and any(
                kw in message_lower for kw in ['selic', 'taxa', 'atual', 'notícia']
            )
        }