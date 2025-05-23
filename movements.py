from nt import error
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from sqlalchemy.exc import IntegrityError
from app import app, db
from models import Movement, MovementType, Item, SubStock, InventoryItem, Project, PurchaseOrder, PurchaseOrderItem
from forms import MovementForm, PurchaseOrderForm, PurchaseOrderItemForm
from settings import get_setting

# Routes for inventory movements and purchase orders
#Rotas para movimentos de estoque e pedidos de compra
@app.route('/movements')
@login_required
def movements():
    type_filter = request.args.get('type', 'all')
    query = Movement.query
    
    if type_filter != 'all':
        query = query.filter(Movement.movement_type_id == type_filter)
    
    movements = query.order_by(Movement.created_at.desc()).all()
    movement_types = MovementType.query.all()
    
    return render_template('movements/movements.html',
                         title='Movimentações',
                         movements=movements,
                         movement_types=movement_types,
                         type_filter=type_filter)


@app.route('/api/items/<int:item_id>')
@login_required
def get_item_details(item_id):
    item = Item.query.get_or_404(item_id)
    return jsonify({
        'id': item.id,
        'name': item.name,
        'sku': item.sku,
        'color': item.color,
        'brand': {'id': item.brand.id, 'name': item.brand.name} if item.brand else None
    })

