import re
import requests
import json
from typing import Dict, Optional
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from app.utils.config import settings
from app.utils.logger import logger

class WebSearch:
    def __init__(self):
        self.serper_api_key = settings.SERPER_API_KEY
    
    def search_selic_rate(self) -> Dict[str, Optional[str]]:
        """Busca a taxa Selic atual"""
        try:
            if not self.serper_api_key:
                return {
                    "error": "Chave da API de busca não configurada",
                    "source": None
                }
            
            # Busca por "taxa Selic atual"
            url = "https://google.serper.dev/search"
            payload = json.dumps({
                "q": "taxa selic atual 2024",
                "num": 3
            })
            headers = {
                'X-API-KEY': self.serper_api_key,
                'Content-Type': 'application/json'
            }
            
            response = requests.post(url, headers=headers, data=payload, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            # Extrai a informação da taxa Selic dos resultados
            selic_info = self._extract_selic_info(data)
            return selic_info
            
        except Exception as e:
            logger.error(f"Erro na busca da Selic: {e}")
            return {
                "error": f"Erro ao buscar taxa Selic: {e}",
                "source": None
            }
    
    def _extract_selic_info(self, data: Dict) -> Dict[str, Optional[str]]:
        """Extrai informação da taxa Selic dos resultados da busca"""
        try:
            if 'organic' not in data or not data['organic']:
                return {
                    "error": "Nenhum resultado encontrado",
                    "source": None
                }
            
            # Pega o primeiro resultado
            first_result = data['organic'][0]
            title = first_result.get('title', '')
            snippet = first_result.get('snippet', '')
            link = first_result.get('link', '')
            
            # Tenta extrair a taxa Selic do snippet
            selic_rate = self._find_selic_in_text(snippet) or self._find_selic_in_text(title)
            
            if selic_rate:
                return {
                    "rate": selic_rate,
                    "source": link,
                    "snippet": snippet[:200] + "..." if len(snippet) > 200 else snippet
                }
            else:
                return {
                    "error": "Taxa Selic não encontrada nos resultados",
                    "source": link,
                    "snippet": snippet[:200] + "..." if len(snippet) > 200 else snippet
                }
                
        except Exception as e:
            logger.error(f"Erro ao extrair info da Selic: {e}")
            return {
                "error": f"Erro ao processar resultados: {e}",
                "source": None
            }
    
    def _find_selic_in_text(self, text: str) -> Optional[str]:
        """Encontra a taxa Selic no texto"""
        patterns = [
            r'Selic[\s\S]*?(\d+[.,]\d+)%',
            r'taxa Selic[\s\S]*?(\d+[.,]\d+)%',
            r'(\d+[.,]\d+)%[\s\S]*?Selic',
            r'Selic[\s\S]*?(\d+[.,]\d+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).replace(',', '.') + "%"
        
        return None

# Versão alternativa sem API (fallback)
class WebSearchFallback:
    def search_selic_rate(self) -> Dict[str, Optional[str]]:
        """Versão fallback sem API externa"""
        return {
            "rate": "13,25%",  # Valor exemplo
            "source": "https://www.bcb.gov.br/controleinflacao/taxaselic",
            "snippet": "Taxa Selic definida pelo Copom. Consulte o site oficial do Banco Central para informações atualizadas.",
            "note": "Dado ilustrativo - Configure SERPER_API_KEY para busca em tempo real"
        }