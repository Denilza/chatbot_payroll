# 🤖 Chatbot Folha de Pagamento  

**Aplicação:** [Chatbot Folha de Pagamento](https://denilza-chatbot-payroll.streamlit.app/)  

Um chatbot inteligente para consulta de **folha de pagamento (payroll)** — o conjunto de registros salariais de colaboradores, incluindo salários, bônus e descontos.  
O sistema permite consultar informações salariais de forma simples, automatizada e segura, utilizando **técnicas de RAG (Retrieval-Augmented Generation)** e **processamento de linguagem natural (NLP)**.  

---

## 🎯 Objetivo e Justificativa  

O projeto foi desenvolvido para **automatizar consultas de folha de pagamento**, reduzindo o tempo de resposta do RH e melhorando a transparência com os funcionários.  

### 🧠 Justificativas Técnicas  
- Utiliza o modelo **GPT-3.5-Turbo** (LLM livre da OpenAI), escolhido pelo **baixo custo, estabilidade e excelente desempenho** em tarefas de linguagem.  
- A arquitetura **RAG (Retrieval-Augmented Generation)** garante **respostas precisas e contextualizadas** com base nos dados reais da folha.  
- O **Pandas** foi adotado para manipulação e análise eficiente dos dados salariais, pela sua **performance, flexibilidade e ampla adoção no ecossistema de dados em Python**.  
- Estrutura modular em **Python (3.11.9)** facilita **testes, manutenção e escalabilidade**.  

graph LR
    A[📩 Mensagem do Usuário] --> B{🔍 Análise de Intenção}
    
    B -->|Consulta Folha| C[📊 Sistema RAG]
    B -->|Busca Web| D[🌐 Web Search]
    B -->|Conversa Geral| E[💬 LLM Direto]
    
    C --> F[🔍 Buscar Dados]
    F --> G[📋 Formatar Resposta]
    
    D --> H[🌐 Buscar na Web]
    H --> I[📝 Extrair Informação]
    
    E --> J[🧠 Gerar Resposta]
    
    G --> K[📤 Entregar Resposta]
    I --> K
    J --> K
    
    K --> L[💾 Atualizar Memória]
---
## ⚙️ Execução Local  

### 1️⃣ Clonar o repositório  
```bash
git clone https://github.com/Denilza/chatbot_payroll.git
cd chatbot_payroll

# 2. Venv
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# 3. Instalar
pip install -e .

# 4. Executar
streamlit run streamlit_app.py

🎯 Como Usar
Acesse a aplicação no navegador: http://localhost:8501

Faça perguntas em linguagem natural sobre folha de pagamento

Visualize evidências expandindo a seção "Ver Evidências"

Exporte dados usando o botão de download JSON

🔧 Configuração de Desenvolvimento
Variáveis de Ambiente
env
SERPER_API_KEY=sua_chave_api_serper
OPENAI_API_KEY=sua_chave_openai
LOG_LEVEL=INFO
Desenvolvimento Local
bash

# Desenvolvimento
pip install -r requirements-dev.txt
streamlit run streamlit_app.py

🧪 Executando Testes

Os testes unitários estão localizados na pasta tests/.
Para executá-los, use:

pytest -v


## Endpoints disponíveis

### 1. Chat - Processamento de consultas
```bash
$ curl -X POST http://localhost:8000/chat \
>   -H "Content-Type: application/json" \
>   -d '{"message": "Quanto recebi em maio/2025? (Ana Souza)"}'
{"response":"ana souza recebeu R$ 8.418,75 em maio de 2025.","evidence":[{"employee_id":"E001","name":"Ana Souza","competency":"2025-05","net_pay":8418.75,"payment_date":"2025-05-28","base_salary":8000.0,"bonus":1200.0,"deductions_inss":880.0,"deductions_irrf":551.25}],"sources":["payroll.csv"],"conversation_id":"default"}(venv) 

📞 Suporte
Para dúvidas e suporte:

📧 Email: denilzalimas@gmail.com

🤝 Contribuição
Este projeto está em constante evolução! Contribuições são bem-vindas:

Fork o projeto

Crie uma branch para sua feature (git checkout -b feature/nova-feature)

Commit suas mudanças (git commit -am 'Adiciona nova feature')

Push para a branch (git push origin feature/nova-feature)

Abra um Pull Request


📝 Licença
Este projeto está sob a licença MIT. Veja o arquivo LICENSE para detalhes.

# chatbot_payroll
