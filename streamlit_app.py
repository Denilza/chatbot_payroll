import os
import re
import sys
import json
import pandas as pd
import streamlit as st
from datetime import datetime

# === Ajuste do PATH para imports locais ===
current_dir = os.getcwd()
sys.path.insert(0, current_dir)

# === Imports locais com fallback de segurança ===
try:
    from app.models.payroll import PayrollData
    from app.services.payroll_service import PayrollService
    from app.core.rag_engine import RAGEngine
    from app.services.llm_service import LLMService
    from app.core.chatbot import Chatbot
    from app.utils.config import settings

except ImportError as e:
    st.error(f"❌ Erro ao carregar módulos locais: {e}")
    st.stop()

# === IMPORTAÇÕES DOS GUARDRAILS E OBSERVABILITY ===
try:
    from guardrails import Guardrails
    from observability import Observability
    import logging
    logger = logging.getLogger('chatbot_payroll')

except ImportError as e:
    st.warning(f"⚠️ Módulos de segurança não encontrados: {e}")
    # Fallback básico
    class Guardrails:
        def validate_input(self, x): return True, "OK", {}
        def sanitize_input(self, x): return x
    class Observability:
        def log_interaction(self, *args, **kwargs): return "no-log"
        def log_guardrail_trigger(self, *args, **kwargs): return "no-log"


