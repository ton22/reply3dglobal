# Documentação ThreeDStock

Bem-vindo à documentação do ThreeDStock. O ThreeDStock é um sistema abrangente de gerenciamento de estoque projetado para rastrear itens, gerenciar movimentações de estoque e administrar projetos.

## Principais Características

- **Gerenciamento de Estoque**: Rastreie itens em múltiplos subestoques com informações detalhadas, incluindo SKUs, códigos de barras e níveis mínimos de estoque
- **Movimentações de Estoque**: Registre e acompanhe movimentações de itens entre diferentes subestoques
- **Gerenciamento de Projetos**: Gerencie projetos e suas necessidades de inventário associadas
- **Pedidos de Compra**: Crie e acompanhe pedidos de compra para reposição de estoque
- **Relatórios**: Gere diversos relatórios, incluindo status do inventário, movimentações e alertas de estoque baixo
- **Gerenciamento de Usuários**: Controle de acesso baseado em funções e autenticação de usuários
- **Suporte Offline**: Recursos de Progressive Web App (PWA) para acesso offline

## Arquitetura do Sistema

O aplicativo é construído utilizando:

- **Backend**: Flask (Python)
- **Banco de Dados**: SQLAlchemy com SQLite
- **Frontend**: HTML, CSS, JavaScript com Bootstrap
- **Autenticação**: Flask-Login
- **Documentação**: MkDocs

## Início Rápido

1. Clone o repositório
2. Instale as dependências: `pip install -r requirements.txt`
3. Inicialize o banco de dados: `flask db upgrade`
4. Execute a aplicação: `python run.py`

Para instruções detalhadas de configuração, consulte o guia [Primeiros Passos](user-guide/getting-started.md).

## Estrutura da Documentação

- **Guia do Usuário**: Instruções para uso da aplicação
- **Guia do Administrador**: Administração e configuração do sistema
- **Guia do Desenvolvedor**: Documentação da API e diretrizes de desenvolvimento
- **Solução de Problemas**: Problemas comuns e soluções

## Suporte

Para suporte, por favor, abra uma issue em nosso repositório GitHub ou entre em contato com o administrador do sistema.

## Recursos Adicionais

### Tutoriais em Vídeo
- Configuração inicial do sistema
- Gerenciamento básico de estoque
- Criação e gestão de projetos
- Geração de relatórios

### Melhores Práticas
- Organização de subestoques
- Nomenclatura de itens
- Controle de movimentações
- Gestão de pedidos de compra

### Requisitos do Sistema
- Python 3.8 ou superior
- SQLite 3
- Navegador web moderno
- 2GB de RAM
- 500MB de espaço em disco
