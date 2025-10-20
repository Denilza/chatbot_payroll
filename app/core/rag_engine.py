import re
import sys
import os
from typing import List, Tuple, Optional, Dict, Any
import requests

# ================================
# Imports locais com fallback
# ================================
try:
    from ..services.payroll_service import PayrollService
    from ..services.formatter import format_currency_brl, format_payment_date
    from ..models.schemas import Evidence
    from ...logger import logger
except ImportError:
    sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
    try:
        from app.services.payroll_service import PayrollService
        from app.services.formatter import format_currency_brl, format_payment_date
        from app.models.schemas import Evidence
        from logger import logger
    except ImportError:
        class PayrollService:
            def get_employee_records(self, name): 
                return type('obj', (object,), {'empty': True, 'iloc': []})()
            def search_by_competency(self, comp, name): 
                return type('obj', (object,), {'empty': True, 'iloc': []})()
            def find_max_bonus(self, name): 
                return type('obj', (object,), {'empty': True, 'iloc': []})()
            def to_evidence(self, records): return []
            def get_empty_dataframe(self): 
                return type('obj', (object,), {'empty': True})()
        
        def format_currency_brl(value): return f"R$ {value:,.2f}"
        def format_payment_date(date): return date
        
        class Evidence: pass
        
        class Logger:
            def info(self, msg): print(f"INFO: {msg}")
            def error(self, msg): print(f"ERROR: {msg}")
            def warning(self, msg): print(f"WARNING: {msg}")
        
        logger = Logger()