# === Classe principal do Chatbot ===
class StreamlitChatbot:
    """Lógica principal do Chatbot de Folha de Pagamento."""

    def __init__(self):
        # Inicializar Guardrails e Observability
        self.guardrails = Guardrails()
        self.observability = Observability()
        self.session_id = f"session_{datetime.now():%Y%m%d_%H%M%S}"
        
        data_file = "data/payroll.csv"
        if not os.path.exists(data_file):
            st.error(f"❌ Arquivo de dados não encontrado: `{data_file}`")
            self.initialized = False
            return

        try:
            self.payroll_data = PayrollData(data_file)
            self.payroll_service = PayrollService(self.payroll_data)
            self.rag_engine = RAGEngine(self.payroll_service)
            self.llm_service = LLMService()
            self.chatbot = Chatbot(self.rag_engine, self.llm_service)
            self.initialized = True
            
            # Log de inicialização
            self.observability.log_interaction(
                session_id=self.session_id,
                user_input="SYSTEM_STARTUP",
                response="Chatbot inicializado com sucesso",
                response_time=0.0,
                status="success"
            )
            
        except Exception as e:
            st.error(f"❌ Falha ao inicializar o chatbot: {e}")
            self.initialized = False

    # === Método principal de processamento ===
    def process_message(self, message: str) -> dict:
        """Processa a mensagem do usuário e retorna resposta e evidências."""
        if not self.initialized:
            return {"response": "Chatbot não inicializado corretamente.", "evidence": [], "sources": []}

        start_time = datetime.now()
        
        try:
            # === 1. VALIDAÇÃO COM GUARDRAILS ===
            is_valid, validation_message, guardrail_metadata = self.guardrails.validate_input(message)
            
            if not is_valid:
                response_time = (datetime.now() - start_time).total_seconds()
                
                # Log do bloqueio
                self.observability.log_guardrail_trigger(
                    session_id=self.session_id,
                    guardrail_type="input_validation",
                    user_input=message,
                    details=guardrail_metadata
                )
                
                self.observability.log_interaction(
                    session_id=self.session_id,
                    user_input=message,
                    response=validation_message,
                    response_time=response_time,
                    status="blocked",
                    guardrail_metadata=guardrail_metadata
                )
                return {"response": validation_message, "evidence": [], "sources": []}

            # === 2. CHAMADA AO RAGENGINE ===
            response_text, evidence = self.rag_engine.process_query(message)

            # === 3. FORMATAÇÃO DO NOME (capitalize) PARA EXIBIÇÃO ===
            match = re.search(r"\*\*(.*?)\*\*", response_text)
            if match:
                employee_name = match.group(1)
                formatted_name = ' '.join(word.capitalize() for word in employee_name.split())
                response_text = response_text.replace(f"**{employee_name}**", f"**{formatted_name}**")

            # === 4. CALCULO DE TEMPO DE RESPOSTA E LOG ===
            response_time = (datetime.now() - start_time).total_seconds()
            self.observability.log_interaction(
                session_id=self.session_id,
                user_input=message,
                response=response_text,
                response_time=response_time,
                status="success"
            )

            return {"response": response_text, "evidence": evidence, "sources": []}

        except Exception as e:
            logger.error(f"Erro ao processar mensagem: {e}")
            return {"response": f"❌ Erro ao processar mensagem: {e}", "evidence": [], "sources": []}

    # === Utilitários ===
    @staticmethod
    def _format_currency(value: float) -> str:
        """Formata números no padrão brasileiro de moeda."""
        return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    def format_evidence(self, evidence: list) -> str:
        """Formata a exibição das evidências de consulta."""
        if not evidence:
            return ""

        formatted = ["**📊 Evidências Encontradas:**\n"]
        for i, ev in enumerate(evidence, 1):
            formatted.append(
                f"""
**Registro {i}:**
- 👤 **Funcionário:** {ev.name} ({ev.employee_id})
- 📅 **Competência:** {ev.competency}
- 💰 **Salário Líquido:** {self._format_currency(ev.net_pay)}
"""
            )
            if ev.base_salary:
                formatted.append(f"- 📋 **Salário Base:** {self._format_currency(ev.base_salary)}")
            if ev.bonus:
                formatted.append(f"- 🎁 **Bônus:** {self._format_currency(ev.bonus)}")
            if ev.deductions_inss:
                formatted.append(f"- 🏦 **INSS:** {self._format_currency(ev.deductions_inss)}")
            if ev.deductions_irrf:
                formatted.append(f"- 📊 **IRRF:** {self._format_currency(ev.deductions_irrf)}")

            formatted.append(f"- 📆 **Data Pagamento:** {ev.payment_date}\n---\n")

        return "\n".join(formatted)

    @staticmethod
    def _is_relevant_question(message: str) -> bool:
        """Verifica se a pergunta é relevante ao contexto de folha de pagamento."""
        keywords = [
            "salário", "pagamento", "folha", "holerite", "contracheque",
            "inss", "irrf", "bruto", "líquido", "bonus", "bônus",
            "ana souza", "bruno lima", "funcionário", "colaborador",
            "quanto recebi", "quando pagou", "maio", "junho", "julho", "2025", "2024"
        ]
        return any(k in message.lower() for k in keywords)

    def generate_json_download(self, messages: list, conversation_id: str) -> dict:
        """Gera o JSON da conversa para exportação."""
        now = datetime.now().isoformat()
        conversation = {
            "conversation_id": conversation_id,
            "timestamp": now,
            "total_messages": len(messages),
            "messages": [],
        }

        for i, m in enumerate(messages, start=1):
            entry = {
                "sequence": i,
                "role": m["role"],
                "content": m["content"],
                "timestamp": now,
            }

            if m.get("evidence"):
                entry["evidence"] = [
                    {
                        "employee_id": ev.employee_id,
                        "name": ev.name,
                        "competency": ev.competency,
                        "net_pay": float(ev.net_pay),
                        "payment_date": ev.payment_date,
                        "base_salary": float(ev.base_salary or 0),
                        "bonus": float(ev.bonus or 0),
                        "deductions_inss": float(ev.deductions_inss or 0),
                        "deductions_irrf": float(ev.deductions_irrf or 0),
                    }
                    for ev in m["evidence"]
                ]

            conversation["messages"].append(entry)

        return conversation


# === Funções de Sessão ===
def initialize_session_state():
    """Inicializa variáveis persistentes da sessão."""
    if "chatbot" not in st.session_state:
        st.session_state.chatbot = StreamlitChatbot()

    st.session_state.setdefault("messages", [])
    st.session_state.setdefault("conversation_id", f"session_{datetime.now():%Y%m%d_%H%M%S}")


def clear_conversation():
    """Limpa todas as mensagens da conversa."""
    st.session_state.update({"messages": [], "initial_question": None, "selected_suggestion": None})


