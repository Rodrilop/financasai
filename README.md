# 💎 FinançasAI: Inteligência Financeira e Investimentos

FinançasAI é uma plataforma de gestão financeira pessoal de alta performance, projetada para unir o controle de gastos tradicional com a inteligência de investimentos e o poder da Inteligência Artificial Generativa.

O sistema atua como um **Agente Financeiro Proativo**, capaz de entender comandos de voz, processar comprovantes via imagem e fornecer recomendações estratégicas baseadas no perfil do investidor e no cenário real do mercado brasileiro (B3).

---

## 🚀 Funcionalidades Principais

### 🧠 Assistente IA de Segunda Geração
*   **Multimodalidade**: Entende texto, áudio (voz) e imagens (comprovantes e prints).
*   **Function Calling**: A IA executa ações reais no banco de dados, como registrar despesas, atualizar salários ou consultar cotações.
*   **Análise Proativa**: Sistema de notificações que gera alertas automáticos sobre saúde financeira e oportunidades de investimento.

### 📈 Investimentos e Portfólio (B3 em Tempo Real)
*   **Acompanhamento ao Vivo**: Cotações de Ações e FIIs da B3 via Yahoo Finance.
*   **Métricas Avançadas**: Cálculo automático de **Yield on Cost (YoC)** e estimativa de dividendos para os próximos 12 meses.
*   **Alocação Estratégica**: Sugestões de investimento baseadas em perfis (Conservador, Moderado, Agressivo) e critérios de Benjamin Graham e Luiz Barsi.

### 📊 Gestão de Gastos e Orçamento
*   **Regra 50-30-20**: Monitoramento automático de gastos em categorias Essencial, Importante e Opcional.
*   **Reserva de Emergência**: Acompanhamento visual de progresso da meta de reserva.
*   **Importação Inteligente**: Importador de CSV robusto com detecção automática de delimitadores e mapeamento de colunas bancárias.

### 📱 Integração WhatsApp (Evolution API)
*   Controle suas finanças diretamente pelo WhatsApp. Envie mensagens de texto ou áudio para o bot e ele registrará tudo automaticamente no seu dashboard.

---

## 🛠️ Stack Tecnológica

### Frontend
*   **React + Vite**: Interface ultrarrápida e responsiva.
*   **Vanilla CSS**: Design customizado com estética *premium*, dark mode e glassmorphism.
*   **Recharts**: Visualização de dados e gráficos financeiros.

### Backend
*   **FastAPI (Python)**: API de alta performance e baixa latência.
*   **Turso (libSQL)**: Banco de dados na borda (edge computing) para latência mínima.
*   **Custom DB Proxy**: Implementação de proxy HTTP para Turso, garantindo resiliência e fallback automático para **SQLite** local.

### Inteligência Artificial
*   **Groq (Llama 3.3)**: Motor primário para raciocínio lógico ultrarrápido.
*   **Gemini 2.0 Flash**: Fallback e processamento multimodal (imagem/áudio).
*   **Whisper**: Transcrição de áudio para comandos de voz.

---

## 🏗️ Arquitetura e Diferenciais Técnicos

### Resiliência de Dados
O sistema utiliza um padrão de **Connection Proxy** que detecta a disponibilidade do banco em nuvem (Turso). Caso a conexão falhe, a aplicação alterna instantaneamente para um banco SQLite local, sincronizando os dados quando a rede é restabelecida.

### Agentic Reasoning
Diferente de chatbots comuns, a IA do FinançasAI possui ferramentas (`tools`) que permitem interagir com o sistema. Ela pode consultar seu saldo antes de dar uma recomendação ou verificar o preço de uma ação antes de sugerir uma compra.

---

## ⚙️ Instalação e Configuração

### 1. Requisitos
*   Python 3.10+
*   Node.js 18+
*   Conta no Turso (opcional, para nuvem)
*   API Keys: Groq, Gemini e Evolution API (para WhatsApp).

### 2. Configuração do Backend
1. Navegue até `/backend`.
2. Instale as dependências: `pip install -r requirements.txt`.
3. Configure o arquivo `.env`:
   ```env
   GROQ_API_KEY=sua_chave
   GEMINI_API_KEY=sua_chave
   TURSO_DATABASE_URL=libsql://seu-db.turso.io
   TURSO_AUTH_TOKEN=seu_token
   JWT_SECRET_KEY=sua_chave_secreta
   ```
4. Inicie o servidor: `uvicorn main:app --reload`.

### 3. Configuração do Frontend
1. Navegue até `/frontend`.
2. Instale as dependências: `npm install`.
3. Inicie o ambiente de desenvolvimento: `npm run dev`.

---

## 🛡️ Segurança e Privacidade
*   Autenticação via **JWT (JSON Web Tokens)**.
*   Criptografia de senhas com **Bcrypt**.
*   Isolamento de dados por `user_id` em todas as camadas da aplicação.

---

## 📄 Licença
Distribuído sob a licença MIT. Veja `LICENSE` para mais informações.

---
*Desenvolvido com foco em alta performance e inteligência financeira.*
