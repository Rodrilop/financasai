# 🤖 FinançasAI: O seu Agente Financeiro Inteligente

O **FinançasAI** é uma plataforma de gestão financeira revolucionária que utiliza Inteligência Artificial Multimodal para transformar a maneira como você lida com dinheiro.

## ✨ Funcionalidades "Agent-First"

- **📸 Visão Computacional:** Tire fotos de seus cupons fiscais e o Assistente registra os gastos automaticamente via Groq Vision/Gemini.
- **🎙️ Comandos de Voz:** Fale naturalmente com o app. O Assistente entende, transcreve (Groq Whisper) e executa suas ordens via áudio nativo.
- **📈 Gestão de Carteira:** Adicione e acompanhe ações da B3, FIIs e Criptomoedas em tempo real direto pela conversa.
- **📱 WhatsApp Integration:** Controle suas finanças pelo WhatsApp (via Evolution API).
- **🔎 Investigação Web:** O Assistente pesquisa taxas de juros (Selic), moedas (Dólar) e notícias do mercado em tempo real.
- **🔔 Motor Proativo:** A IA analisa seus dados em background e envia notificações automáticas com dicas de economia.

## 🛠️ Tecnologias Utilizadas

### Backend
- **FastAPI** com **Uvicorn** e **Groq SDK** (Llama 3.3 / Whisper)
- **SQLite** (padrão local) ou **Turso / libSQL** (Edge-Cloud)
- **Google Gemini** (Vision fallback) via `google-generativeai`
- **yfinance** & **duckduckgo-search** para dados de mercado
- **JWT** via `pyjwt` + senhas com `passlib[bcrypt]`
- **Pytest** para testes automatizados

### Frontend
- **React 18** + **Vite 5**
- **React Router DOM** — navegação e rotas protegidas via `AuthContext`
- **Recharts** — gráficos financeiros interativos
- **Axios** — comunicação com a API
- **Vitest** + **Testing Library** — testes unitários

### Infraestrutura
- **Docker** + **Docker Compose** — ambiente completo em contêineres

---

## 🚀 Como Executar

### ✅ Opção 1 — Docker (Recomendado)

A forma mais simples de rodar o projeto inteiro com um único comando.

**Pré-requisitos:** Docker Desktop instalado e em execução.

**1. Clone o repositório:**
```bash
git clone https://github.com/SEU_USUARIO/financasai.git
cd financasai
```

**2. Crie o arquivo `.env` na raiz do projeto:**
```env
GROQ_API_KEY=sua_chave_groq_aqui
GEMINI_API_KEY=sua_chave_gemini_aqui
JWT_SECRET_KEY=uma_chave_secreta_forte_aqui
TURSO_DATABASE_URL=        # (opcional) URL do banco Turso
TURSO_AUTH_TOKEN=          # (opcional) Token do Turso
```

> ⚠️ Sem `TURSO_DATABASE_URL`, o app usa **SQLite local** automaticamente. Não é necessário configurar o Turso para rodar.

**3. Suba os contêineres:**
```bash
docker compose up --build
```

| Serviço | URL |
|---|---|
| Frontend (React/Vite) | http://localhost:5173 |
| Backend (FastAPI) | http://localhost:8000 |
| Documentação Swagger | http://localhost:8000/docs |

Para parar:
```bash
docker compose down
```

---

### 🔧 Opção 2 — Execução Local (sem Docker)

**Backend:**
```bash
cd backend

# Crie e ative um ambiente virtual
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

pip install -r requirements.txt
```

Crie o arquivo `backend/.env`:
```env
GROQ_API_KEY=sua_chave_groq_aqui
GEMINI_API_KEY=sua_chave_gemini_aqui
JWT_SECRET_KEY=uma_chave_secreta_forte_aqui
```

Inicie a API:
```bash
python -m uvicorn main:app --reload --port 8000
```

**Frontend** (em outro terminal):
```bash
cd frontend
npm install
npm run dev
```

---

## 🧪 Testes

**Backend:**
```bash
cd backend
pytest tests/ -v
```

**Frontend:**
```bash
cd frontend
npm test
```

---

## 📁 Estrutura do Projeto