@app.route('/movements/new', methods=['GET', 'POST'])
@login_required
def new_movement():
    form = MovementForm()

    # Carregar opções para os selects
    items = Item.query.order_by(Item.name).all()
    movement_types = MovementType.query.all()
    substocks = SubStock.query.all()
    active_projects = Project.query.filter_by(status='active').all()
    purchase_orders = PurchaseOrder.query.filter(PurchaseOrder.status != 'cancelled').all()

    # Configurar choices dos campos select
    form.item_id.choices = [(i.id, i.name) for i in items]
    form.movement_type_id.choices = [(t.id, t.name) for t in movement_types]
    form.source_substock_id.choices = [(0, '-')] + [(s.id, s.name) for s in substocks]
    form.destination_substock_id.choices = [(0, '-')] + [(s.id, s.name) for s in substocks]
    form.project_id.choices = [(0, 'Nenhum')] + [(p.id, p.name) for p in active_projects]
    form.purchase_order_id.choices = [(0, 'Nenhum')] + [(po.id, po.po_number) for po in purchase_orders]

    if request.method == 'GET':
        # Obter parâmetros da URL
        purchase_order_id = request.args.get('purchase_order_id')
        item_id = request.args.get('item_id')
        movement_type = request.args.get('movement_type', '').lower()
        source_substock_id = request.args.get('source_substock_id')
        destination_substock_id = request.args.get('destination_substock_id')
        quantity = request.args.get('quantity')
        
        try:
            # Verificar se veio de um pedido de compra
            if purchase_order_id and item_id:
                purchase_order_id = int(purchase_order_id)
                item_id = int(item_id)
                
                # Buscar informações do pedido
                po_item = PurchaseOrderItem.query.filter_by(
                    purchase_order_id=purchase_order_id,
                    item_id=item_id
                ).first()
                
                if po_item:
                    # Configurar formulário para recebimento
                    entry_type = MovementType.query.filter_by(name='Entrada').first()
                    if entry_type:
                        form.movement_type_id.data = entry_type.id
                        form.movement_type_id.render_kw = {'readonly': True}
                    
                    form.item_id.data = item_id
                    form.item_id.render_kw = {'readonly': True}
                    
                    form.quantity.data = po_item.quantity - po_item.received_quantity
                    form.purchase_order_id.data = purchase_order_id
                    
                    # Definir subestoque padrão para entrada
                    default_substock = SubStock.query.filter_by(name='Padrão').first()
                    if default_substock:
                        form.destination_substock_id.data = default_substock.id
                else:
                    flash('Item do pedido de compra não encontrado.', 'danger')
                    
            # Verificar se veio da lista de itens
            elif item_id:
                item_id = int(item_id)
                item = Item.query.get(item_id)
                if item:
                    # Configurar formulário com o item selecionado
                    form.item_id.data = item_id
                    
                    # Processar quantidade se fornecida
                    if quantity:
                        try:
                            form.quantity.data = float(quantity)
                        except ValueError:
                            flash('Quantidade inválida.', 'warning')
                    
                    # Determinar o tipo de movimento baseado no parâmetro
                    if movement_type == 'saida':
                        move_type = MovementType.query.filter_by(name='Saída').first()
                        if move_type:
                            form.movement_type_id.data = move_type.id
                            # Configurar origem se fornecida, senão usar padrão
                            if source_substock_id:
                                try:
                                    form.source_substock_id.data = int(source_substock_id)
                                except ValueError:
                                    flash('Subestoque de origem inválido.', 'warning')
                                    default_substock = SubStock.query.filter_by(name='Padrão').first()
                                    if default_substock:
                                        form.source_substock_id.data = default_substock.id
                            else:
                                default_substock = SubStock.query.filter_by(name='Padrão').first()
                                if default_substock:
                                    form.source_substock_id.data = default_substock.id
                            form.destination_substock_id.data = 0
                    elif movement_type == 'entrada':
                        entry_type = MovementType.query.filter_by(name='Entrada').first()
                        if entry_type:
                            form.movement_type_id.data = entry_type.id
                            # Configurar destino se fornecido, senão usar padrão
                            if destination_substock_id:
                                try:
                                    form.destination_substock_id.data = int(destination_substock_id)
                                except ValueError:
                                    flash('Subestoque de destino inválido.', 'warning')
                                    default_substock = SubStock.query.filter_by(name='Padrão').first()
                                    if default_substock:
                                        form.destination_substock_id.data = default_substock.id
                            else:
                                default_substock = SubStock.query.filter_by(name='Padrão').first()
                                if default_substock:
                                    form.destination_substock_id.data = default_substock.id
                            form.source_substock_id.data = 0
                    elif movement_type == 'transferencia':
                        transfer_type = MovementType.query.filter_by(name='Transferência').first()
                        if transfer_type:
                            form.movement_type_id.data = transfer_type.id
                            # Configurar origem e destino
                            if source_substock_id:
                                try:
                                    form.source_substock_id.data = int(source_substock_id)
                                except ValueError:
                                    flash('Subestoque de origem inválido.', 'warning')
                            if destination_substock_id:
                                try:
                                    form.destination_substock_id.data = int(destination_substock_id)
                                except ValueError:
                                    flash('Subestoque de destino inválido.', 'warning')
                    else:
                        # Definir tipo de movimento padrão como Entrada (comportamento padrão)
                        entry_type = MovementType.query.filter_by(name='Entrada').first()
                        if entry_type:
                            form.movement_type_id.data = entry_type.id
                        # Definir subestoque padrão para destino
                        default_substock = SubStock.query.filter_by(name='Padrão').first()
                        if default_substock:
                            form.destination_substock_id.data = default_substock.id
                    
                    # Opcionalmente bloquear alteração do tipo se especificado
                    if movement_type:
                        form.movement_type_id.render_kw = {'readonly': True}
                else:
                    flash('Item não encontrado.', 'danger')
        except ValueError as e:
            flash(f'Erro ao processar parâmetros: {str(e)}', 'danger')

    if form.validate_on_submit():
        try:
            # Validar item selecionado
            if not form.item_id.data:
                flash('Selecione um item.', 'danger')
                return render_template('movements/movement_form.html', form=form)

            # Validar quantidade
            if form.quantity.data <= 0:
                flash('A quantidade deve ser maior que zero.', 'danger')
                return render_template('movements/movement_form.html', form=form)

            # Obter tipo de movimento
            movement_type = MovementType.query.get(form.movement_type_id.data)
            if not movement_type:
                flash('Tipo de movimento inválido.', 'danger')
                return render_template('movements/movement_form.html', form=form)

            # Validar origem/destino conforme tipo de movimento
            if 'entrada' in movement_type.name.lower():
                if form.destination_substock_id.data == 0:
                    flash('Movimentações de entrada devem ter destino.', 'danger')
                    return render_template('movements/movement_form.html', form=form)
                form.source_substock_id.data = 0

            elif 'saída' in movement_type.name.lower():
                if form.source_substock_id.data == 0:
                    flash('Movimentações de saída devem ter origem.', 'danger')
                    return render_template('movements/movement_form.html', form=form)
                form.destination_substock_id.data = 0

            elif 'transferência' in movement_type.name.lower():
                if form.source_substock_id.data == 0 or form.destination_substock_id.data == 0:
                    flash('Transferências requerem origem e destino.', 'danger')
                    return render_template('movements/movement_form.html', form=form)
                if form.source_substock_id.data == form.destination_substock_id.data:
                    flash('Origem e destino devem ser diferentes.', 'danger')
                    return render_template('movements/movement_form.html', form=form)

            # Criar movimento
            movement = Movement(
                item_id=form.item_id.data,
                quantity=form.quantity.data,
                movement_type_id=form.movement_type_id.data,
                notes=form.notes.data,
                reference_code=form.reference_code.data,
                created_by_id=current_user.id
            )

            # Definir origem/destino se aplicável
            if form.source_substock_id.data != 0:
                movement.source_substock_id = form.source_substock_id.data
            if form.destination_substock_id.data != 0:
                movement.destination_substock_id = form.destination_substock_id.data

            # Associar ao projeto se selecionado
            if form.project_id.data != 0:
                movement.project_id = form.project_id.data

            # Associar ao pedido de compra se selecionado
            if form.purchase_order_id.data != 0:
                movement.purchase_order_id = form.purchase_order_id.data
                po_item = PurchaseOrderItem.query.filter_by(
                    purchase_order_id=form.purchase_order_id.data,
                    item_id=form.item_id.data
                ).first()
                
                if po_item:
                    po_item.received_quantity += form.quantity.data
                    db.session.add(po_item)

            # Atualizar estoque
            if movement_type.affects_stock:
                if not update_inventory(movement):
                    return render_template('movements/movement_form.html', form=form)

            # Salvar movimento
            db.session.add(movement)
            db.session.commit()

            flash('Movimentação registrada com sucesso!', 'success')
            if form.purchase_order_id.data != 0:
                return redirect(url_for('purchase_orders'))
            return redirect(url_for('movements'))

        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao registrar movimentação: {str(e)}', 'danger')
            return render_template('movements/movement_form.html', form=form)

    return render_template('movements/movement_form.html', 
                         form=form,
                         title='Nova Movimentação')

