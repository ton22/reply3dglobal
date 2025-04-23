from nt import error
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from sqlalchemy.exc import IntegrityError
from app import app, db
from models import Movement, MovementType, Item, SubStock, InventoryItem, Project, PurchaseOrder, PurchaseOrderItem
from forms import MovementForm, PurchaseOrderForm, PurchaseOrderItemForm

# Routes for inventory movements and purchase orders
#Rotas para movimentos de estoque e pedidos de compra
@app.route('/movements')
@login_required
def movements():
    # Filter by movement type if requested
    #Filtro por tipo de movimento se solicitado
    type_filter = request.args.get('type', 'all')
    
    query = Movement.query
    
    if type_filter != 'all':
        query = query.filter(Movement.movement_type_id == type_filter)
    
    movements = query.order_by(Movement.created_at.desc()).all()
    movement_types = MovementType.query.all()
    
    context = {
        'title': 'Movimentações de Estoque',
        'movements': movements,
        'movement_types': movement_types,
        'type_filter': type_filter
    }
    
    return render_template('movements/movements.html', **context)

@app.route('/movements/new', methods=['GET', 'POST'])
@login_required
def new_movement():
    form = MovementForm()
    
    # Carregar todas as opções
    purchase_orders = PurchaseOrder.query.all()
    form.purchase_order_id.choices = [(0, 'Nenhum')] + [(po.id, po.po_number) for po in purchase_orders]
    form.item_id.choices = [(i.id, i.name) for i in Item.query.order_by(Item.name).all()]
    form.movement_type_id.choices = [(t.id, t.name) for t in MovementType.query.all()]
    form.source_substock_id.choices = [(0, '-')] + [(s.id, s.name) for s in SubStock.query.all()]
    form.destination_substock_id.choices = [(0, '-')] + [(s.id, s.name) for s in SubStock.query.all()]
    form.project_id.choices = [(0, 'Nenhum')] + [(p.id, p.name) for p in Project.query.filter_by(status='active').all()]

    # Limpar atributos readonly por padrão
    form.movement_type_id.render_kw = None
    form.item_id.render_kw = None
    form.purchase_order_id.render_kw = None
    form.destination_substock_id.render_kw = None

    # Verificar se veio de um pedido de compra
    purchase_order_id = request.args.get('purchase_order_id')
    item_id = request.args.get('item_id')
    
    if purchase_order_id and item_id:
        
        # Preencher o formulário com as informações do pedido
        po_item = PurchaseOrderItem.query.filter_by(
            purchase_order_id=purchase_order_id,
            item_id=item_id
        ).first()
        
        if po_item:
            # Definir o tipo de movimento como Entrada
            entry_type = MovementType.query.filter_by(name='Entrada').first()
            if entry_type:
                form.movement_type_id.data = entry_type.id
                form.movement_type_id.render_kw = {'readonly': True}
            
            # Definir o item
            form.item_id.data = item_id
            form.item_id.render_kw = {'readonly': True}
            
            # Definir a quantidade restante a receber
            remaining_quantity = po_item.quantity - po_item.received_quantity
            form.quantity.data = remaining_quantity
            
            # Definir o pedido de compra
            form.purchase_order_id.data = int(purchase_order_id)
            form.purchase_order_id.render_kw = {'readonly': True}
            
            # Definir o subestoque de destino como o subestoque padrão
            default_substock = SubStock.query.filter_by(name='Padrão').first()
            if default_substock:
                form.destination_substock_id.data = default_substock.id
                form.destination_substock_id.render_kw = {'readonly': True}

    if form.validate_on_submit():
        # Verificar se o movimento já existe baseado nos dados fornecidos
        existing_movement = Movement.query.filter(
            Movement.item_id == form.item_id.data,
            Movement.quantity == form.quantity.data,
            Movement.created_at >= datetime.utcnow() - timedelta(seconds=15)
        ).first()

        if existing_movement:
            flash('Esta movimentação já foi registrada.', 'warning')
            return redirect(url_for('movements'))

        try:
            # Validate quantity
            # Validar quantidade
            if form.quantity.data <= 0:
                flash('A quantidade deve ser maior que zero', 'danger')
                return render_template('movements/movement_form.html', form=form, title='Nova Movimentação')

            # Get the movement type to determine how to handle stock
            # Obtenha o tipo de movimento para determinar como lidar com o estoque
            movement_type = MovementType.query.get(form.movement_type_id.data)

            # Validate substocks based on movement type
            # Validar subestoques com base no tipo de movimento
            # if 'entrada' in movement_type.name.lower() and form.source_substock_id.data == 0:
            #     flash('Movimentações de entrada não devem ter origem', 'danger')
            #     return render_template('movements/movement_form.html', form=form, title='Nova Movimentação')
            if 'entrada' in movement_type.name.lower() and form.destination_substock_id.data == 0:
                # console.log('form.destination_substock_id.data', form.destination_substock_id.data)
                flash('Movimentações de entrada devem ter destino', 'danger')
                return render_template('movements/movement_form.html', form=form, title='Nova Movimentação')


            if 'saída' in movement_type.name.lower() and form.destination_substock_id.data != 0:
                flash('Movimentações de saída não devem ter destino', 'danger')
                return render_template('movements/movement_form.html', form=form, title='Nova Movimentação')

            if 'transferência' in movement_type.name.lower():
                if form.source_substock_id.data == 0 or form.destination_substock_id.data == 0:
                    flash('Transferências requerem origem e destino', 'danger')
                    return render_template('movements/movement_form.html', form=form, title='Nova Movimentação')
                if form.source_substock_id.data == form.destination_substock_id.data:
                    flash('Origem e destino devem ser diferentes', 'danger')
                    return render_template('movements/movement_form.html', form=form, title='Nova Movimentação')

            # Create the movement record
            movement = Movement(
                item_id=form.item_id.data,
                quantity=form.quantity.data,
                movement_type_id=form.movement_type_id.data,
                notes=form.notes.data,
                reference_code=form.reference_code.data,
                created_by_id=current_user.id
            )

            # Handle source and destination substocks
            if form.source_substock_id.data != 0:
                movement.source_substock_id = form.source_substock_id.data

            if form.destination_substock_id.data != 0:
                movement.destination_substock_id = form.destination_substock_id.data

            # Handle project association
            if form.project_id.data != 0:
                movement.project_id = form.project_id.data

            # Handle purchase order association
            if form.purchase_order_id.data != 0:
                movement.purchase_order_id = form.purchase_order_id.data
                
                # Update the received quantity in the purchase order
                po_item = PurchaseOrderItem.query.filter_by(
                    purchase_order_id=form.purchase_order_id.data,
                    item_id=form.item_id.data
                ).first()
                
                if po_item:
                    po_item.received_quantity += form.quantity.data
                    
                    # Check if all items are received
                    purchase_order = PurchaseOrder.query.get(form.purchase_order_id.data)
                    all_received = True
                    
                    for item in purchase_order.items:
                        if item.received_quantity < item.quantity:
                            all_received = False
                            break
                    
                    if all_received:
                        purchase_order.status = 'received'
                        purchase_order.received_at = datetime.utcnow()
                        db.session.add(purchase_order)

            # Update inventory based on movement type
            if movement_type.affects_stock:
                # For entries, increase stock in destination
                if movement.destination_substock_id and not movement.source_substock_id:
                    inv_item = InventoryItem.query.filter_by(
                        item_id=movement.item_id,
                        substock_id=movement.destination_substock_id
                    ).first()

                    if inv_item:
                        inv_item.quantity += movement.quantity
                    else:
                        inv_item = InventoryItem(
                            item_id=movement.item_id,
                            substock_id=movement.destination_substock_id,
                            quantity=movement.quantity
                        )
                        db.session.add(inv_item)

                # For exits, decrease stock in source
                elif movement.source_substock_id and not movement.destination_substock_id:
                    inv_item = InventoryItem.query.filter_by(
                        item_id=movement.item_id,
                        substock_id=movement.source_substock_id
                    ).first()

                    if inv_item:
                        if inv_item.quantity >= movement.quantity:
                            inv_item.quantity -= movement.quantity
                        else:
                            flash('Quantidade insuficiente no estoque de origem', 'danger')
                            return render_template('movements/movement_form.html', form=form, title='Nova Movimentação')
                    else:
                        flash('Item não encontrado no estoque de origem', 'danger')
                        return render_template('movements/movement_form.html', form=form, title='Nova Movimentação')

                # For transfers, decrease in source and increase in destination
                elif movement.source_substock_id and movement.destination_substock_id:
                    # Check source inventory
                    source_inv = InventoryItem.query.filter_by(
                        item_id=movement.item_id,
                        substock_id=movement.source_substock_id
                    ).first()

                    if not source_inv or source_inv.quantity < movement.quantity:
                        flash('Quantidade insuficiente no estoque de origem', 'danger')
                        return render_template('movements/movement_form.html', form=form, title='Nova Movimentação')

                    # Update source inventory
                    source_inv.quantity -= movement.quantity

                    # Update destination inventory
                    dest_inv = InventoryItem.query.filter_by(
                        item_id=movement.item_id,
                        substock_id=movement.destination_substock_id
                    ).first()

                    if dest_inv:
                        dest_inv.quantity += movement.quantity
                    else:
                        dest_inv = InventoryItem(
                            item_id=movement.item_id,
                            substock_id=movement.destination_substock_id,
                            quantity=movement.quantity
                        )
                        db.session.add(dest_inv)

            # Save the movement and all related changes
            db.session.add(movement)
            db.session.commit()

             # Se veio de um pedido de compra, atualizar o status
            if form.purchase_order_id.data:
                purchase_order = PurchaseOrder.query.get(form.purchase_order_id.data)
                if purchase_order:
                    po_item = PurchaseOrderItem.query.filter_by(
                        purchase_order_id=purchase_order.id,
                        item_id=form.item_id.data
                    ).first()
                    if po_item:
                        # Atualizar a quantidade recebida do item
                        po_item.received_quantity += form.quantity.data
                        db.session.add(po_item)
                        
                        # Atualizar o status do pedido
                        update_purchase_order_status(purchase_order.id)
            
            db.session.commit()
            
            # Redirecionar para a página de pedidos de compra
            return redirect(url_for('purchase_orders'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao criar movimentação: {str(e)}', 'danger')
            return render_template('movements/movement_form.html', form=form)
    else:
        return render_template('movements/movement_form.html', form=form)
@app.route('/movements/<int:movement_id>')
@login_required
def movement_detail(movement_id):
    movement = Movement.query.get_or_404(movement_id)
    
    context = {
        'title': f'Movimentação #{movement.id}',
        'movement': movement
    }
    
    return render_template('movements/movement_detail.html', **context)

@app.route('/purchase_orders')
@login_required
def purchase_orders():
    # Filter by status if requested
    status_filter = request.args.get('status', 'all')
    
    query = PurchaseOrder.query
    
    if status_filter != 'all':
        query = query.filter(PurchaseOrder.status == status_filter)
    
    purchase_orders = query.order_by(PurchaseOrder.created_at.desc()).all()
    
    context = {
        'title': 'Pedidos de Compra',
        'purchase_orders': purchase_orders,
        'status_filter': status_filter,
        'statuses': [
            {'value': 'all', 'label': 'Todos'},
            {'value': 'draft', 'label': 'Rascunho'},
            {'value': 'sent', 'label': 'Enviado'},
            {'value': 'received', 'label': 'Recebido'},
            {'value': 'cancelled', 'label': 'Cancelado'}
        ]
    }
    
    return render_template('movements/purchase_orders.html', **context)

@app.route('/purchase_orders/new', methods=['GET', 'POST'])
@login_required
def new_purchase_order():
    form = PurchaseOrderForm()
    
    if form.validate_on_submit():
        po_number = form.po_number.data if form.po_number.data else f'PO-{datetime.utcnow().strftime("%Y%m%d-%H%M%S")}'
        
        purchase_order = PurchaseOrder(
            po_number=po_number,
            supplier=form.supplier.data,
            status='draft',
            notes=form.notes.data,
            created_by_id=current_user.id
        )
        
        db.session.add(purchase_order)
        db.session.commit()
        
        flash('Pedido de compra criado com sucesso', 'success')
        return redirect(url_for('purchase_order_detail', po_id=purchase_order.id))
    
    return render_template('movements/purchase_order_form.html', form=form, title='Novo Pedido de Compra')

@app.route('/purchase_orders/auto_generate')
@login_required
def auto_generate_po():
    # Get items below minimum stock
    items = Item.query.all()
    items_to_order = []
    
    for item in items:
        total_stock = sum(inv_item.quantity for inv_item in item.inventory_items)
        if total_stock < item.minimum_stock:
            items_to_order.append({
                'item': item,
                'current_stock': total_stock,
                'to_order': item.minimum_stock - total_stock
            })
    
    if not items_to_order:
        flash('Não há itens abaixo do estoque mínimo para gerar pedido de compra', 'info')
        return redirect(url_for('purchase_orders'))
    
    # Create a new PO
    po_number = f'AUTO-{datetime.utcnow().strftime("%Y%m%d-%H%M%S")}'
    
    purchase_order = PurchaseOrder(
        po_number=po_number,
        supplier='A definir',
        status='draft',
        notes='Pedido gerado automaticamente para itens abaixo do estoque mínimo',
        created_by_id=current_user.id
    )
    
    db.session.add(purchase_order)
    db.session.flush()  # Get the ID without committing
    
    # Add items to the PO
    for item_data in items_to_order:
        po_item = PurchaseOrderItem(
            purchase_order_id=purchase_order.id,
            item_id=item_data['item'].id,
            quantity=item_data['to_order']
        )
        db.session.add(po_item)
    
    db.session.commit()
    
    flash(f'Pedido de compra {po_number} gerado com sucesso para {len(items_to_order)} itens', 'success')
    return redirect(url_for('purchase_order_detail', po_id=purchase_order.id))

@app.route('/purchase_orders/<int:po_id>')
@login_required
def purchase_order_detail(po_id):
    purchase_order = PurchaseOrder.query.get_or_404(po_id)
    
    context = {
        'title': f'Pedido de Compra: {purchase_order.po_number}',
        'purchase_order': purchase_order
    }
    
    return render_template('movements/purchase_order_detail.html', **context)

@app.route('/purchase_orders/<int:po_id>/add_item', methods=['GET', 'POST'])
@login_required
def add_po_item(po_id):
    purchase_order = PurchaseOrder.query.get_or_404(po_id)
    form = PurchaseOrderItemForm()
    form.item_id.choices = [(item.id, item.name) for item in Item.query.all()]

    # Calcular o valor total dos itens não recebidos
    total_pending_value = sum(
        (item.quantity - item.received_quantity) * item.unit_price
        for item in purchase_order.items
        if item.quantity > item.received_quantity
    )

    if form.validate_on_submit():
        new_item = PurchaseOrderItem(
            quantity=form.quantity.data,
            unit_price=form.unit_price.data,
            purchase_order_id=purchase_order.id,
            item_id=form.item_id.data
        )
        db.session.add(new_item)
        db.session.commit()
        flash('Item adicionado ao pedido com sucesso!', 'success')
        return redirect(url_for('purchase_order_detail', po_id=purchase_order.id))

    return render_template(
        'movements/po_item_form.html',
        form=form,
        purchase_order=purchase_order,
        total_pending_value=total_pending_value
    )

@app.route('/purchase_orders/<int:po_id>/edit_item/<int:item_id>', methods=['GET', 'POST'])
@login_required
def edit_po_item(po_id, item_id):
    purchase_order = PurchaseOrder.query.get_or_404(po_id)
    
    # Can't modify if not in draft status
    if purchase_order.status != 'draft':
        flash('Este pedido de compra não pode ser modificado no status atual', 'danger')
        return redirect(url_for('purchase_order_detail', po_id=po_id))
    
    po_item = PurchaseOrderItem.query.filter_by(
        purchase_order_id=po_id,
        item_id=item_id
    ).first_or_404()
    
    form = PurchaseOrderItemForm(obj=po_item)
    form.item_id.choices = [(po_item.item_id, po_item.item.name)]
    
    if form.validate_on_submit():
        po_item.quantity = form.quantity.data
        
        db.session.commit()
        
        flash('Item atualizado com sucesso', 'success')
        return redirect(url_for('purchase_order_detail', po_id=po_id))
    
    return render_template('movements/po_item_form.html', form=form, purchase_order=purchase_order, title='Editar Item do Pedido')

@app.route('/purchase_orders/<int:po_id>/remove_item/<int:item_id>')
@login_required
def remove_po_item(po_id, item_id):
    purchase_order = PurchaseOrder.query.get_or_404(po_id)
    
    # Can't modify if not in draft status
    if purchase_order.status != 'draft':
        flash('Este pedido de compra não pode ser modificado no status atual', 'danger')
        return redirect(url_for('purchase_order_detail', po_id=po_id))
    
    po_item = PurchaseOrderItem.query.filter_by(
        purchase_order_id=po_id,
        item_id=item_id
    ).first_or_404()
    
    db.session.delete(po_item)
    db.session.commit()
    
    flash('Item removido do pedido de compra', 'success')
    return redirect(url_for('purchase_order_detail', po_id=po_id))

@app.route('/purchase_orders/<int:po_id>/status/<status>')
@login_required
def update_po_status(po_id, status):
    purchase_order = PurchaseOrder.query.get_or_404(po_id)
    
    valid_transitions = {
        'draft': ['sent', 'cancelled'],
        'sent': ['received', 'cancelled'],
        'received': [],
        'cancelled': []
    }
    
    if status in valid_transitions[purchase_order.status]:
        purchase_order.status = status
        
        if status == 'sent':
            purchase_order.sent_at = datetime.utcnow()
        elif status == 'received':
            purchase_order.received_at = datetime.utcnow()
        
        db.session.commit()
        flash(f'Status do pedido de compra atualizado para {status}', 'success')
    else:
        flash('Transição de status inválida', 'danger')
    
    return redirect(url_for('purchase_order_detail', po_id=po_id))

def update_purchase_order_status(purchase_order_id):
    """Atualiza o status de um pedido de compra com base nas quantidades recebidas."""
    purchase_order = PurchaseOrder.query.get(purchase_order_id)
    if not purchase_order:
        return
    
    # Verificar se todos os itens foram recebidos
    all_received = all(item.received_quantity >= item.quantity 
                      for item in purchase_order.items)
    
    if all_received:
        purchase_order.status = 'received'
        purchase_order.received_at = datetime.utcnow()
    else:
        # Se algum item foi recebido, mas não todos, manter como sent
        if any(item.received_quantity > 0 for item in purchase_order.items):
            purchase_order.status = 'sent'
        else:
            # Se nenhum item foi recebido, manter como draft
            purchase_order.status = 'draft'
    
    # Atualizar a quantidade total recebida do pedido
    purchase_order.total_received = sum(item.received_quantity for item in purchase_order.items)
    
    db.session.add(purchase_order)
    db.session.commit()