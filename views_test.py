from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from your_app import app, db
from your_models import (
    Movement, MovementType, PurchaseOrder, PurchaseOrderItem,
    SubStock, InventoryItem, Project, Item
)
from your_forms import MovementForm

@app.route('/movements/new', methods=['GET', 'POST'])
@login_required
def new_movement():
    form = MovementForm()

    # Carregar todas as opções
    purchase_orders = PurchaseOrder.query.all()
    form.purchase_order_id.choices = [(0, 'Nenhum')] + [(po.id, po.po_number) for po in purchase_orders]
    form.item_id.choices = [(0, 'Selecione um item')] + [(i.id, i.name) for i in Item.query.order_by(Item.name).all()]
    form.movement_type_id.choices = [(t.id, t.name) for t in MovementType.query.all()]
    form.source_substock_id.choices = [(0, '-')] + [(s.id, s.name) for s in SubStock.query.all()]
    form.destination_substock_id.choices = [(0, '-')] + [(s.id, s.name) for s in SubStock.query.all()]
    form.project_id.choices = [(0, 'Nenhum')] + [(p.id, p.name) for p in Project.query.filter_by(status='active').all()]

    # Limpar atributos readonly por padrão
    form.movement_type_id.render_kw = None
    form.item_id.render_kw = None
    form.purchase_order_id.render_kw = None
    form.destination_substock_id.render_kw = None

    # Definir item_id como None por padrão para movimentações normais
    form.item_id.data = None

    # Verificar se veio de um pedido de compra
    purchase_order_id = request.args.get('purchase_order_id')
    item_id = request.args.get('item_id')
    if purchase_order_id and item_id and request.method == 'GET':
        # Preencher o formulário com as informações do pedido de compra
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
        else:
            flash('Item ou pedido de compra inválido.', 'danger')

    if form.validate_on_submit():
        # Validar se item_id é válido
        if not form.item_id.data or form.item_id.data == '0':
            flash('Selecione um item válido.', 'danger')
            return render_template('movements/movement_form.html', form=form, title='Nova Movimentação')

        # Verificar se o movimento já existe
        existing_movement = Movement.query.filter(
            Movement.item_id == form.item_id.data,
            Movement.quantity == form.quantity.data,
            Movement.created_at >= datetime.utcnow() - timedelta(seconds=15)
        ).first()

        if existing_movement:
            flash('Esta movimentação já foi registrada.', 'warning')
            return redirect(url_for('movements'))

        try:
            # Validar quantidade
            if form.quantity.data <= 0:
                flash('A quantidade deve ser maior que zero.', 'danger')
                return render_template('movements/movement_form.html', form=form, title='Nova Movimentação')

            # Obter o tipo de movimento
            movement_type = MovementType.query.get(form.movement_type_id.data)

            # Validar subestoques com base no tipo de movimento
            if 'entrada' in movement_type.name.lower() and form.destination_substock_id.data == 0:
                flash('Movimentações de entrada devem ter destino.', 'danger')
                return render_template('movements/movement_form.html', form=form, title='Nova Movimentação')

            if 'saída' in movement_type.name.lower() and form.destination_substock_id.data != 0:
                flash('Movimentações de saída não devem ter destino.', 'danger')
                return render_template('movements/movement_form.html', form=form, title='Nova Movimentação')

            if 'transferência' in movement_type.name.lower():
                if form.source_substock_id.data == 0 or form.destination_substock_id.data == 0:
                    flash('Transferências requerem origem e destino.', 'danger')
                    return render_template('movements/movement_form.html', form=form, title='Nova Movimentação')
                if form.source_substock_id.data == form.destination_substock_id.data:
                    flash('Origem e destino devem ser diferentes.', 'danger')
                    return render_template('movements/movement_form.html', form=form, title='Nova Movimentação')

            # Criar o registro de movimentação
            movement = Movement(
                item_id=form.item_id.data,
                quantity=form.quantity.data,
                movement_type_id=form.movement_type_id.data,
                notes=form.notes.data,
                reference_code=form.reference_code.data,
                created_by_id=current_user.id
            )

            # Definir subestoques de origem e destino
            if form.source_substock_id.data != 0:
                movement.source_substock_id = form.source_substock_id.data

            if form.destination_substock_id.data != 0:
                movement.destination_substock_id = form.destination_substock_id.data

            # Associar projeto, se aplicável
            if form.project_id.data != 0:
                movement.project_id = form.project_id.data

            # Associar pedido de compra e atualizar received_quantity
            if form.purchase_order_id.data != 0:
                movement.purchase_order_id = form.purchase_order_id.data
                po_item = PurchaseOrderItem.query.filter_by(
                    purchase_order_id=form.purchase_order_id.data,
                    item_id=form.item_id.data
                ).first()
                if po_item:
                    po_item.received_quantity += form.quantity.data
                    db.session.add(po_item)
                    # Atualizar o status do pedido de compra
                    purchase_order = PurchaseOrder.query.get(form.purchase_order_id.data)
                    all_received = all(item.received_quantity >= item.quantity for item in purchase_order.items)
                    if all_received:
                        purchase_order.status = 'received'
                        purchase_order.received_at = datetime.utcnow()
                        db.session.add(purchase_order)

            # Atualizar o estoque com base no tipo de movimento
            if movement_type.affects_stock:
                # Entradas: aumentar estoque no destino
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

                # Saídas: diminuir estoque na origem
                elif movement.source_substock_id and not movement.destination_substock_id:
                    inv_item = InventoryItem.query.filter_by(
                        item_id=movement.item_id,
                        substock_id=movement.source_substock_id
                    ).first()
                    if inv_item:
                        if inv_item.quantity >= movement.quantity:
                            inv_item.quantity -= movement.quantity
                        else:
                            flash('Quantidade insuficiente no estoque de origem.', 'danger')
                            return render_template('movements/movement_form.html', form=form, title='Nova Movimentação')
                    else:
                        flash('Item não encontrado no estoque de origem.', 'danger')
                        return render_template('movements/movement_form.html', form=form, title='Nova Movimentação')

                # Transferências: diminuir na origem, aumentar no destino
                elif movement.source_substock_id and movement.destination_substock_id:
                    source_inv = InventoryItem.query.filter_by(
                        item_id=movement.item_id,
                        substock_id=movement.source_substock_id
                    ).first()
                    if not source_inv or source_inv.quantity < movement.quantity:
                        flash('Quantidade insuficiente no estoque de origem.', 'danger')
                        return render_template('movements/movement_form.html', form=form, title='Nova Movimentação')
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

            # Salvar a movimentação e todas as alterações
            db.session.add(movement)
            db.session.commit()

            # Exibir mensagem de sucesso e redirecionar
            flash('Movimentação criada com sucesso.', 'success')
            if form.purchase_order_id.data != 0:
                return redirect(url_for('purchase_orders'))  # Voltar para pedidos de compra
            return redirect(url_for('new_movement'))  # Nova movimentação limpa

        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao criar movimentação: {str(e)}', 'danger')
            return render_template('movements/movement_form.html', form=form, title='Nova Movimentação')

    return render_template('movements/movement_form.html', form=form, title='Nova Movimentação')