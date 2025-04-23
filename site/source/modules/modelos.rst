Modelos do Sistema
================

Esta seção documenta os modelos (models) do sistema, que representam as entidades
e seus relacionamentos no banco de dados.

Item
----

.. autoclass:: models.Item
   :members:
   :undoc-members:
   :show-inheritance:

Representa um item no estoque, com suas propriedades e métodos:

* Nome e descrição
* SKU (Stock Keeping Unit)
* Tipo de item
* Unidade de medida
* Estoque mínimo
* Métodos para cálculo de estoque

SubStock
--------

.. autoclass:: models.SubStock
   :members:
   :undoc-members:
   :show-inheritance:

Representa uma localização ou subdivisão do estoque:

* Nome e descrição
* Tipo de substock
* Itens armazenados

Movement
--------

.. autoclass:: models.Movement
   :members:
   :undoc-members:
   :show-inheritance:

Registra movimentações de itens no estoque:

* Tipo de movimento
* Item movimentado
* Quantidade
* Origem e destino
* Data e hora
* Referências (projeto, pedido)

PurchaseOrder
------------

.. autoclass:: models.PurchaseOrder
   :members:
   :undoc-members:
   :show-inheritance:

Gerencia pedidos de compra:

* Número do pedido
* Fornecedor
* Status
* Itens e quantidades
* Data de criação/modificação

Project
-------

.. autoclass:: models.Project
   :members:
   :undoc-members:
   :show-inheritance:

Controla projetos que utilizam itens do estoque:

* Nome e descrição
* Status
* Data de início/fim
* Itens utilizados 