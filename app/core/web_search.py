import requests
from duckduckgo_search import DDGS
from typing import List, Dict, Optional
import re
from datetime import datetime
import json


class WebSearchService:
    """Serviço para busca web com citação de fontes"""
    
    def __init__(self):
        self.ddgs = DDGS()
    
    def search_selic_rate(self) -> Dict[str, str]:
        """
        Busca a taxa Selic atual com fontes confiáveis
        Retorna: {'taxa': 'valor', 'fonte': 'url', 'descricao': 'texto'}
        """
        try:
            # Busca por termos relacionados à Selic
            search_terms = [
                "taxa selic atual Banco Central",
                "Selic hoje BCB",
                "taxa básica de juros Brasil",
                "Copom Selic atual"
            ]
            
            results = []
            for term in search_terms:
                search_results = self.ddgs.text(
                    term, 
                    region='br-br', 
                    max_results=3
                )
                results.extend(search_results)
            
            # Filtra fontes confiáveis
            reliable_sources = self._filter_reliable_sources(results)
            
            if reliable_sources:
                best_result = reliable_sources[0]
                selic_value = self._extract_selic_value(best_result['body'])
                
                return {
                    'taxa': selic_value,
                    'fonte': best_result['href'],
                    'descricao': best_result['body'][:200] + "...",
                    'timestamp': datetime.now().isoformat()
                }
            else:
                return {
                    'taxa': 'Não encontrada',
                    'fonte': 'Busca não retornou resultados confiáveis',
                    'descricao': 'Tente novamente em alguns instantes',
                    'timestamp': datetime.now().isoformat()
                }
                
        except Exception as e:
            return {
                'taxa': 'Erro na busca',
                'fonte': f'Erro: {str(e)}',
                'descricao': 'Não foi possível acessar as informações',
                'timestamp': datetime.now().isoformat()
            }
    
    def search_general_info(self, query: str, max_results: int = 3) -> List[Dict]:
        """
        Busca geral por informações na web
        """
        try:
            results = self.ddgs.text(
                query, 
                region='br-br', 
                max_results=max_results
            )
            
            formatted_results = []
            for result in results:
                formatted_results.append({
                    'titulo': result['title'],
                    'url': result['href'],
                    'resumo': result['body'][:150] + "..." if len(result['body']) > 150 else result['body'],
                    'fonte': self._extract_domain(result['href'])
                })
            
            return formatted_results
            
        except Exception as e:
            return [{
                'titulo': 'Erro na busca',
                'url': '',
                'resumo': f'Não foi possível realizar a busca: {str(e)}',
                'fonte': 'Sistema'
            }]
    
    def _filter_reliable_sources(self, results: List[Dict]) -> List[Dict]:
        """Filtra fontes confiáveis para dados econômicos"""
        reliable_domains = [
            'bcb.gov.br', 'bancentral.gov.br',  # Banco Central
            'gov.br', '.gov.br',                # Governo
            'ibge.gov.br',                      # IBGE
            'valor.com.br',                     # Valor Econômico
            'g1.globo.com/economia',            # G1 Economia
            'infomoney.com.br',                 # InfoMoney
            'economia.uol.com.br'               # UOL Economia
        ]
        
        reliable_results = []
        for result in results:
            if any(domain in result['href'].lower() for domain in reliable_domains):
                reliable_results.append(result)
        
        return reliable_results
    
    def _extract_selic_value(self, text: str) -> str:
        """Extrai o valor da Selic do texto"""
        # Padrões para encontrar a taxa Selic
        patterns = [
            r'Selic[\s\S]*?(\d+[.,]\d+)%',
            r'taxa Selic[\s\S]*?(\d+[.,]\d+)',
            r'(\d+[.,]\d+)%[\s\S]*?Selic',
            r'juros[\s\S]*?(\d+[.,]\d+)%'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                value = match.group(1).replace(',', '.')
                try:
                    # Valida se é um número válido
                    float(value)
                    return f"{value}%"
                except ValueError:
                    continue
        
        return "Valor não identificado"
    
    def _extract_domain(self, url: str) -> str:
        """Extrai o domínio de uma URL"""
        from urllib.parse import urlparse
        try:
            domain = urlparse(url).netloc
            return domain.replace('www.', '')
        except:
            return url[:30] + "..."
    
    def format_search_response(self, search_data: Dict) -> str:
        """Formata a resposta da busca para exibição"""
        if search_data.get('taxa', '').lower() != 'não encontrada':
            return (
                f"**📊 {search_data['taxa']}**\n\n"
                f"**Fonte:** {search_data['fonte']}\n"
                f"**Descrição:** {search_data['descricao']}\n"
                f"*Atualizado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}*"
            )
        else:
            return "Não foi possível encontrar a taxa Selic atual no momento."