# === CSS Personalizado ===
def inject_custom_css():
    
    st.markdown("""
    <style>
    .main .block-container { padding-top: 2rem; padding-bottom: 1rem; }
    .stChatInput input { border-radius: 12px; border: 2px solid #2563EB; height: 60px; font-size: 16px; padding: 15px 20px; background-color: white; }
    .stChatInput { margin-top: 10px; margin-bottom: 0; }
    .not-understood-message { background-color: #fffbeb; border: 1px solid #fef3c7; border-radius: 8px; padding: 20px; margin: 10px 0; color: #92400e; border-left: 4px solid #f59e0b; }
    .guardrail-blocked { background-color: #fff3cd; border: 1px solid #ffeaa7; border-radius: 8px; padding: 20px; margin: 10px 0; color: #856404; border-left: 4px solid #ffc107; }
    .success-message { background-color: #d4edda; border: 1px solid #c3e6cb; border-radius: 8px; padding: 20px; margin: 10px 0; color: #155724; border-left: 4px solid #28a745; }
    </style>
    """, unsafe_allow_html=True)


# === Função principal ===
def main():
    st.set_page_config(
        page_title="🤖 Chatbot Folha de Pagamento",
        page_icon="💰",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    inject_custom_css()
    initialize_session_state()

    # ===== Cabeçalho =====
    col1, col2 = st.columns([4, 1])
    with col1:
        st.title("📋 Chatbot Folha de Pagamento")
        st.markdown(
            "<div style='color:#2563EB;font-size:1.1rem;margin-bottom:20px;'>"
            "Faça perguntas sobre folha de pagamento e obtenha respostas com evidências detalhadas."
            "</div>",
            unsafe_allow_html=True,
        )
    with col2:
        if st.button("🔄 Reiniciar", key="btn_restart"):
            clear_conversation()
            st.rerun()

    # ===== Sidebar =====
    with st.sidebar:
        st.markdown("### 💬 Sobre o Chat")
        st.info(
            "Este assistente utiliza IA e dados reais para responder dúvidas sobre "
            "folha de pagamento de funcionários como Ana Souza e Bruno Lima."
        )

        with st.expander("💡 Exemplos de Perguntas", expanded=True):
            st.markdown(
                """
                - "Quanto recebi (líquido) em maio/2025? (Ana Souza)"  
                - "Qual o total líquido de Ana Souza no 1º trimestre de 2025?"  
                - "Qual foi o desconto de INSS do Bruno em jun/2025?"  
                - "Quando foi pago o salário de abril/2025 do Bruno e qual o líquido?"  
                - "Qual foi o maior bônus do Bruno e em que mês?"
                """
            )

    # ===== Chat =====
    for i, msg in enumerate(st.session_state.messages):
        with st.chat_message(msg["role"]):
            # Aplica estilos diferentes para tipos de mensagens
            if "🚫 **Guardrail Ativado**" in msg["content"]:
                st.markdown(f'<div class="guardrail-blocked">{msg["content"]}</div>', unsafe_allow_html=True)
            elif "❌ Não foi possível compreender" in msg["content"]:
                st.markdown(f'<div class="not-understood-message">{msg["content"]}</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="success-message">{msg["content"]}</div>', unsafe_allow_html=True)

            if msg.get("evidence"):
                with st.expander("📊 Ver Evidências", expanded=False):
                    formatted = st.session_state.chatbot.format_evidence(msg["evidence"])
                    st.markdown(formatted)

                    # Exportação das evidências
                    json_data = st.session_state.chatbot.generate_json_download([msg], st.session_state.conversation_id)
                    st.download_button(
                        label="📥 Baixar JSON",
                        data=json.dumps(json_data, indent=2, ensure_ascii=False),
                        file_name=f"folha_{datetime.now():%Y%m%d_%H%M%S}.json",
                        mime="application/json",
                        key=f"download_{i}",
                        use_container_width=True,
                    )

    # ===== Input do Usuário =====
    user_input = st.chat_input("💬 Escreva sua pergunta sobre folha de pagamento...")

    # ===== Processamento da Mensagem =====
    if user_input:
        st.session_state.messages.append({"role": "user", "content": user_input})

        with st.spinner("🛡️ Validando e processando..."):
            result = st.session_state.chatbot.process_message(user_input)

        st.session_state.messages.append(
            {"role": "assistant", "content": result["response"], "evidence": result["evidence"]}
        )

        st.rerun()


if __name__ == "__main__":
    main()
