import re
import sys
import os
from typing import List, Tuple, Optional, Dict, Any
import requests

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from app.services.payroll_service import PayrollService
from app.services.formatter import format_currency_brl, format_payment_date
from app.models.schemas import Evidence
from app.utils.logger import logger


class RAGEngine:
    def __init__(self, payroll_service: PayrollService):
        self.payroll_service = payroll_service

    def process_query(self, query: str) -> Tuple[str, List[Evidence]]:
        """Processa consulta e retorna resposta e evidências"""
        if self._is_web_search_query(query):
            return self._handle_web_search(query)

        employee_name = self._extract_employee_name(query)
        
        # VALIDAÇÃO MELHORADA - Se não encontrou nome específico
        if not employee_name:
            # Tenta identificar se a pergunta é sobre folha sem mencionar funcionário
            payroll_terms = ['salário', 'líquido', 'bruto', 'inss', 'irrf', 'bônus', 'pagamento', 'holerite', 'recebi', 'desconto']
            query_terms = query.lower().split()
            
            if any(term in query_terms for term in payroll_terms):
                return "Não consegui localizar na minha base de conhecimento esse funcionário. Exemplos: 'Ana Souza' ou 'Bruno Lima'.", []
            else:
                # Se não tem termos de folha, trata como consulta geral
                return self._handle_general_query_without_employee(query)
        
        # VALIDAÇÃO SE FUNCIONÁRIO EXISTE
        if not self._employee_exists(employee_name):
            available_employees = "Ana Souza e Bruno Lima"
            return f"❌ Funcionário '{employee_name}' não encontrado. Os funcionários disponíveis são: {available_employees}.", []

        date_info = self._extract_date_info(query)
        query_type = self._classify_query(query)

        logger.info(
            f"Query processada - Funcionário: {employee_name}, Data: {date_info}, Tipo: {query_type}"
        )

        # Roteia para o tipo de consulta
        if query_type == "net_pay_specific":
            return self._handle_net_pay_specific(employee_name, date_info, query)
        elif query_type == "net_pay_aggregate":
            return self._handle_net_pay_aggregate(employee_name, date_info, query)
        elif query_type == "deduction_query":
            return self._handle_deduction_query(employee_name, date_info, query)
        elif query_type == "bonus_query":
            return self._handle_bonus_query(employee_name, query)
        elif query_type == "payment_date_query":
            return self._handle_payment_date_query(employee_name, date_info, query)
        else:
            return self._handle_general_query(employee_name, query)

    # -----------------------
    # Validações e helpers
    # -----------------------
    def _employee_exists(self, employee_name: str) -> bool:
        """Verifica se o funcionário existe na base de dados"""
        try:
            # Normaliza o nome para comparação
            normalized_name = employee_name.lower().strip()
            
            # Lista de funcionários disponíveis
            available_employees = ['ana souza', 'bruno lima']
            
            # Verifica se o nome normalizado está na lista
            return any(normalized_name == emp.lower() for emp in available_employees)
            
        except Exception as e:
            logger.error(f"Erro ao verificar funcionário {employee_name}: {e}")
            return False

    def _is_web_search_query(self, query: str) -> bool:
        query_lower = query.lower()
        web_terms = ['selic', 'taxa atual', 'notícia', 'busca na web', 'internet', 'cite a fonte']
        return any(term in query_lower for term in web_terms)

    # -----------------------
    # Web search (Selic)
    # -----------------------
    def _handle_web_search(self, query: str) -> Tuple[str, List[Evidence]]:
        query_lower = query.lower()
        if any(term in query_lower for term in ['selic', 'taxa selic', 'juros básicos']):
            return self._fetch_selic_web()
        else:
            return "Busca na web disponível apenas para taxa Selic no momento.", []

    def _fetch_selic_web(self) -> Tuple[str, List[Evidence]]:
        api_key = os.getenv("SERPER_API_KEY")
        if not api_key:
            return "❌ Chave SERPER_API_KEY não configurada no arquivo .env", []

        try:
            url = "https://api.serper.dev/search"
            headers = {"X-API-KEY": api_key}
            payload = {"q": "taxa Selic atual site:bcb.gov.br", "num": 1}

            resp = requests.post(url, json=payload, headers=headers, timeout=10)
            resp.raise_for_status()
            data = resp.json()

            snippet = data.get("organic", [{}])[0].get("snippet", "Informação não encontrada")
            link = data.get("organic", [{}])[0].get("link", "https://www.bcb.gov.br")

            response = f"💰 **Taxa Selic atual:** {snippet}\n\n🔗 **Fonte oficial:** {link}"
            return response, []
        except Exception as e:
            return f"❌ Erro ao buscar taxa Selic na web: {e}", []

    # -----------------------
    # Extração de nomes e datas
    # -----------------------
    def _extract_employee_name(self, query: str) -> Optional[str]:
        """Extrai e valida o nome do funcionário da query"""
        query_lower = query.lower().strip()
        
        # Mapeamento de nomes e variações
        employee_mapping = {
            'ana souza': ['ana souza', 'ana', 'souza'],
            'bruno lima': ['bruno lima', 'bruno', 'lima']
        }
        
        # Remove pontuação para melhor matching
        query_clean = re.sub(r'[^\w\s]', ' ', query_lower)
        
        # Procura por menções diretas aos funcionários
        for full_name, variations in employee_mapping.items():
            # Verifica o nome completo
            if full_name in query_lower:
                return full_name
            
            # Verifica variações
            for variation in variations:
                if re.search(rf'\b{variation}\b', query_clean):
                    return full_name
        
        return None

    def _extract_date_info(self, query: str) -> Dict[str, Any]:
        date_info = {}
        query_lower = query.lower()
        year_match = re.search(r'(20\d{2})', query)
        date_info['year'] = int(year_match.group(1)) if year_match else 2025

        quarter_match = re.search(r'(\d+)[º°]?\s*trimestre', query_lower)
        if quarter_match:
            date_info['quarter'] = int(quarter_match.group(1))

        month_patterns = [
            (r'janeiro|jan', 1), (r'fevereiro|fev', 2), (r'março|mar', 3),
            (r'abril|abr', 4), (r'maio|mai', 5), (r'junho|jun', 6),
            (r'julho|jul', 7), (r'agosto|ago', 8), (r'setembro|set', 9),
            (r'outubro|out', 10), (r'novembro|nov', 11), (r'dezembro|dez', 12)
        ]
        for pattern, month_num in month_patterns:
            if re.search(pattern, query_lower):
                date_info['month'] = month_num
                break

        competency_match = re.search(r'(\d{4}-\d{2})', query)
        if competency_match:
            date_info['competency'] = competency_match.group(1)
        return date_info

    def _classify_query(self, query: str) -> str:
        query_lower = query.lower()
        if any(term in query_lower for term in ['quanto recebi', 'salário líquido', 'líquido', 'total líquido', 'recebi']):
            if any(term in query_lower for term in ['trimestre', 'total', 'soma']):
                return "net_pay_aggregate"
            return "net_pay_specific"
        elif any(term in query_lower for term in ['desconto', 'inss', 'irrf']):
            return "deduction_query"
        elif any(term in query_lower for term in ['bônus', 'bonus', 'maior bônus']):
            return "bonus_query"
        elif any(term in query_lower for term in ['quando foi pago', 'data de pagamento', 'pagamento']):
            return "payment_date_query"
        else:
            return "general_query"

    # -----------------------
    # Handlers de folha de pagamento
    # -----------------------
    def _handle_net_pay_specific(self, employee_name: str, date_info: Dict, query: str) -> Tuple[str, List[Evidence]]:
        try:
            competency = date_info.get('competency') or f"{date_info['year']}-{date_info.get('month',1):02d}"
            records = self.payroll_service.search_by_competency(competency, employee_name)
            if records.empty:
                return f"Não foram encontrados registros para {employee_name} no período especificado.", []

            net_pay = records.iloc[0]['net_pay']
            month_year = records.iloc[0]['competency']
            evidence = self.payroll_service.to_evidence(records)

            response = f"{employee_name} recebeu {format_currency_brl(net_pay)} em {self._format_month_year(month_year)}."
            return response, evidence
        except Exception as e:
            return f"❌ Erro ao processar consulta de salário: {e}", []

    def _handle_net_pay_aggregate(self, employee_name: str, date_info: Dict, query: str) -> Tuple[str, List[Evidence]]:
        try:
            # CORREÇÃO: Filtrar por trimestre quando especificado
            if 'quarter' in date_info:
                records = self._get_quarter_records(employee_name, date_info['quarter'], date_info['year'])
                period_description = f"no {date_info['quarter']}º trimestre de {date_info['year']}"
            else:
                # Se não há trimestre, soma todos os registros (comportamento original)
                records = self.payroll_service.get_employee_records(employee_name)
                period_description = "no período total"
            
            if records.empty:
                return f"Não foram encontrados registros para {employee_name} {period_description}.", []
            
            total_net = records['net_pay'].sum()
            evidence = self.payroll_service.to_evidence(records)
            response = f"O total líquido de {employee_name} {period_description} foi {format_currency_brl(total_net)}."
            return response, evidence
        except Exception as e:
            return f"❌ Erro ao processar consulta agregada: {e}", []

    def _get_quarter_records(self, employee_name: str, quarter: int, year: int) -> Any:
        """Filtra registros por trimestre específico"""
        try:
            # Define os meses do trimestre
            quarter_months = {
                1: [1, 2, 3],   # 1º trimestre: jan, fev, mar
                2: [4, 5, 6],   # 2º trimestre: abr, mai, jun
                3: [7, 8, 9],   # 3º trimestre: jul, ago, set
                4: [10, 11, 12] # 4º trimestre: out, nov, dez
            }
            
            months = quarter_months.get(quarter, [])
            if not months:
                return self.payroll_service.get_empty_dataframe()
            
            # Busca todos os registros do funcionário
            all_records = self.payroll_service.get_employee_records(employee_name)
            if all_records.empty:
                return all_records
            
            # Filtra por ano e meses do trimestre
            quarter_records = all_records[
                all_records['competency'].str.startswith(str(year)) &
                all_records['competency'].str.extract(r'(\d{4})-(\d{2})')[1].astype(int).isin(months)
            ]
            
            return quarter_records
            
        except Exception as e:
            logger.error(f"Erro ao filtrar registros do trimestre: {e}")
            return self.payroll_service.get_empty_dataframe()

    def _handle_deduction_query(self, employee_name: str, date_info: Dict, query: str) -> Tuple[str, List[Evidence]]:
        deduction_type = 'INSS' if 'inss' in query.lower() else 'IRRF'
        field = 'deductions_inss' if deduction_type=='INSS' else 'deductions_irrf'
        records = self.payroll_service.get_employee_records(employee_name)
        if records.empty:
            return f"Não foram encontrados registros de {deduction_type} para {employee_name}.", []
        value = records.iloc[-1][field]
        month_year = records.iloc[-1]['competency']
        evidence = self.payroll_service.to_evidence(records.tail(1))
        response = f"O desconto de {deduction_type} de {employee_name} em {self._format_month_year(month_year)} foi {format_currency_brl(value)}."
        return response, evidence

    def _handle_bonus_query(self, employee_name: str, query: str) -> Tuple[str, List[Evidence]]:
        records = self.payroll_service.find_max_bonus(employee_name)
        if records.empty:
            return f"Não foram encontrados registros de bônus para {employee_name}.", []
        max_bonus = records.iloc[0]['bonus']
        month_year = records.iloc[0]['competency']
        evidence = self.payroll_service.to_evidence(records)
        response = f"O maior bônus de {employee_name} foi {format_currency_brl(max_bonus)} em {self._format_month_year(month_year)}."
        return response, evidence

    def _handle_payment_date_query(self, employee_name: str, date_info: Dict, query: str) -> Tuple[str, List[Evidence]]:
        records = self.payroll_service.get_employee_records(employee_name)
        if records.empty:
            return f"Não foram encontrados registros para {employee_name}.", []
        record = records.iloc[-1]
        payment_date = format_payment_date(record['payment_date'])
        net_pay = record['net_pay']
        month_year = record['competency']
        evidence = self.payroll_service.to_evidence(records.tail(1))
        response = f"O pagamento de {employee_name} referente a {self._format_month_year(month_year)} foi em {payment_date} no valor líquido de {format_currency_brl(net_pay)}."
        return response, evidence

    def _handle_general_query(self, employee_name: str, query: str) -> Tuple[str, List[Evidence]]:
        records = self.payroll_service.get_employee_records(employee_name)
        if records.empty:
            return f"Não foram encontrados registros para o funcionário {employee_name}.", []
        latest = records.iloc[-1]
        evidence = self.payroll_service.to_evidence(records.head(3))
        response = f"Encontrei {len(records)} registros para {employee_name}. Último registro: {self._format_month_year(latest['competency'])} com salário líquido de {format_currency_brl(latest['net_pay'])}."
        return response, evidence

    def _handle_general_query_without_employee(self, query: str) -> Tuple[str, List[Evidence]]:
        """Lida com consultas que não mencionam funcionário específico"""
        try:
            # Tenta buscar informações gerais
            all_employees = ['Ana Souza', 'Bruno Lima']
            all_evidence = []
            responses = []
            
            for employee in all_employees:
                try:
                    # Busca os registros do funcionário
                    records = self.payroll_service.get_employee_records(employee)
                    if not records.empty:
                        latest = records.iloc[-1]
                        responses.append(
                            f"**{employee}:** Último salário: {format_currency_brl(latest['net_pay'])} "
                            f"em {self._format_month_year(latest['competency'])}"
                        )
                        all_evidence.extend(self.payroll_service.to_evidence(records.tail(1)))
                except Exception as e:
                    logger.warning(f"Erro ao processar {employee}: {e}")
                    continue
            
            if responses:
                response = "**Informações Gerais dos Funcionários:**\n\n" + "\n\n".join(responses)
                response += "\n\n💡 *Para informações específicas, mencione o nome do funcionário.*"
                return response, all_evidence
            else:
                return "Não foram encontrados registros de funcionários. Os funcionários disponíveis são: Ana Souza e Bruno Lima.", []
                
        except Exception as e:
            return f"Erro ao processar consulta geral: {e}", []

    # -----------------------
    # Helpers
    # -----------------------
    def _format_month_year(self, competency: str) -> str:
        try:
            year, month = competency.split('-')
            month_names = [
                'janeiro', 'fevereiro', 'março', 'abril', 'maio', 'junho',
                'julho', 'agosto', 'setembro', 'outubro', 'novembro', 'dezembro'
            ]
            return f"{month_names[int(month)-1]} de {year}"
        except:
            return competency
        