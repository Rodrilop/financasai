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

Feito com 💻 e IA para a sua liberdade financeira!
