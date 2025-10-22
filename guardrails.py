import re
from typing import Tuple, Dict, Any
from datetime import datetime
import logging

logger = logging.getLogger('chatbot_payroll')


class Guardrails:
    def __init__(self):
        # Lista de termos sensíveis que o chatbot não deve responder
        self.sensitive_topics = [
            'violência', 'conteúdo adulto', 'sexo', 'sexual',
            'droga', 'ilegal', 'hackear', 'senha', 'password',
            'cartão de crédito', 'cpf', 'conta bancária'
        ]
        
        # Domínios e nomes de funcionários permitidos
        self.allowed_domains = [
            'folha de pagamento', 'salário', 'salario', 'desconto', 'bônus',
            'funcionário', 'funcionario', 'Ana Souza', 'Bruno Lima',
            'selic', 'taxa selic', 'juros', 'economia'
        ]

        # Nomes de funcionários (para extração precisa)
        self.known_names = ['Ana Souza', 'Bruno Lima']
        
        self.max_input_length = 500
        logger.info("🛡️ Guardrails inicializados")

    # ---------------------------------------------------------------
    # Função que extrai o nome do funcionário preservando a capitalização original
    # ---------------------------------------------------------------
    def extract_employee_name(self, message: str) -> str | None:
        """
        Retorna o nome do funcionário conforme digitado no input (mantendo maiúsculas/minúsculas).
        """
        for name in self.known_names:
            match = re.search(rf"\b{name}\b", message, re.IGNORECASE)
            if match:
                return match.group(0)  # Retorna o nome exatamente como o usuário digitou
        return None

    # ---------------------------------------------------------------
    # Função que verifica se a pergunta é relevante (folha de pagamento)
    # ---------------------------------------------------------------
    def _is_relevant_question(self, message: str) -> bool:
        """Verifica se a pergunta é relevante ao contexto de folha de pagamento."""
        keywords = [
            "salário", "pagamento", "folha", "holerite", "contracheque",
            "inss", "irrf", "bruto", "líquido", "bonus", "bônus",
            "ana souza", "bruno lima", "funcionário", "colaborador",
            "quanto recebi", "quando pagou", "maio", "junho", "julho", "2025", "2024"
        ]
        return any(k in message.lower() for k in keywords)

    # ---------------------------------------------------------------
    # Função principal de validação do input
    # ---------------------------------------------------------------
    def validate_input(self, user_input: str) -> Tuple[bool, str, Dict[str, Any]]:
        """Valida o texto inserido pelo usuário com base em regras pré-definidas."""
        user_input_clean = user_input.lower()
        validation_metadata = {
            'failed_checks': [],
            'input_length': len(user_input),
            'timestamp': datetime.now().isoformat(),
            'original_input': user_input,
            'validation_input': user_input_clean
        }

        # Verifica tamanho máximo
        if len(user_input) > self.max_input_length:
            validation_metadata['failed_checks'].append('max_length')
            logger.warning(f"🚫 Input muito longo ({len(user_input)} chars)")
            return False, f"Pergunta muito longa. Máximo permitido: {self.max_input_length} caracteres.", validation_metadata

        # Verifica se o tema é relevante
        if not self._is_relevant_question(user_input):
            validation_metadata['failed_checks'].append('domain')
            logger.warning(f"🚫 Pergunta fora de contexto: {user_input}")
            return False, "Por favor, faça perguntas sobre folha de pagamento ou funcionários", validation_metadata

        # Verifica conteúdo sensível
        for topic in self.sensitive_topics:
            if topic in user_input_clean:
                validation_metadata['failed_checks'].append('sensitive_content')
                logger.warning(f"🚫 Conteúdo sensível detectado: {topic}")
                return False, "Tópico sensível detectado. Não posso ajudar com isso.", validation_metadata

        # Extrai o nome do funcionário conforme digitado
        employee_name = self.extract_employee_name(user_input)
        if employee_name:
            validation_metadata['employee_name'] = employee_name
            logger.info(f"👤 Funcionário identificado: {employee_name}")

        logger.info("✅ Validação bem-sucedida")
        return True, "Validação bem-sucedida", validation_metadata


# ---------------------------------------------------------------
# Exemplo de uso (teste rápido)
# ---------------------------------------------------------------
if __name__ == "__main__":
    guardrails = Guardrails()

    pergunta = "Quanto recebi (líquido) em maio/2025? (Ana Souza)"
    valido, msg, meta = guardrails.validate_input(pergunta)

    print(f"✔️ Válido: {valido}")
    print(f"Mensagem: {msg}")
    print("Metadados:")
    for k, v in meta.items():
        print(f"  {k}: {v}")

    # Geração da resposta final (mantendo o nome como no input)
    if valido and meta.get('employee_name'):
        resposta = f"**{meta['employee_name']}** recebeu R$ 8.418,75 em maio de 2025."
        print("\nResposta formatada:", resposta)
