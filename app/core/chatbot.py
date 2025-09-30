from typing import List, Dict, Any, Tuple
from ..services.llm_service import LLMService
from .rag_engine import RAGEngine
from .memory import ConversationMemory
from ..models.schemas import ChatResponse, Evidence
from ..utils.config import settings
from ..utils.logger import logger

class Chatbot:
    def __init__(self, rag_engine: RAGEngine, llm_service: LLMService):
        self.rag_engine = rag_engine
        self.llm_service = llm_service
        self.memory = ConversationMemory(settings.MAX_CONVERSATION_HISTORY)
        
        # System prompt para o LLM
        self.system_prompt = """
        Você é um assistente especializado em folha de pagamento. Suas respostas devem ser:
        - Clarase concisas
        - Em português brasileiro
        - Com formatação adequada para valores monetários (R$)
        - Incluir as evidências fornecidas quando relevante
        
        Use as informações fornecidas para responder perguntas sobre folha de pagamento.
        Se não tiver informações suficientes, peça mais detalhes.
        Para perguntas gerais não relacionadas a folha, responda de forma útil mas breve.
        """
    
    def process_message(self, message: str, conversation_id: str = "default") -> ChatResponse:
        """Processa mensagem e retorna resposta"""
        
        # Adiciona mensagem do usuário ao histórico
        self.memory.add_message(conversation_id, "user", message)
        
        # Analisa intenção
        intent = self.llm_service.extract_intent(message)
        
        # Processa com RAG se for sobre folha
        if intent["is_payroll_related"]:
            response_text, evidence = self.rag_engine.process_query(message)
            sources = ["payroll.csv"]
        else:
            # Usa LLM para perguntas gerais
            messages = self._build_messages(conversation_id, message)
            response_text = self.llm_service.generate_response(messages)
            evidence = []
            sources = []
        
        # Adiciona resposta ao histórico
        self.memory.add_message(conversation_id, "assistant", response_text)
        
        return ChatResponse(
            response=response_text,
            evidence=evidence,
            sources=sources,
            conversation_id=conversation_id
        )
    
    def _build_messages(self, conversation_id: str, current_message: str) -> List[Dict[str, str]]:
        """Constrói lista de mensagens para o LLM"""
        messages = [{"role": "system", "content": self.system_prompt}]
        
        # Adiciona histórico
        history = self.memory.get_history(conversation_id)
        messages.extend(history)
        
        # Adiciona mensagem atual
        messages.append({"role": "user", "content": current_message})
        
        return messages