```
financasai/
├── backend/
│   ├── main.py           # Endpoints FastAPI
│   ├── auth.py           # JWT e hashing de senhas
│   ├── database.py       # Conexão SQLite / Turso
│   ├── analyzer.py       # Lógica de análise financeira
│   ├── ai_engine.py      # Integração com Google Gemini
│   ├── market.py         # Dados de mercado (yfinance)
│   ├── requirements.txt
│   ├── Dockerfile
│   ├── .dockerignore
│   └── tests/
│       ├── test_auth.py
│       └── test_main.py
├── frontend/
│   ├── src/
│   │   ├── pages/        # Dashboard, Expenses, Analysis, Investments, Settings, Login, Register
│   │   ├── components/   # Modal
│   │   ├── contexts/     # AuthContext (JWT)
│   │   └── App.jsx
│   ├── Dockerfile
│   └── package.json
├── docker-compose.yml
└── .env                  # Variáveis de ambiente (não versionar)
```

---

## 🔒 Segurança

- **Autenticação JWT** — todas as rotas da API (exceto `/api/auth/*` e `/health`) exigem token Bearer.
- **Senhas hasheadas** — `bcrypt` com `passlib` (fixado em `bcrypt==4.0.1` por compatibilidade).
- **Variáveis de ambiente** — nunca versionadas (`.env` está no `.gitignore`).
- **CORS configurado** — apenas via middleware do FastAPI.
- **Validação de dados** — todos os inputs validados por modelos Pydantic com limites de tamanho e tipo.

> ⚠️ O arquivo `backend/.env` e o arquivo `.env` da raiz **nunca devem ser commitados** no repositório.

---

## 🔄 CI/CD

O repositório possui um pipeline de GitHub Actions configurado em `.github/` que executa `pytest` e `vitest` automaticamente a cada push para o branch principal.

---

## 🆓 Deploy Gratuito em Produção

Stack 100% gratuito para projetos pessoais:

| Serviço | Plataforma | Custo |
|---|---|---|
| **Frontend** | [Vercel](https://vercel.com) | Grátis |
| **Backend** | [Render](https://render.com) | Grátis (dorme após 15min) |
| **Banco de dados** | [Turso](https://turso.tech) | Grátis (5GB) |
| **Anti-sleep** | [UptimeRobot](https://uptimerobot.com) | Grátis |

### Passo 1 — Banco de dados (Turso)

1. Crie uma conta em [turso.tech](https://turso.tech)
2. Instale a CLI no PowerShell: 
   ```powershell
   powershell -ExecutionPolicy Bypass -c "irm https://github.com/tursodatabase/turso/releases/latest/download/turso_cli-installer.ps1 | iex"
   ```
3. Feche e abra o terminal novamente para aplicar o comando.
4. Faça login: `turso auth login`
5. Crie o banco: `turso db create financasai`
5. Obtenha as credenciais:
   ```bash
   turso db show financasai --url   # → TURSO_DATABASE_URL
   turso db tokens create financasai # → TURSO_AUTH_TOKEN
   ```

### Passo 2 — Backend (Render)

1. Acesse [render.com](https://render.com) e conecte seu repositório GitHub
2. Crie um **Web Service** → selecione o repositório → defina:
   - **Root Directory**: `backend`
   - **Runtime**: Docker
   - **Instance Type**: Free
3. Em **Environment Variables**, adicione:
   ```
   GEMINI_API_KEY=sua_chave_aqui
   GEMINI_MODEL=gemini-2.5-flash
   JWT_SECRET_KEY=chave_secreta_forte_aleatoria
   TURSO_DATABASE_URL=libsql://financasai-...turso.io
   TURSO_AUTH_TOKEN=eyJh...
   ```
4. Copie a URL do serviço: `https://financasai.onrender.com`

### Passo 3 — Frontend (Vercel)

1. Acesse [vercel.com](https://vercel.com) e conecte seu repositório GitHub
2. Crie um novo projeto → selecione o repositório → defina:
   - **Root Directory**: `frontend`
   - **Framework Preset**: Vite (detectado automaticamente)
3. Em **Environment Variables**, adicione:
   ```
   VITE_API_URL=https://financasai.onrender.com
   ```
4. Clique em **Deploy** — sua URL será `https://financasai.vercel.app`

### Passo 4 — Anti-sleep (UptimeRobot)

1. Crie uma conta em [uptimerobot.com](https://uptimerobot.com)
2. Crie um novo monitor:
   - **Tipo**: HTTP(S)
   - **URL**: `https://financasai.onrender.com/health`
   - **Intervalo**: 5 minutos
3. Isso mantém o backend acordado e evita o cold start

---

Feito com 💻 e IA para a sua liberdade financeira!
