Rotas do Sistema
===============

Esta seção documenta as principais rotas (endpoints) do sistema.

Inventário
---------

.. automodule:: inventory
   :members:
   :undoc-members:
   :show-inheritance:

Rotas para gerenciamento de itens e estoque:

* ``/inventory`` - Lista de itens
* ``/inventory/new`` - Criar novo item
* ``/inventory/<item_id>`` - Detalhes do item
* ``/inventory/<item_id>/edit`` - Editar item
* ``/inventory/<item_id>/delete`` - Excluir item

Movimentações
------------

.. automodule:: movements
   :members:
   :undoc-members:
   :show-inheritance:

Rotas para controle de movimentações:

* ``/movements`` - Lista de movimentações
* ``/movements/new`` - Nova movimentação
* ``/movements/<movement_id>`` - Detalhes da movimentação
* ``/movements/types`` - Tipos de movimentação

Pedidos de Compra
---------------

.. automodule:: purchase_orders
   :members:
   :undoc-members:
   :show-inheritance:

Rotas para gerenciamento de pedidos:

* ``/purchase_orders`` - Lista de pedidos
* ``/purchase_orders/new`` - Novo pedido
* ``/purchase_orders/<po_id>`` - Detalhes do pedido
* ``/purchase_orders/<po_id>/edit`` - Editar pedido
* ``/purchase_orders/<po_id>/items`` - Itens do pedido

Projetos
-------

.. automodule:: projects
   :members:
   :undoc-members:
   :show-inheritance:

Rotas para gestão de projetos:

* ``/projects`` - Lista de projetos
* ``/projects/new`` - Novo projeto
* ``/projects/<project_id>`` - Detalhes do projeto
* ``/projects/<project_id>/edit`` - Editar projeto

Relatórios
---------

.. automodule:: reports
   :members:
   :undoc-members:
   :show-inheritance:

Rotas para geração de relatórios:

* ``/reports`` - Dashboard principal
* ``/reports/inventory`` - Relatório de inventário
* ``/reports/movements`` - Relatório de movimentações
* ``/reports/low_stock`` - Relatório de estoque baixo
* ``/reports/projects`` - Relatório de projetos
* ``/reports/purchase_orders`` - Relatório de pedidos 