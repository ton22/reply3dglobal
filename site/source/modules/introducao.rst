Introdução
===========

Sobre o Sistema
--------------

O Sistema de Gestão de Estoque é uma aplicação web desenvolvida em Python usando o framework Flask.
Foi projetado para atender às necessidades de controle de estoque de empresas, oferecendo uma
interface intuitiva e funcionalidades completas para gerenciamento de inventário.

Tecnologias Utilizadas
---------------------

* **Backend**: Python com Flask
* **Banco de Dados**: SQLAlchemy ORM
* **Frontend**: HTML5, CSS3, JavaScript
* **UI Framework**: Bootstrap
* **Gráficos**: Chart.js
* **Exportação**: jsPDF, CSV

Arquitetura do Sistema
--------------------

O sistema segue uma arquitetura MVC (Model-View-Controller):

* **Models**: Definição das entidades e relacionamentos do banco de dados
* **Views**: Templates HTML para renderização das páginas
* **Controllers**: Rotas e lógica de negócio em Python

Estrutura de Diretórios
----------------------

.. code-block:: text

    ThreeDStock/
    ├── app/
    │   ├── __init__.py
    │   ├── models.py
    │   ├── forms.py
    │   └── routes/
    ├── templates/
    │   ├── base.html
    │   ├── inventory/
    │   ├── movements/
    │   └── reports/
    ├── static/
    │   ├── css/
    │   ├── js/
    │   └── img/
    ├── migrations/
    └── docs/

Requisitos do Sistema
-------------------

* Python 3.8 ou superior
* Flask e suas dependências
* SQLAlchemy
* Outras bibliotecas Python conforme requirements.txt 