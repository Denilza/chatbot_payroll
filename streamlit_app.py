import streamlit as st
import pandas as pd
import sys
import os
import json
from datetime import datetime
import re

# Adiciona o diretório atual ao Python path
current_dir = os.getcwd()
sys.path.insert(0, current_dir)

# Importar módulos locais
try:
    from app.models.payroll import PayrollData
    from app.services.payroll_service import PayrollService
    from app.core.rag_engine import RAGEngine
    from app.services.llm_service import LLMService
    from app.core.chatbot import Chatbot
    from app.utils.config import settings
except ImportError as e:
    st.error(f"❌ Erro ao importar módulos: {e}")
    st.stop()

class StreamlitChatbot:
    def __init__(self):
        try:
            # Verificar se o arquivo de dados existe
            data_file = "data/payroll.csv"
            if not os.path.exists(data_file):
                st.error(f"❌ Arquivo de dados não encontrado: {data_file}")
                self.initialized = False
                return
            
            self.payroll_data = PayrollData(data_file)
            self.payroll_service = PayrollService(self.payroll_data)
            self.rag_engine = RAGEngine(self.payroll_service)
            self.llm_service = LLMService()
            self.chatbot = Chatbot(self.rag_engine, self.llm_service)
            self.initialized = True
        except Exception as e:
            st.error(f"❌ Erro ao inicializar chatbot: {e}")
            self.initialized = False
    
    def format_evidence(self, evidence: list) -> str:
        """Formata evidências para exibição"""
        if not evidence:
            return ""
        
        formatted = "**📊 Evidências Encontradas:**\n\n"
        for i, ev in enumerate(evidence, 1):
            formatted += f"**Registro {i}:**\n"
            formatted += f"- 👤 **Funcionário:** {ev.name} ({ev.employee_id})\n"
            formatted += f"- 📅 **Competência:** {ev.competency}\n"
            formatted += f"- 💰 **Salário Líquido:** R$ {ev.net_pay:,.2f}\n".replace(",", "X").replace(".", ",").replace("X", ".")
            
            if ev.base_salary:
                formatted += f"- 📋 **Salário Base:** R$ {ev.base_salary:,.2f}\n".replace(",", "X").replace(".", ",").replace("X", ".")
            if ev.bonus:
                formatted += f"- 🎁 **Bônus:** R$ {ev.bonus:,.2f}\n".replace(",", "X").replace(".", ",").replace("X", ".")
            if ev.deductions_inss:
                formatted += f"- 🏦 **INSS:** R$ {ev.deductions_inss:,.2f}\n".replace(",", "X").replace(".", ",").replace("X", ".")
            if ev.deductions_irrf:
                formatted += f"- 📊 **IRRF:** R$ {ev.deductions_irrf:,.2f}\n".replace(",", "X").replace(".", ",").replace("X", ".")
            
            formatted += f"- 📆 **Data Pagamento:** {ev.payment_date}\n"
            formatted += "\n---\n"
        
        return formatted
    
    def process_message(self, message: str) -> dict:
        """Processa mensagem e retorna resposta"""
        if not self.initialized:
            return {
                "response": "Chatbot não inicializado corretamente.",
                "evidence": [],
                "sources": []
            }
        
        try:
            # Usa o RAGEngine diretamente para melhor controle
            response_text, evidence = self.rag_engine.process_query(message)
            
            return {
                "response": response_text,
                "evidence": evidence,
                "sources": []
            }
                
        except Exception as e:
            return {
                "response": f"Erro ao processar mensagem: {e}",
                "evidence": [],
                "sources": []
            }
    
    def _identify_employee(self, message: str) -> str:
        """Identifica qual funcionário está sendo mencionado na mensagem"""
        message_clean = re.sub(r'[^\w\s]', ' ', message).lower()
        
        # Mapeamento de funcionários
        employee_mapping = {
            'Ana Souza': ['ana souza', 'ana', 'souza'],
            'Bruno Lima': ['bruno lima', 'bruno', 'lima']
        }
        
        # Procura por menções
        for employee, mentions in employee_mapping.items():
            for mention in mentions:
                if re.search(rf'\b{mention}\b', message_clean):
                    return employee
        
        return None
    
    def generate_json_download(self, messages: list, conversation_id: str) -> dict:
        """Gera JSON para download com todas as informações da conversa"""
        conversation_data = {
            "conversation_id": conversation_id,
            "timestamp": datetime.now().isoformat(),
            "total_messages": len(messages),
            "messages": []
        }
        
        for i, message in enumerate(messages):
            message_data = {
                "sequence": i + 1,
                "role": message["role"],
                "content": message["content"],
                "timestamp": datetime.now().isoformat()
            }
            
            # Adiciona evidências se existirem
            if message.get("evidence"):
                message_data["evidence"] = [
                    {
                        "employee_id": ev.employee_id,
                        "name": ev.name,
                        "competency": ev.competency,
                        "net_pay": float(ev.net_pay),
                        "payment_date": ev.payment_date,
                        "base_salary": float(ev.base_salary) if ev.base_salary else None,
                        "bonus": float(ev.bonus) if ev.bonus else None,
                        "deductions_inss": float(ev.deductions_inss) if ev.deductions_inss else None,
                        "deductions_irrf": float(ev.deductions_irrf) if ev.deductions_irrf else None
                    }
                    for ev in message["evidence"]
                ]
            
            conversation_data["messages"].append(message_data)
        
        return conversation_data