# ================================
# RAG Engine
# ================================
class RAGEngine:
    def __init__(self, payroll_service: PayrollService):
        self.payroll_service = payroll_service
        logger.info("RAGEngine inicializado!")

    def process_query(self, query: str) -> Tuple[str, List[Evidence]]:
        try:
            logger.info(f"Processando query: '{query}'")
            
            if self._is_web_search_query(query):
                return self._handle_web_search(query)

            employee_name = self._extract_employee_name(query)
            logger.info(f"Funcionário detectado: '{employee_name}'")
            
            # Se não encontrou funcionário
            if not employee_name:
                payroll_terms = ['salário', 'salario', 'líquido', 'liquido', 'bruto', 'inss', 'irrf', 'bônus', 'bonus', 'pagamento', 'holerite', 'recebi', 'desconto', 'folha', 'contracheque']
                query_terms = query.lower()
                if any(term in query_terms for term in payroll_terms):
                    return self._get_employee_not_found_message(query, "")
                else:
                    return self._handle_general_query_without_employee(query)
            
            if not self._employee_exists(employee_name):
                return self._get_employee_not_found_message(query, employee_name)

            date_info = self._extract_date_info(query)
            logger.info(f"Data info: {date_info}")
            
            query_type = self._classify_query(query)
            logger.info(f"Tipo de query: {query_type}")

            # Roteia para o tipo de consulta
            if query_type == "net_pay_specific":
                return self._handle_net_pay_specific(employee_name, date_info, query)
            elif query_type == "net_pay_aggregate":
                return self._handle_net_pay_aggregate(employee_name, date_info, query)
            elif query_type == "deduction_query":
                return self._handle_deduction_query(employee_name, date_info, query)
            elif query_type == "bonus_query":
                return self._handle_bonus_query(employee_name, date_info, query)
            elif query_type == "payment_date_query":
                return self._handle_payment_date_query(employee_name, date_info, query)
            else:
                return self._handle_general_query(employee_name, query)
                
        except Exception as e:
            error_msg = f"❌ Erro crítico no processamento: {e}"
            logger.error(error_msg)
            return error_msg, []

    # -----------------------
    # Validações e helpers
    # -----------------------
    def _employee_exists(self, employee_name: str) -> bool:
        if not employee_name:
            return False
        available_employees = ['ana souza', 'bruno lima']
        return any(employee_name.lower() == emp.lower() for emp in available_employees)

    def _get_employee_not_found_message(self, query: str, mentioned_name: str) -> Tuple[str, List[Evidence]]:
        available_employees = "**Ana Souza** e **Bruno Lima**"
        message = f"❌ **Funcionário não encontrado**\n\nConsulta: '{query}'\n"
        if mentioned_name:
            message += f"Funcionário mencionado: '{mentioned_name}'\n\n"
        message += f"👥 Funcionários disponíveis: {available_employees}\n\n"
        message += "💡 **Dica:** Use o nome completo do funcionário para obter informações precisas.\n\n"
        message += "📋 Exemplos de consulta:\n• `Qual o salário da Ana Souza?`\n• `Quanto recebeu Bruno Lima em junho?`\n• `Mostre os descontos da Ana`\n• `Quando foi pago o salário do Bruno?`"
        return message, []

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
    # Extração de datas
    # -----------------------
    def _extract_date_info(self, query: str) -> Dict[str, Any]:
        date_info = {}
        query_lower = query.lower()
        month_year_match = re.search(r'(\d{1,2})/(\d{4})', query)
        if month_year_match:
            month = int(month_year_match.group(1))
            year = int(month_year_match.group(2))
            date_info['month'] = month
            date_info['year'] = year
            date_info['competency'] = f"{year}-{month:02d}"
            return date_info
        competency_match = re.search(r'(\d{4})-(\d{2})', query)
        if competency_match:
            year = int(competency_match.group(1))
            month = int(competency_match.group(2))
            date_info['month'] = month
            date_info['year'] = year
            date_info['competency'] = f"{year}-{month:02d}"
            return date_info
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
        if 'month' in date_info and 'competency' not in date_info:
            date_info['competency'] = f"{date_info['year']}-{date_info['month']:02d}"
        return date_info

    # -----------------------
    # Extração de funcionários
    # -----------------------
    def _extract_employee_name(self, query: str) -> Optional[str]:
        query_lower = query.lower()
        employee_mapping = {
            'ana souza': ['ana souza', 'ana', 'souza', 'ana s', 'a. souza'],
            'bruno lima': ['bruno lima', 'bruno', 'lima', 'bruno l', 'b. lima']
        }
        query_clean = re.sub(r'[^\w\s]', ' ', query)
        query_clean_lower = query_clean.lower()
        for full_name, variations in employee_mapping.items():
            for variation in variations:
                if re.search(rf'\b{re.escape(variation)}\b', query_clean_lower):
                    match = re.search(rf'\b{variation}\b', query_clean, re.IGNORECASE)
                    if match:
                        return full_name  # Retorna nome completo
        return None

    # -----------------------
    # Classificação de query
    # -----------------------
    def _classify_query(self, query: str) -> str:
        query_lower = query.lower()
        if any(term in query_lower for term in ['quanto recebi', 'salário líquido', 'salario liquido', 'líquido', 'liquido', 'total líquido', 'total liquido', 'recebi']):
            if any(term in query_lower for term in ['trimestre', 'total', 'soma']):
                return "net_pay_aggregate"
            return "net_pay_specific"
        elif any(term in query_lower for term in ['desconto', 'inss', 'irrf']):
            return "deduction_query"
        elif any(term in query_lower for term in ['bônus', 'bonus', 'maior bônus', 'maior bonus']):
            return "bonus_query"
        elif any(term in query_lower for term in ['quando foi pago', 'data de pagamento', 'pagamento', 'pago']):
            return "payment_date_query"
        else:
            return "general_query"

    # -----------------------
    # Handlers atualizados (respeitando competência)
    # -----------------------
    def _handle_net_pay_specific(self, employee_name: str, date_info: Dict, query: str) -> Tuple[str, List[Evidence]]:
        try:
            records = self.payroll_service.get_employee_records(employee_name)
            if 'competency' in date_info:
                records = records[records['competency'] == date_info['competency']]
            if records.empty:
                period_desc = self._get_period_description(date_info)
                return f"Não foram encontrados registros para {employee_name} {period_desc}.", []
            record = records.iloc[0]
            evidence = self.payroll_service.to_evidence(records)
            response = f"**{employee_name}** recebeu {format_currency_brl(record['net_pay'])} em {self._format_month_year(record['competency'])}."
            return response, evidence
        except Exception as e:
            return f"❌ Erro ao processar consulta de salário: {e}", []

    def _handle_net_pay_aggregate(self, employee_name: str, date_info: Dict, query: str) -> Tuple[str, List[Evidence]]:
        try:
            if 'quarter' in date_info:
                records = self._get_quarter_records(employee_name, date_info['quarter'], date_info['year'])
                period_desc = f"no {date_info['quarter']}º trimestre de {date_info['year']}"
            elif 'month' in date_info:
                records = self.payroll_service.get_employee_records(employee_name)
                records = records[records['competency'] == date_info['competency']]
                period_desc = self._get_period_description(date_info)
            else:
                records = self.payroll_service.get_employee_records(employee_name)
                period_desc = "no período total"
            if records.empty:
                return f"Não foram encontrados registros para {employee_name} {period_desc}.", []
            total_net = records['net_pay'].sum()
            evidence = self.payroll_service.to_evidence(records)
            response = f"O total líquido de **{employee_name}** {period_desc} foi {format_currency_brl(total_net)}."
            return response, evidence
        except Exception as e:
            return f"❌ Erro ao processar consulta agregada: {e}", []

    def _handle_payment_date_query(self, employee_name: str, date_info: Dict, query: str) -> Tuple[str, List[Evidence]]:
        try:
            records = self.payroll_service.get_employee_records(employee_name)
            if 'competency' in date_info:
                records = records[records['competency'] == date_info['competency']]
            if records.empty:
                period_desc = self._get_period_description(date_info)
                return f"Não foram encontrados registros de pagamento para {employee_name} {period_desc}.", []
            record = records.iloc[0]
            evidence = self.payroll_service.to_evidence(records)
            response = f"O salário de **{employee_name}** foi pago em {format_payment_date(record['payment_date'])}, e o líquido recebido foi {format_currency_brl(record['net_pay'])}."
            return response, evidence
        except Exception as e:
            return f"❌ Erro ao processar consulta de data de pagamento: {e}", []

    def _handle_deduction_query(self, employee_name: str, date_info: Dict, query: str) -> Tuple[str, List[Evidence]]:
        deduction_type = 'INSS' if 'inss' in query.lower() else 'IRRF'
        field = 'deductions_inss' if deduction_type=='INSS' else 'deductions_irrf'
        records = self.payroll_service.get_employee_records(employee_name)
        if 'competency' in date_info:
            records = records[records['competency'] == date_info['competency']]
        if records.empty:
            period_desc = self._get_period_description(date_info)
            return f"Não foram encontrados registros de {deduction_type} para {employee_name} {period_desc}.", []
        record = records.iloc[0]
        evidence = self.payroll_service.to_evidence(records)
        response = f"O desconto de **{deduction_type}** de **{employee_name}** em {self._format_month_year(record['competency'])} foi {format_currency_brl(record[field])}."
        return response, evidence

    def _handle_bonus_query(self, employee_name: str, date_info: Dict, query: str) -> Tuple[str, List[Evidence]]:
        records = self.payroll_service.find_max_bonus(employee_name)
        if records.empty:
            return f"Não foram encontrados registros de bônus para {employee_name}.", []
        max_record = records.iloc[0]
        evidence = self.payroll_service.to_evidence(records)
        response = f"O maior bônus de **{employee_name}** foi {format_currency_brl(max_record['bonus'])} em {self._format_month_year(max_record['competency'])}."
        return response, evidence

    def _handle_general_query(self, employee_name: str, query: str) -> Tuple[str, List[Evidence]]:
        records = self.payroll_service.get_employee_records(employee_name)
        if records.empty:
            return f"Não foram encontrados registros para o funcionário {employee_name}.", []
        latest = records.iloc[-1]
        evidence = self.payroll_service.to_evidence(records.head(3))
        response = f"Encontrei {len(records)} registros para **{employee_name}**. O mais recente é {self._format_month_year(latest['competency'])}, líquido {format_currency_brl(latest['net_pay'])}."
        return response, evidence

    def _handle_general_query_without_employee(self, query: str) -> Tuple[str, List[Evidence]]:
        return "Não foi possível identificar o funcionário na consulta. Por favor, utilize o nome completo.", []

    # -----------------------
    # Helpers adicionais
    # -----------------------
    def _format_month_year(self, competency: str) -> str:
        year, month = map(int, competency.split('-'))
        months_pt = ["Janeiro","Fevereiro","Março","Abril","Maio","Junho","Julho","Agosto","Setembro","Outubro","Novembro","Dezembro"]
        return f"{months_pt[month-1]}/{year}"

    def _get_period_description(self, date_info: Dict[str,int]) -> str:
        if 'month' in date_info:
            return f"em {self._format_month_year(date_info['competency'])}"
        elif 'quarter' in date_info:
            return f"no {date_info['quarter']}º trimestre de {date_info['year']}"
        elif 'year' in date_info:
            return f"no ano de {date_info['year']}"
        return ""

    def _get_quarter_records(self, employee_name: str, quarter: int, year: int):
        records = self.payroll_service.get_employee_records(employee_name)
        if records.empty:
            return records
        month_start = 3*(quarter-1)+1
        month_end = month_start+2
        records['month_int'] = records['competency'].str[5:7].astype(int)
        records['year_int'] = records['competency'].str[:4].astype(int)
        quarter_records = records[(records['month_int']>=month_start) & (records['month_int']<=month_end) & (records['year_int']==year)]
        return quarter_records
