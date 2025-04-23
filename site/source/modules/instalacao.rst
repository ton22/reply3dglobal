Instalação
==========

Este guia descreve como instalar e configurar o sistema.

Requisitos
---------

* Python 3.8 ou superior
* pip (gerenciador de pacotes Python)
* Banco de dados PostgreSQL
* Git

Instalação
---------

1. Clone o repositório:

   .. code-block:: bash

      git clone https://github.com/seu-usuario/ThreeDStock.git
      cd ThreeDStock

2. Crie um ambiente virtual:

   .. code-block:: bash

      python -m venv venv
      source venv/bin/activate  # Linux/Mac
      venv\Scripts\activate     # Windows

3. Instale as dependências:

   .. code-block:: bash

      pip install -r requirements.txt

4. Configure as variáveis de ambiente:

   Crie um arquivo `.env` na raiz do projeto:

   .. code-block:: text

      FLASK_APP=app
      FLASK_ENV=development
      DATABASE_URL=postgresql://user:password@localhost/dbname
      SECRET_KEY=sua-chave-secreta

Configuração do Banco de Dados
---------------------------

1. Crie o banco de dados:

   .. code-block:: sql

      CREATE DATABASE threeDStock;

2. Execute as migrações:

   .. code-block:: bash

      flask db upgrade

3. (Opcional) Carregue dados iniciais:

   .. code-block:: bash

      flask seed-db

Executando o Sistema
-----------------

1. Inicie o servidor de desenvolvimento:

   .. code-block:: bash

      flask run

2. Acesse o sistema:

   Abra o navegador e acesse ``http://localhost:5000``

3. Faça login com as credenciais padrão:

   * Usuário: admin
   * Senha: admin123

   **Importante**: Altere a senha após o primeiro login!

Configurações Adicionais
----------------------

Configuração de E-mail
~~~~~~~~~~~~~~~~~~~~

Para habilitar o envio de e-mails (alertas, notificações):

.. code-block:: python

   MAIL_SERVER = 'smtp.gmail.com'
   MAIL_PORT = 587
   MAIL_USE_TLS = True
   MAIL_USERNAME = 'seu-email@gmail.com'
   MAIL_PASSWORD = 'sua-senha'

Configuração de Upload de Arquivos
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Para configurar o upload de arquivos:

.. code-block:: python

   UPLOAD_FOLDER = 'uploads'
   ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg'} 