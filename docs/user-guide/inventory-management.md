# Gerenciamento de Estoque

Este guia abrange as funcionalidades de gerenciamento de estoque do ThreeDStock.

## Itens

### Adicionando Novos Itens

Para adicionar um novo item ao estoque:

1. Navegue até Estoque > Itens
2. Clique em "Novo Item"
3. Preencha as informações obrigatórias:
   - Nome
   - Tipo de Item
   - Unidade de Medida
   - Nível Mínimo de Estoque
4. Campos opcionais:
   - Descrição
   - SKU (gerado automaticamente se deixado em branco)
   - Código de Barras (gerado automaticamente se deixado em branco)
   - Cor
   - Marca

### Gerenciando Níveis de Estoque

Os níveis de estoque são rastreados por subestoque. Para visualizar ou modificar os níveis de estoque:

1. Acesse a página de detalhes do item
2. Visualize os níveis atuais de estoque em todos os subestoques
3. Use a funcionalidade de Movimentações para ajustar os níveis de estoque

### Alertas de Estoque Baixo

O sistema monitora automaticamente os níveis de estoque e fornece alertas quando:

- O estoque total cai abaixo do nível mínimo
- O estoque em um subestoque específico está baixo

## Subestoques

### Criando Subestoques

Subestoques representam localizações físicas ou departamentos onde o estoque é armazenado.

Para criar um novo subestoque:

1. Navegue até Estoque > Subestoques
2. Clique em "Novo Subestoque"
3. Forneça:
   - Nome
   - Descrição
   - Localização

### Gerenciando Subestoques

Cada subestoque pode ser gerenciado independentemente, permitindo:

- Visualização do inventário atual
- Rastreamento de movimentações
- Monitoramento de níveis de estoque

### Transferências entre Subestoques

Para transferir itens entre subestoques:

1. Acesse a seção de Movimentações
2. Selecione "Nova Transferência"
3. Escolha:
   - Item a ser transferido
   - Quantidade
   - Subestoque de origem
   - Subestoque de destino
4. Adicione observações se necessário
5. Confirme a transferência

## Inventário

### Realização de Inventário Físico

Para realizar um inventário físico:

1. Gere um relatório de estoque atual
2. Realize a contagem física
3. Registre as diferenças encontradas
4. Faça os ajustes necessários através de movimentações

### Ajustes de Estoque

Para corrigir discrepâncias no estoque:

1. Acesse a página do item
2. Utilize a função de ajuste de estoque
3. Registre o motivo do ajuste
4. Confirme as alterações

## Relatórios de Estoque

### Tipos de Relatórios Disponíveis

- Posição atual de estoque
- Itens abaixo do estoque mínimo
- Movimentações por período
- Inventário por subestoque
- Histórico de ajustes

### Gerando Relatórios

1. Acesse a seção de Relatórios
2. Selecione o tipo de relatório
3. Defina os filtros desejados
4. Escolha o formato de saída (PDF, Excel, etc.)
5. Gere o relatório
