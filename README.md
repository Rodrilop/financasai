# 📊 FinançasAI

O **FinançasAI** é um assistente financeiro pessoal completo, com um design moderno e responsivo, focado em ajudar você a gerenciar suas despesas, entender seus hábitos de consumo e receber dicas e estratégias de investimentos personalizadas impulsionadas por **Inteligência Artificial (Google Gemini)**.

---

## 🌟 Principais Funcionalidades

- **Gerenciamento de Despesas**: Adicione, edite, categorize e priorize ("Essencial", "Importante", "Opcional") seus gastos mensais. Conta com exclusão em massa e filtros avançados.
- **Análise Inteligente de IA**: Integração nativa com a API do Google Gemini (modelo 2.5-flash) para avaliar a sua saúde financeira, sugerir cortes de despesas reais com base nos seus dados e montar dicas de investimentos baseadas no seu perfil.
- **Painel de Investimentos**: Recomendações de alocação de carteira (Ações, FIIs, Tesouro Selic, CDBs) baseadas no seu perfil (Conservador, Moderado, Agressivo).
- **Design Totalmente Responsivo**: Layout premium em "Dark Mode" com navegação inferior (*Bottom Navigation*) quando acessado por dispositivos móveis, garantindo ergonomia nativa para celulares de todas as resoluções.
- **Dashboard e Gráficos**: Resumo visual dos seus gastos por categoria usando o `recharts`.

---

## 🛠️ Tecnologias Utilizadas

### Backend
- **[Python 3](https://www.python.org/)**
- **[FastAPI](https://fastapi.tiangolo.com/)**: Construção da API super-rápida.
- **[SQLite](https://sqlite.org/)**: Banco de dados relacional leve e local.
- **[Google Generative AI](https://aistudio.google.com/)**: Integração com o Google Gemini.

### Frontend
- **[React 18](https://react.dev/)** + **[Vite](https://vitejs.dev/)**: Framework rápido de desenvolvimento UI.
- **React Router DOM**: Navegação e roteamento.
- **Recharts**: Criação de gráficos financeiros interativos.
- **Vanilla CSS**: Estilização altamente customizada e totalmente responsiva.

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

Crie um arquivo `.env` na pasta `backend` com a sua chave da API do Google Gemini:
```env
GEMINI_API_KEY=sua_chave_aqui
GEMINI_MODEL=gemini-2.5-flash
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

## 🔒 Segurança de Dados

- **Proteção da Chave da API**: O repositório já conta com o arquivo `.gitignore` configurado. Lembre-se de NUNCA dar *commit* ou subir seu arquivo `backend/.env` para o GitHub público, pois ele contém sua chave do Gemini.
- **Privacidade do Banco de Dados**: Seus gastos e informações ficam armazenados localmente no arquivo `financasai.db`, garantindo que apenas você (e o seu próprio computador) tenha os dados da sua vida financeira.

---

Feito com 💻 e IA para sua liberdade financeira!
