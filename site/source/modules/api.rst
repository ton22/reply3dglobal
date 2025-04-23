API do Sistema
============

O sistema fornece uma API para integração com outros sistemas.

Endpoints para Gráficos
---------------------

Endpoints que fornecem dados para os gráficos do sistema:

``/api/chart/inventory_value``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Retorna dados do valor do inventário por substock:

.. code-block:: json

    {
        "labels": ["Estoque Principal", "Almoxarifado", "Produção"],
        "datasets": [{
            "label": "Número de Itens por Sub-estoque",
            "data": [150, 75, 25],
            "backgroundColor": ["#FF6384", "#36A2EB", "#FFCE56"]
        }]
    }

``/api/chart/movements_by_type``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Retorna estatísticas de movimentações por tipo:

.. code-block:: json

    {
        "labels": ["Entrada", "Saída", "Transferência"],
        "datasets": [{
            "label": "Movimentações por Tipo",
            "data": [45, 32, 18],
            "backgroundColor": ["#4BC0C0", "#FF6384", "#36A2EB"]
        }]
    }

``/api/chart/projects_by_status``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Retorna contagem de projetos por status:

.. code-block:: json

    {
        "labels": ["Ativos", "Concluídos", "Cancelados"],
        "datasets": [{
            "label": "Projetos por Status",
            "data": [12, 8, 3],
            "backgroundColor": ["#36A2EB", "#4BC0C0", "#FF6384"]
        }]
    }

Autenticação
-----------

Todas as chamadas à API requerem autenticação. O sistema usa autenticação baseada em sessão
através do Flask-Login.

Formato de Resposta
-----------------

Todas as respostas são retornadas no formato JSON com os seguintes campos padrão:

.. code-block:: json

    {
        "status": "success",
        "data": {},
        "message": "Operação realizada com sucesso"
    }

Em caso de erro:

.. code-block:: json

    {
        "status": "error",
        "error": "Descrição do erro",
        "code": 400
    }

Códigos de Status
---------------

* 200: Sucesso
* 400: Erro de requisição
* 401: Não autorizado
* 404: Não encontrado
* 500: Erro interno do servidor 