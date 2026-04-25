# 📊 FinançasAI

O **FinançasAI** é um assistente financeiro pessoal completo, com design moderno em dark mode e totalmente responsivo. Ajuda você a gerenciar despesas, entender seus hábitos de consumo e receber recomendações de investimento personalizadas com **Inteligência Artificial (Google Gemini)**.

---

## 🌟 Principais Funcionalidades

- **Gerenciamento de Despesas** — Adicione, edite, categorize e priorize gastos ("Essencial", "Importante", "Opcional"), com exclusão em massa e filtros avançados.
- **Autenticação Segura** — Login e registro com JWT e senhas hasheadas via `bcrypt`.
- **Análise com IA** — Integração com a API do Google Gemini (gemini-2.5-flash) para avaliar saúde financeira, sugerir cortes e recomendar investimentos com base no seu perfil.
- **Painel de Investimentos** — Alocação de carteira (Ações, FIIs, Tesouro Selic, CDBs) adaptada ao perfil: Conservador, Moderado ou Agressivo.
- **Dashboard e Gráficos** — Resumo visual dos gastos por categoria usando `recharts`.
- **Design Responsivo** — Layout premium em dark mode com Bottom Navigation em dispositivos móveis.

---

## 🛠️ Tecnologias Utilizadas

### Backend
- **Python 3.10** com **FastAPI** e **Uvicorn**
- **SQLite** (padrão local) com suporte opcional ao **Turso / libSQL** (Edge-Cloud)
- **Google Gemini** via `google-generativeai`
- **JWT** via `pyjwt` + senhas com `passlib[bcrypt]` (bcrypt 4.0.1)
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
GEMINI_API_KEY=sua_chave_gemini_aqui
GEMINI_MODEL=gemini-2.5-flash
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
GEMINI_API_KEY=sua_chave_gemini_aqui
GEMINI_MODEL=gemini-2.5-flash
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
4. Copie a URL do serviço: `https://financasai-backend.onrender.com`

### Passo 3 — Frontend (Vercel)

1. Acesse [vercel.com](https://vercel.com) e conecte seu repositório GitHub
2. Crie um novo projeto → selecione o repositório → defina:
   - **Root Directory**: `frontend`
   - **Framework Preset**: Vite (detectado automaticamente)
3. Em **Environment Variables**, adicione:
   ```
   VITE_API_URL=https://financasai-backend.onrender.com
   ```
4. Clique em **Deploy** — sua URL será `https://financasai.vercel.app`

### Passo 4 — Anti-sleep (UptimeRobot)

1. Crie uma conta em [uptimerobot.com](https://uptimerobot.com)
2. Crie um novo monitor:
   - **Tipo**: HTTP(S)
   - **URL**: `https://financasai-backend.onrender.com/health`
   - **Intervalo**: 5 minutos
3. Isso mantém o backend acordado e evita o cold start

---

Feito com 💻 e IA para a sua liberdade financeira!
