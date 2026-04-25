# 📊 FinançasAI

O **FinançasAI** é um assistente financeiro pessoal completo, com um design moderno e responsivo, focado em ajudar você a gerenciar suas despesas, entender seus hábitos de consumo e receber dicas e estratégias de investimentos personalizadas impulsionadas por **Inteligência Artificial (Google Gemini)**.

---

## 🌟 Principais Funcionalidades

- **Gerenciamento de Despesas**: Adicione, edite, categorize e priorize ("Essencial", "Importante", "Opcional") seus gastos mensais. Conta com exclusão em massa e filtros avançados.
- **Sistema de Autenticação Seguro**: Login e registro com JWT e senhas hasheadas utilizando `bcrypt`.
- **Análise Inteligente de IA**: Integração nativa com a API do Google Gemini (modelo 2.5-flash) para avaliar a sua saúde financeira, sugerir cortes de despesas reais com base nos seus dados e montar dicas de investimentos baseadas no seu perfil.
- **Painel de Investimentos**: Recomendações de alocação de carteira (Ações, FIIs, Tesouro Selic, CDBs) baseadas no seu perfil (Conservador, Moderado, Agressivo).
- **Design Totalmente Responsivo**: Layout premium em "Dark Mode" com navegação inferior (*Bottom Navigation*) quando acessado por dispositivos móveis, garantindo ergonomia nativa para celulares de todas as resoluções.
- **Dashboard e Gráficos**: Resumo visual dos seus gastos por categoria usando o `recharts`.

---

## 🛠️ Tecnologias Utilizadas

### Backend
- **[Python 3](https://www.python.org/)**
- **[FastAPI](https://fastapi.tiangolo.com/)**: Construção da API super-rápida.
- **[Turso / libSQL](https://turso.tech/)**: Banco de dados Edge-Cloud escalável (com fallback local SQLite).
- **[Google Generative AI](https://aistudio.google.com/)**: Integração com o Google Gemini.
- **Pytest**: Suíte de testes automatizados do backend.

### Frontend
- **[React 18](https://react.dev/)** + **[Vite](https://vitejs.dev/)**: Framework rápido de desenvolvimento UI.
- **React Router DOM**: Navegação, roteamento e rotas privadas protegidas por AuthContext.
- **Recharts**: Criação de gráficos financeiros interativos.
- **Vitest**: Testes unitários do frontend.

---

## 🚀 Como Executar o Projeto Localmente

### 1. Clonando o Repositório
```bash
git clone https://github.com/SEU_USUARIO/financasai.git
cd financasai
```

### 2. Configurando o Backend (API)
Navegue para a pasta do backend:
```bash
cd backend
```

Instale as dependências num ambiente Python:
```bash
# Recomendado: Crie e ative um ambiente virtual (venv)
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

pip install -r requirements.txt
```

Crie um arquivo `.env` na pasta `backend` com as suas chaves:
```env
GEMINI_API_KEY=sua_chave_gemini_aqui
GEMINI_MODEL=gemini-2.5-flash
JWT_SECRET_KEY=uma_chave_secreta_forte_aqui
TURSO_DATABASE_URL= # (opcional) sua_url_turso_aqui
TURSO_AUTH_TOKEN= # (opcional) seu_token_turso_aqui
```

Inicie o servidor local do FastAPI:
```bash
python -m uvicorn main:app --reload --port 8000
```
A documentação da sua API (Swagger) estará disponível em: `http://localhost:8000/docs`.

### 3. Configurando o Frontend
Abra um **novo terminal**, volte para a raiz do projeto e acesse a pasta do frontend:
```bash
cd frontend
```

Instale as dependências do Node:
```bash
npm install
```

Inicie o servidor de desenvolvimento do Vite:
```bash
npm run dev
```
Acesse no seu navegador ou pelo celular (através do seu IP local): `http://localhost:5173/`.

---

## 🔒 Segurança de Dados (Production-Ready)

- **Proteção de Chaves**: O repositório já conta com o arquivo `.gitignore` configurado e tem histórico de Git auditado. Lembre-se de NUNCA dar *commit* ou subir seu arquivo `backend/.env`.
- **Autenticação**: Rotas protegidas via JWT (`JSON Web Tokens`).
- **Validação e Limites**: O backend conta com Rate Limiting (`slowapi`) que evita abusos nos limites de tokens da IA e injeções nos dados usando metadados Pydantic.
- **CI/CD Pipeline**: GitHub actions configurado para rodar `pytest` e `vitest` em todo commit que for enviado para o repositório principal.

---

Feito com 💻 e IA para sua liberdade financeira!
