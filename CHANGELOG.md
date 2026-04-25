# Changelog

## [1.0.0] - 2026-04-24
### Added
- **Autenticação:** Sistema de Login e Registro de usuários com senhas criptografadas (bcrypt) e tokens JWT.
- **Banco de Dados em Nuvem:** Suporte ao Turso (libSQL) para armazenamento de dados centralizado, com fallback para SQLite local.
- **Integração de IA:** Recomendações financeiras automáticas e chat integrado usando Google Gemini 2.5 Flash.
- **Responsividade:** Design mobile-first com barra de navegação inferior (Bottom Navigation) otimizada para smartphones.
- **Testes Automatizados:** Cobertura de testes unitários para a API Backend (pytest) e Componentes Frontend (vitest).
- **CI/CD:** Pipeline automatizado no GitHub Actions para garantir qualidade de código em novas integrações.
- **Segurança:** Rate limiting implementado via `slowapi` e validação restrita de dados via Pydantic.

### Changed
- Refatoração dos modelos Pydantic usando `Field` para validação minuciosa (garantia de valores não negativos, limite de caracteres).
- Separação da lógica de Banco de Dados (`database.py`) e Autenticação (`auth.py`).

### Security
- Limpeza do histórico do Git para remover completamente credenciais (`.env`) expostas acidentalmente no passado.
- Senhas de usuário agora são caculadas em hash com o algoritmo bcrypt e nunca salvas em texto limpo.
- Endpoints da API protegidos com JWT (JSON Web Tokens).
