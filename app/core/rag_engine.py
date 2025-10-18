import re
import sys
import os
from typing import List, Tuple, Optional, Dict, Any
import requests

# Corrigir os imports para a estrutura correta
try:
    # Importações relativas dentro do mesmo pacote
    from ..services.payroll_service import PayrollService
    from ..services.formatter import format_currency_brl, format_payment_date
    from ..models.schemas import Evidence
    from ..utils.logger import logger
    print("✅ Todos os imports funcionaram!")
    
except ImportError as e:
    print(f"❌ Erro de import: {e}")
    # Fallback para imports absolutos
    try:
        sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
        from app.services.payroll_service import PayrollService
        from app.services.formatter import format_currency_brl, format_payment_date
        from app.models.schemas import Evidence
        from app.utils.logger import logger
        print("✅ Imports absolutos funcionaram!")
    except ImportError:
        print("⚠️  Usando classes dummy para teste")
        # Criar classes dummy para não quebrar o código
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
        
        class Evidence:
            pass
        
        class Logger:
            def info(self, msg): print(f"INFO: {msg}")
            def error(self, msg): print(f"ERROR: {msg}")
            def warning(self, msg): print(f"WARNING: {msg}")
        
        logger = Logger()


class RAGEngine:
    def __init__(self, payroll_service: PayrollService):
        self.payroll_service = payroll_service
        logger.info("RAGEngine inicializado!")

    def process_query(self, query: str) -> Tuple[str, List[Evidence]]:
        """Processa consulta e retorna resposta e evidências"""
        try:
            logger.info(f"Processando query: '{query}'")
            
            if self._is_web_search_query(query):
                return self._handle_web_search(query)

            employee_name = self._extract_employee_name(query)
            logger.info(f"Funcionário detectado: '{employee_name}'")
            
            # VALIDAÇÃO MELHORADA - Se não encontrou nome específico
            if not employee_name:
                payroll_terms = ['salário', 'salario', 'líquido', 'liquido', 'bruto', 'inss', 'irrf', 'bônus', 'bonus', 'pagamento', 'holerite', 'recebi', 'desconto', 'folha', 'contracheque']
                query_terms = query.lower()
                
                if any(term in query_terms for term in payroll_terms):
                    return self._get_employee_not_found_message(query, "")
                else:
                    return self._handle_general_query_without_employee(query)
            
            # VALIDAÇÃO SE FUNCIONÁRIO EXISTE
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
                return self._handle_bonus_query(employee_name, query)
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
        """Verifica se o funcionário existe na base de dados"""
        try:
            if not employee_name:
                return False
                
            # Normaliza o nome para comparação
            normalized_name = employee_name.lower().strip()
            
            # Lista de funcionários disponíveis
            available_employees = ['ana souza', 'bruno lima']
            
            # Verifica se o nome normalizado está na lista
            return any(normalized_name == emp.lower() for emp in available_employees)
            
        except Exception as e:
            logger.error(f"Erro ao verificar funcionário {employee_name}: {e}")
            return False

    def _get_employee_not_found_message(self, query: str, mentioned_name: str) -> Tuple[str, List[Evidence]]:
        """Retorna mensagem amigável quando funcionário não é encontrado"""
        available_employees = "**Ana Souza** e **Bruno Lima**"
        
        # Mensagem base
        if mentioned_name:
            message = (
                f"❌ **Funcionário não encontrado**\n\n"
                f"**Consulta:** '{query}'\n"
                f"**Funcionário mencionado:** '{mentioned_name}'\n\n"
                f"👥 **Funcionários disponíveis:** {available_employees}\n\n"
            )
        else:
            message = (
                f"❌ **Não consegui identificar o funcionário**\n\n"
                f"**Consulta:** '{query}'\n\n"
                f"👥 **Funcionários disponíveis:** {available_employees}\n\n"
            )
        
        # Sugestões personalizadas
        suggestions = self._get_query_suggestions(query, mentioned_name)
        message += suggestions
        
        # Exemplos de consulta
        message += (
            f"📋 **Exemplos de consulta:**\n"
            f"• `Qual o salário da Ana Souza?`\n"
            f"• `Quanto recebeu Bruno Lima em junho?`\n"
            f"• `Mostre os descontos da Ana`\n"
            f"• `Quando foi pago o salário do Bruno?`"
        )
        
        return message, []

    def _get_query_suggestions(self, query: str, mentioned_name: str) -> str:
        """Retorna sugestões personalizadas baseadas na query"""
        query_lower = query.lower()
        mentioned_lower = mentioned_name.lower()
        
        suggestions = []
        
        # Sugestões baseadas no nome mencionado
        if "jojo" in query_lower or "juju" in query_lower or "jaja" in query_lower:
            suggestions.append("Verifique se o nome está correto - talvez você queira consultar 'Ana Souza' ou 'Bruno Lima'")
        elif "carlos" in query_lower or "maria" in query_lower or "pedro" in query_lower:
            suggestions.append("Estes funcionários não constam no sistema atual")
        elif "silva" in query_lower or "santos" in query_lower:
            suggestions.append("No momento temos apenas Ana Souza e Bruno Lima")
        
        # Sugestões baseadas no padrão de busca
        if len(mentioned_name.split()) == 1 and mentioned_name:
            suggestions.append("Use o nome completo para melhor precisão")
        
        if "salário" in query_lower or "salario" in query_lower or "recebi" in query_lower:
            suggestions.append("Para salários, mencione o nome do funcionário")
        
        if "desconto" in query_lower or "inss" in query_lower or "irrf" in query_lower:
            suggestions.append("Para descontos, use o nome completo do funcionário")
        
        if suggestions:
            return "💡 **Dicas:** " + " | ".join(suggestions) + "\n\n"
        
        return "💡 **Dica:** Mencione o nome completo do funcionário para obter informações precisas.\n\n"

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
    # Extração de nomes e datas - CORRIGIDA
    # -----------------------
    def _extract_date_info(self, query: str) -> Dict[str, Any]:
        date_info = {}
        query_lower = query.lower()
        
        # 1. Procura por padrão MM/YYYY (04/2025)
        month_year_match = re.search(r'(\d{1,2})/(\d{4})', query)
        if month_year_match:
            month = int(month_year_match.group(1))
            year = int(month_year_match.group(2))
            date_info['month'] = month
            date_info['year'] = year
            date_info['competency'] = f"{year}-{month:02d}"
            return date_info
        
        # 2. Procura por padrão YYYY-MM (2025-04)
        competency_match = re.search(r'(\d{4})-(\d{2})', query)
        if competency_match:
            year = int(competency_match.group(1))
            month = int(competency_match.group(2))
            date_info['month'] = month
            date_info['year'] = year
            date_info['competency'] = f"{year}-{month:02d}"
            return date_info
        
        # 3. Procura por ano
        year_match = re.search(r'(20\d{2})', query)
        if year_match:
            date_info['year'] = int(year_match.group(1))
        else:
            date_info['year'] = 2025  # Default

        # 4. Procura por trimestre
        quarter_match = re.search(r'(\d+)[º°]?\s*trimestre', query_lower)
        if quarter_match:
            date_info['quarter'] = int(quarter_match.group(1))

        # 5. Procura por meses por nome
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

        # 6. Se encontrou mês mas não competência, cria a competência
        if 'month' in date_info and 'competency' not in date_info:
            date_info['competency'] = f"{date_info['year']}-{date_info['month']:02d}"

        return date_info

    def _extract_employee_name(self, query: str) -> Optional[str]:
        """Extrai e valida o nome do funcionário da query com melhor detecção"""
        query_lower = query.lower().strip()
        
        # Mapeamento mais abrangente de nomes e variações
        employee_mapping = {
            'ana souza': ['ana souza', 'ana', 'souza', 'ana s', 'a. souza'],
            'bruno lima': ['bruno lima', 'bruno', 'lima', 'bruno l', 'b. lima']
        }
        
        # Remove pontuação para melhor matching
        query_clean = re.sub(r'[^\w\s]', ' ', query_lower)
        query_words = query_clean.split()
        
        # Procura por menções diretas aos funcionários
        for full_name, variations in employee_mapping.items():
            # Verifica o nome completo
            if full_name in query_lower:
                return full_name
            
            # Verifica variações com palavra exata
            for variation in variations:
                if re.search(rf'\b{re.escape(variation)}\b', query_clean):
                    return full_name
        
        # Tentativa adicional: procura por palavras que possam ser nomes
        possible_names = []
        for word in query_words:
            if len(word) > 2:  # Ignora palavras muito curtas
                for full_name, variations in employee_mapping.items():
                    if any(variation.startswith(word.lower()) for variation in variations):
                        possible_names.append(full_name)
        
        # Retorna o primeiro nome possível encontrado (sem duplicatas)
        if possible_names:
            return list(dict.fromkeys(possible_names))[0]
        
        return None

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
    # Handlers de folha de pagamento - CORRIGIDOS
    # -----------------------
    def _handle_net_pay_specific(self, employee_name: str, date_info: Dict, query: str) -> Tuple[str, List[Evidence]]:
        try:
            # Se tem competência específica, busca por ela
            if 'competency' in date_info:
                records = self.payroll_service.search_by_competency(date_info['competency'], employee_name)
            else:
                # Se não tem competência, usa mês/ano ou busca último registro
                competency = f"{date_info['year']}-{date_info.get('month',1):02d}"
                records = self.payroll_service.search_by_competency(competency, employee_name)
            
            if records.empty:
                period_desc = self._get_period_description(date_info)
                return f"Não foram encontrados registros para {employee_name} {period_desc}.", []

            record = records.iloc[0]
            net_pay = record['net_pay']
            month_year = record['competency']
            evidence = self.payroll_service.to_evidence(records)

            response = f"**{employee_name}** recebeu {format_currency_brl(net_pay)} em {self._format_month_year(month_year)}."
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
            response = f"O total líquido de **{employee_name}** {period_description} foi {format_currency_brl(total_net)}."
            return response, evidence
        except Exception as e:
            return f"❌ Erro ao processar consulta agregada: {e}", []

    def _handle_payment_date_query(self, employee_name: str, date_info: Dict, query: str) -> Tuple[str, List[Evidence]]:
        try:
            # Se tem competência específica, busca por ela
            if 'competency' in date_info:
                records = self.payroll_service.search_by_competency(date_info['competency'], employee_name)
                if records.empty:
                    period_desc = self._get_period_description(date_info)
                    return f"Não foram encontrados registros de pagamento para {employee_name} em {period_desc}.", []
                record = records.iloc[0]  # Pega o primeiro (e único) registro da competência
            else:
                # Se não tem competência, busca o último registro
                records = self.payroll_service.get_employee_records(employee_name)
                if records.empty:
                    return f"Não foram encontrados registros para {employee_name}.", []
                record = records.iloc[-1]  # Pega o último registro
            
            payment_date = format_payment_date(record['payment_date'])
            net_pay = record['net_pay']
            month_year = record['competency']
            evidence = self.payroll_service.to_evidence(records.tail(1))
            
            response = f"O pagamento de **{employee_name}** referente a {self._format_month_year(month_year)} foi em **{payment_date}** no valor líquido de {format_currency_brl(net_pay)}."
            return response, evidence
            
        except Exception as e:
            logger.error(f"Erro ao processar consulta de data de pagamento: {e}")
            return f"❌ Erro ao buscar data de pagamento: {e}", []

    def _handle_deduction_query(self, employee_name: str, date_info: Dict, query: str) -> Tuple[str, List[Evidence]]:
        deduction_type = 'INSS' if 'inss' in query.lower() else 'IRRF'
        field = 'deductions_inss' if deduction_type=='INSS' else 'deductions_irrf'
        
        # Se tem competência específica, busca por ela
        if 'competency' in date_info:
            records = self.payroll_service.search_by_competency(date_info['competency'], employee_name)
        else:
            records = self.payroll_service.get_employee_records(employee_name)
            
        if records.empty:
            period_desc = self._get_period_description(date_info)
            return f"Não foram encontrados registros de {deduction_type} para {employee_name} {period_desc}.", []
        
        record = records.iloc[-1] if 'competency' not in date_info else records.iloc[0]
        value = record[field]
        month_year = record['competency']
        evidence = self.payroll_service.to_evidence(records.tail(1))
        response = f"O desconto de **{deduction_type}** de **{employee_name}** em {self._format_month_year(month_year)} foi {format_currency_brl(value)}."
        return response, evidence

    def _handle_bonus_query(self, employee_name: str, query: str) -> Tuple[str, List[Evidence]]:
        records = self.payroll_service.find_max_bonus(employee_name)
        if records.empty:
            return f"Não foram encontrados registros de bônus para {employee_name}.", []
        max_bonus = records.iloc[0]['bonus']
        month_year = records.iloc[0]['competency']
        evidence = self.payroll_service.to_evidence(records)
        response = f"O maior bônus de **{employee_name}** foi {format_currency_brl(max_bonus)} em {self._format_month_year(month_year)}."
        return response, evidence

    def _handle_general_query(self, employee_name: str, query: str) -> Tuple[str, List[Evidence]]:
        records = self.payroll_service.get_employee_records(employee_name)
        if records.empty:
            return f"Não foram encontrados registros para o funcionário {employee_name}.", []
        latest = records.iloc[-1]
        evidence = self.payroll_service.to_evidence(records.head(3))
        response = f"Encontrei {len(records)} registros para **{employee_name}**. Último registro: {self._format_month_year(latest['competency'])} com salário líquido de {format_currency_brl(latest['net_pay'])}."
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
                response = "**📊 Informações Gerais dos Funcionários:**\n\n" + "\n\n".join(responses)
                response += "\n\n💡 **Para informações específicas, mencione o nome do funcionário.**"
                return response, all_evidence
            else:
                return "Não foram encontrados registros de funcionários. Os funcionários disponíveis são: Ana Souza e Bruno Lima.", []
                
        except Exception as e:
            return f"Erro ao processar consulta geral: {e}", []

    # -----------------------
    # Helpers - CORRIGIDOS
    # -----------------------
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

    def _get_period_description(self, date_info: Dict) -> str:
        """Retorna descrição amigável do período - CORRIGIDA"""
        try:
            if 'competency' in date_info:
                return f"em {self._format_month_year(date_info['competency'])}"
            elif 'month' in date_info:
                competency = f"{date_info['year']}-{date_info['month']:02d}"
                return f"em {self._format_month_year(competency)}"
            elif 'quarter' in date_info:
                return f"no {date_info['quarter']}º trimestre de {date_info['year']}"
            else:
                return f"em {date_info['year']}"
        except Exception as e:
            logger.error(f"Erro ao gerar descrição do período: {e}")
            return "no período solicitado"