def update_inventory(movement):
    """Atualiza o estoque baseado no movimento"""
    try:
        # Entrada: aumentar estoque no destino
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
# Esta solução:
# 1. Mantém a integridade do banco de dados (não permite preços nulos)
# 2. Define um preço temporário de 0.0 que pode ser atualizado depois
# 3. Avisa o usuário que os preços precisam ser atualizados
# 4. Não requer nenhuma alteração no esquema do banco de dados

# O erro ocorreu porque o sistema tentava criar registros de PurchaseOrderItem sem um preço unitário, violando a restrição NOT NULL do banco de dados. Com esta correção, o sistema continuará funcionando como antes, mas agora com preços temporários que podem ser ajustados posteriormente.
        # Saída: diminuir estoque na origem
        elif movement.source_substock_id and not movement.destination_substock_id:
            inv_item = InventoryItem.query.filter_by(
                item_id=movement.item_id,
                substock_id=movement.source_substock_id
            ).first()
            
            if not inv_item or inv_item.quantity < movement.quantity:
                flash('Quantidade insuficiente no estoque de origem.', 'danger')
                return False
                
            inv_item.quantity -= movement.quantity

        # Transferência: diminuir na origem e aumentar no destino
        elif movement.source_substock_id and movement.destination_substock_id:
            source_inv = InventoryItem.query.filter_by(
                item_id=movement.item_id,
                substock_id=movement.source_substock_id
            ).first()
            
            if not source_inv or source_inv.quantity < movement.quantity:
                flash('Quantidade insuficiente no estoque de origem.', 'danger')
                return False
                
            source_inv.quantity -= movement.quantity
            
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

        return True

    except Exception as e:
        flash(f'Erro ao atualizar estoque: {str(e)}', 'danger')
        return False

@app.route('/movements/<int:movement_id>')
@login_required
def movement_detail(movement_id):
    movement = Movement.query.get_or_404(movement_id)
    return render_template('movements/movement_detail.html',
                         title=f'Movimentação #{movement.id}',
                         movement=movement)
    
    
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
        # Usar o prefixo configurado nas settings
        po_prefix = get_setting('po_prefix', 'PO-')  # Pega o prefixo configurado, ou usa 'PO-' como padrão
        po_number = form.po_number.data if form.po_number.data else f'{po_prefix}{datetime.utcnow().strftime("%Y%m%d-%H%M%S")}'
        
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
    
    # Create a new PO using configured prefix
    po_prefix = get_setting('po_prefix', 'PO-')  # Pega o prefixo configurado, ou usa 'PO-' como padrão
    po_number = f'{po_prefix}AUTO-{datetime.utcnow().strftime("%Y%m%d-%H%M%S")}'
    
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
            quantity=item_data['to_order'],
            unit_price=0.0  # Preço temporário que pode ser ajustado depois
        )
        db.session.add(po_item)
    
    db.session.commit()
    
    flash(f'Pedido de compra {po_number} gerado com sucesso para {len(items_to_order)} itens. Por favor, atualize os preços unitários.', 'success')
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
