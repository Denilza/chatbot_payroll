🤖 Chatbot Folha de Pagamento(Acesse aqui: [https://chatbotpayroll-bdjvppxtzn7wukfludds3d.streamlit.app/](https://chatbotpayroll-eptmrmbmrb52zahgcb5knp.streamlit.app/))
Um chatbot inteligente desenvolvido em Python com Streamlit para consultas sobre folha de pagamento, utilizando técnicas de RAG (Retrieval-Augmented Generation) e processamento de linguagem natural.

🚀 Funcionalidades Atuais
💼 Consultas de Folha de Pagamento
Salário Líquido: Consulta de valores líquidos por período

Datas de Pagamento: Informações sobre quando os salários foram pagos

Descontos: Detalhes sobre INSS, IRRF e outras deduções

Bônus: Consulta de valores e períodos de bônus

Histórico: Acesso a registros históricos de pagamento

👥 Funcionários Suportados
Ana Souza

Bruno Lima

📊 Exemplos de Perguntas
"Quanto recebi em maio/2025?" (Ana Souza)

"Qual o total líquido de Ana Souza no 1º trimestre?"

"Qual foi o desconto de INSS do Bruno em jun/2025?"

"Quando foi pago o salário de abril/2025 do Bruno?"

"Qual foi o maior bônus do Bruno e em que mês?"

🛠️ Tecnologias Utilizadas
Frontend: Streamlit

Backend: Python

Processamento de Linguagem: RAG Engine customizado

Armazenamento: CSV com dados de folha de pagamento

Estilização: CSS personalizado com gradientes

🔮 Roadmap e Futuras Melhorias
🌐 Pesquisa Web e Integrações
Integração com APIs financeiras para dados em tempo real

Busca web para consulta de taxas Selic e indicadores econômicos

Web scraping de portais oficiais para informações atualizadas

API do Banco Central para dados econômicos oficiais

🎨 Melhorias de Usabilidade
Interface mais intuitiva com componentes visuais aprimorados

Modo escuro/claro para melhor experiência do usuário

Relatórios exportáveis em PDF e Excel

Gráficos interativos para visualização de dados

Histórico de conversas persistente entre sessões

🤖 Inteligência Artificial
Modelos de LLM mais avançados para melhor compreensão

Análise preditiva de tendências de pagamento

Reconhecimento de voz para interações hands-free

Suporte multilíngue para atendimento internacional

📈 Funcionalidades Avançadas
Comparativos entre funcionários (com privacidade)

Projeções futuras baseadas em dados históricos

Alertas automáticos para datas importantes

Integração com sistemas de RH existentes

Dashboard administrativo para gestores

## 🏗️ Estrutura do Projeto

```text
chatbot_payroll/
├── app/
│   ├── main.py
│   ├── core/
│   │   ├── chatbot.py
│   │   └── rag_engine.py
│   ├── models/
│   │   └── schemas.py
│   └── services/
│       └── payroll_service.py
├── tests/
│   └── test_basico.py
├── .gitignore
├── pyproject.toml
├── README.md
└── streamlit_app.py
```
⚙️ Instalação e Configuração
# 1. Clonar
git clone https://github.com/seu-usuario/chatbot_payroll.git
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
Acesse a aplicação no navegador (geralmente http://localhost:8501)

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
# Ambiente virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Desenvolvimento
pip install -r requirements-dev.txt
streamlit run streamlit_app.py
🤝 Contribuição
Este projeto está em constante evolução! Contribuições são bem-vindas:

Fork o projeto

Crie uma branch para sua feature (git checkout -b feature/nova-feature)

Commit suas mudanças (git commit -am 'Adiciona nova feature')

Push para a branch (git push origin feature/nova-feature)

Abra um Pull Request

📝 Licença
Este projeto está sob a licença MIT. Veja o arquivo LICENSE para detalhes.

# API Chat Bot - Exemplos de Uso

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


# chatbot_payroll
