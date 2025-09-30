from typing import List, Dict, Any
from collections import deque

class ConversationMemory:
    def __init__(self, max_history: int = 10):
        self.max_history = max_history
        self.conversations: Dict[str, deque] = {}
    
    def add_message(self, conversation_id: str, role: str, content: str):
        """Adiciona mensagem ao histórico"""
        if conversation_id not in self.conversations:
            self.conversations[conversation_id] = deque(maxlen=self.max_history)
        
        self.conversations[conversation_id].append({
            "role": role,
            "content": content
        })
    
    def get_history(self, conversation_id: str) -> List[Dict[str, str]]:
        """Retorna histórico da conversa"""
        return list(self.conversations.get(conversation_id, []))
    
    def clear_history(self, conversation_id: str):
        """Limpa histórico da conversa"""
        if conversation_id in self.conversations:
            del self.conversations[conversation_id]