def initialize_session_state():
    """Inicializa o estado da sessão"""
    if 'chatbot' not in st.session_state:
        st.session_state.chatbot = StreamlitChatbot()
    
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    
    if 'conversation_id' not in st.session_state:
        st.session_state.conversation_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

def main():
    st.set_page_config(
        page_title="🤖 Chatbot Folha de Pagamento",
        page_icon="💰",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # CSS personalizado com gradiente linear
    st.markdown("""
    <style>
    /* Fundo cinza claro */
    .main {
        background-color: #f8f9fa;
    }
    
    .stApp {
        background-color: #f8f9fa;
    }
    
    /* Área central com GRADIENTE LINEAR */
    .main .block-container {
        background: linear-gradient(90deg, #2563EB 0%, #7C3AED 100%) !important;
        border-radius: 15px;
        padding: 30px;
        margin: 20px auto;
        max-width: 95%;
        box-shadow: 0 8px 25px rgba(37, 99, 235, 0.3);
        border: 1px solid transparent;
    }
    
    /* Sidebar styling */
    .css-1d391kg, .css-1lcbmhc {
        background-color: #ffffff;
        border-right: 1px solid #e0e0e0;
    }
    
    /* Chat container styling */
    .chat-container {
        background: #ffffff;
        border-radius: 10px;
        padding: 20px;
        margin: 10px 0;
        box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
        border: 1px solid #e0e0e0;
    }
    
    /* Message styling */
    .stChatMessage {
        background: #ffffff;
        border-radius: 10px;
        padding: 15px;
        margin: 10px 0;
        border: 1px solid #e0e0e0;
    }
    
    /* Button styling */
    .stButton button {
        background: linear-gradient(90deg, #2563EB 0%, #7C3AED 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 10px 20px;
        font-weight: 600;
    }
    
    .stButton button:hover {
        background: linear-gradient(90deg, #1d4ed8 0%, #6d28d9 100%);
        color: white;
    }
    
    /* Input styling - AUMENTADO */
    .stChatInput input {
        border-radius: 12px;
        border: 3px solid #2563EB;
        height: 60px;
        font-size: 16px;
        padding: 15px 20px;
        background-color: white;
    }
    
    .stChatInput {
        margin-top: 25px;
        margin-bottom: 15px;
    }
    
    /* Expander styling */
    .streamlit-expanderHeader {
        background-color: #f1f3f4;
        color: #333 !important;
        border-radius: 8px;
        border: 1px solid #e0e0e0;
    }
    
    /* Texto branco para contraste na área com gradiente */
    .main .block-container h1, 
    .main .block-container h2, 
    .main .block-container h3,
    .main .block-container .stMarkdown p,
    .main .block-container .stMarkdown div {
        color: white !important;
    }
    
    /* Download button styling */
    .download-btn {
        background: linear-gradient(90deg, #2563EB 0%, #7C3AED 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 12px 24px;
        font-weight: 600;
        margin-top: 15px;
    }
    
    /* Ajustes para garantir contraste */
    .stChatInput input::placeholder {
        color: #666;
    }
    
    /* Estilo para mensagens de erro */
    .error-message {
        background-color: #fee2e2;
        border: 1px solid #fecaca;
        border-radius: 8px;
        padding: 15px;
        margin: 10px 0;
        color: #dc2626;
    }
    
    /* Estilo para mensagens de sugestão */
    .suggestion-message {
        background-color: #dbeafe;
        border: 1px solid #93c5fd;
        border-radius: 8px;
        padding: 15px;
        margin: 10px 0;
        color: #1e40af;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Header principal - DENTRO DA ÁREA COM GRADIENTE
    st.title("📋Chatbot Folha de Pagamento")
    st.markdown("""
    <div style='color: white; font-size: 1.2rem; margin-bottom: 30px;'>
    Faça perguntas sobre folha de pagamento e obtenha respostas instantâneas com evidências detalhadas.
    </div>
    """, unsafe_allow_html=True)
    
    initialize_session_state()
    
    # Sidebar com informações do chat
    with st.sidebar:
        st.markdown("""
        <div style='padding: 10px; margin-bottom: 20px;'>
            <h3 style='color: #2563EB;'>💬 Sobre o Chat</h3>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div style='background: #f8f9fa; padding: 15px; border-radius: 8px; margin-bottom: 20px;'>
        <p style='color: #333; font-size: 0.9rem; margin-bottom: 10px;'>
        <strong>🤖 Assistente IA</strong><br>
        Este chatbot utiliza inteligência artificial para responder suas dúvidas sobre folha de pagamento de forma precisa e rápida.
        </p>
        <p style='color: #333; font-size: 0.9rem; margin-bottom: 10px;'>
        <strong>📊 Dados em Tempo Real</strong><br>
        Todas as respostas são baseadas em dados reais do sistema de folha de pagamento.
        </p>
        <p style='color: #333; font-size: 0.9rem;'>
        <strong>🔍 Evidências Detalhadas</strong><br>
        Cada resposta inclui evidências completas com todos os detalhes dos cálculos.
        </p>
        </div>
        """, unsafe_allow_html=True)
        
        # Exemplos de perguntas
        with st.expander("💡 Exemplos de Perguntas", expanded=True):
            st.markdown("""
            - *"Quanto recebi em maio/2025?"* (Ana Souza)
            - *"Qual o total líquido de Ana Souza no 1º trimestre?"*
            - *"Qual foi o desconto de INSS do Bruno em jun/2025?"*
            - *"Quando foi pago o salário de abril/2025 do Bruno?"*
            - *"Qual foi o maior bônus do Bruno e em que mês?"*
            """)
        
        # Botão limpar conversa - COM CHAVE ÚNICA
        st.markdown("---")
        if st.button("🗑️ Limpar Conversa", use_container_width=True, key="clear_chat_button"):
            st.session_state.messages = []
            st.rerun()
        
        # Estatísticas (se houver mensagens)
        if st.session_state.messages:
            st.markdown("---")
            st.subheader("📈 Estatísticas")
            user_messages = len([m for m in st.session_state.messages if m['role'] == 'user'])
            bot_messages = len([m for m in st.session_state.messages if m['role'] == 'assistant'])
            st.write(f"💬 **Total:** {len(st.session_state.messages)} mensagens")
            st.write(f"👤 **Suas:** {user_messages}")
            st.write(f"🤖 **Respostas:** {bot_messages}")
    
    # Área principal do chat - DENTRO DA ÁREA COM GRADIENTE
    chat_container = st.container()
    
    with chat_container:
        # Exibir histórico de mensagens - USANDO ENUMERATE PARA OBTER ÍNDICE
        for i, message in enumerate(st.session_state.messages):
            if message["role"] == "user":
                with st.chat_message("user"):
                    st.markdown(message["content"])
            else:
                with st.chat_message("assistant"):
                    # Aplica estilos diferentes para mensagens de erro
                    if "❌" in message["content"]:
                        st.markdown(f'<div class="error-message">{message["content"]}</div>', unsafe_allow_html=True)
                    elif "Por favor, especifique" in message["content"]:
                        st.markdown(f'<div class="suggestion-message">{message["content"]}</div>', unsafe_allow_html=True)
                    else:
                        st.markdown(message["content"])
                    
                    if message.get("evidence"):
                        with st.expander("📊 Ver Evidências", expanded=False):
                            formatted_evidence = st.session_state.chatbot.format_evidence(message["evidence"])
                            st.markdown(formatted_evidence)
                            
                            # Botão de download JSON após as evidências - COM CHAVE ÚNICA
                            if message["evidence"]:
                                st.markdown("---")
                                st.markdown("### 📥 Exportar Dados")
                                conversation_json = st.session_state.chatbot.generate_json_download(
                                    [message], 
                                    f"evidence_{datetime.now().strftime('%H%M%S')}"
                                )
                                
                                st.download_button(
                                    label="📊 Baixar JSON Completo",
                                    data=json.dumps(conversation_json, indent=2, ensure_ascii=False),
                                    file_name=f"folha_pagamento_{message['evidence'][0].name}_{datetime.now().strftime('%Y%m%d')}.json",
                                    mime="application/json",
                                    use_container_width=True,
                                    key=f"download_btn_{i}_{datetime.now().strftime('%H%M%S')}"  # CHAVE ÚNICA ADICIONADA
                                )
    
    # Input do usuário - AUMENTADO E DENTRO DA ÁREA COM GRADIENTE
    st.markdown("---")
    st.markdown("### 👩 Digite sua mensagem")
    
    # Container para dar mais destaque ao input
    with st.container():
        user_input = st.chat_input(
            "💬 Escreva sua pergunta sobre folha de pagamento aqui...",
            key="large_chat_input"
        )
    
    if user_input:
        # Adicionar mensagem do usuário ao histórico
        st.session_state.messages.append({"role": "user", "content": user_input})
        
        # Processar e adicionar resposta do bot
        with st.spinner("🤔 Processando sua pergunta..."):
            response = st.session_state.chatbot.process_message(user_input)
        
        st.session_state.messages.append({
            "role": "assistant", 
            "content": response["response"],
            "evidence": response["evidence"]
        })
        
        st.rerun()

    # Rodapé
    st.markdown(
        """
        <hr>
        <p style='text-align: center; color: gray; font-size: 12px;'>
            Desenvolvido por Denilza Lima-2025
        </p>
        """,
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()