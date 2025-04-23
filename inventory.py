from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, current_app
from flask_login import login_required, current_user
from sqlalchemy import func
from utils import generate_sku, generate_barcode

from app import app, db
from models import Item, ItemType, MeasurementUnit, SubStock, InventoryItem, Movement, MovementType, Brand, Log
from forms import ItemForm, ItemTypeForm, MeasurementUnitForm, SubStockForm, InventorySearchForm, BrandForm

# Routes for inventory management

@app.route('/dashboard')
@login_required
def dashboard():
    # Get low stock items
    low_stock_items = []
    items = Item.query.all()
    for item in items:
        total_stock = sum(inv_item.quantity for inv_item in item.inventory_items)
        if item.is_below_alert_threshold():
            low_stock_items.append({
                'id': item.id,
                'name': item.name,
                'current_stock': total_stock,
                'minimum_stock': item.minimum_stock,
                'unit': item.unit.symbol
            })
    
    # Recent movements
    recent_movements = Movement.query.order_by(Movement.created_at.desc()).limit(10).all()
    
    # Inventory statistics
    total_items = Item.query.count()
    total_substocks = SubStock.query.count()
    
    # Top items with most stock value
    top_items = db.session.query(
        Item, func.sum(InventoryItem.quantity).label('total_quantity')
    ).join(InventoryItem).group_by(Item.id).order_by(func.sum(InventoryItem.quantity).desc()).limit(5).all()
    
    # Data for stock distribution chart
    substocks = SubStock.query.all()
    chart_data = {
        'labels': [s.name for s in substocks],
        'datasets': [{
            'data': [
                db.session.query(func.sum(InventoryItem.quantity)).filter(
                    InventoryItem.substock_id == s.id
                ).scalar() or 0 for s in substocks
            ],
            'backgroundColor': [
                '#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF',
                '#FF9F40', '#8C9EFF', '#AED581', '#FFD54F', '#4DD0E1'
            ]
        }]
    }
    
    context = {
        'title': 'Dashboard',
        'low_stock_items': low_stock_items,
        'recent_movements': recent_movements,
        'total_items': total_items,
        'total_substocks': total_substocks,
        'top_items': top_items,
        'chart_data': chart_data
    }
    
    return render_template('dashboard.html', **context)

@app.route('/inventory/items')
@login_required
def items():
    # Get all item types for the filter dropdown
    item_types = ItemType.query.all()
    
    # Initialize form with request parameters
    form = InventorySearchForm(request.args)
    
    # Base query
    query = Item.query
    
    # Apply filters if provided
    if request.args.get('search') or request.args.get('item_type'):
        if request.args.get('search'):
            search_term = f"%{request.args.get('search')}%"
            query = query.filter((Item.name.ilike(search_term)) | (Item.sku.ilike(search_term)))
        
        if request.args.get('item_type') and request.args.get('item_type') != '0':
            query = query.filter(Item.item_type_id == int(request.args.get('item_type')))
    
    # Get sorted items
    sort_by = request.args.get('sort_by', 'name')
    sort_order = request.args.get('sort_order', 'asc')
    
    if sort_order == 'desc':
        sort_column = getattr(Item, sort_by).desc()
    else:
        sort_column = getattr(Item, sort_by).asc()
    
    items = query.order_by(sort_column).all()
    
    context = {
        'title': 'Itens de Estoque',
        'items': items,
        'form': form,
        'item_types': item_types,
        'sort_by': sort_by,
        'sort_order': sort_order
    }
    
    return render_template('inventory/items.html', **context)

@app.route('/inventory/items/new', methods=['GET', 'POST'])
@login_required
def new_item():
    form = ItemForm()
    form.item_type_id.choices = [(t.id, t.name) for t in ItemType.query.all()]
    form.unit_id.choices = [(u.id, u.name) for u in MeasurementUnit.query.all()]
    form.brand_id.choices = [(b.id, b.name) for b in Brand.query.order_by(Brand.name).all()]
    form.brand_id.choices.insert(0, (-1, 'Sem marca'))
    
    if form.validate_on_submit():
        # Gerar SKU e barcode se estiverem vazios
        sku = form.sku.data if form.sku.data else generate_sku(form.name.data, form.item_type_id.data)
        barcode = form.barcode.data if form.barcode.data else generate_barcode()
        
        # Os outros campos podem ser NULL se vazios
        description = form.description.data if form.description.data else None
        color = form.color.data if form.color.data else None
        
        # Verificar unicidade do SKU gerado
        existing_sku = Item.query.filter_by(sku=sku).first()
        if existing_sku:
            # Tentar gerar outro SKU
            for _ in range(5):  # Tentar no máximo 5 vezes
                new_sku = generate_sku(form.name.data, form.item_type_id.data)
                if not Item.query.filter_by(sku=new_sku).first():
                    sku = new_sku
                    break
        
        item = Item(
            name=form.name.data,
            description=description,
            sku=sku,
            barcode=barcode,
            color=color,
            minimum_stock=form.minimum_stock.data,
            item_type_id=form.item_type_id.data,
            unit_id=form.unit_id.data,
            brand_id=form.brand_id.data if form.brand_id.data != -1 else None
        )
        
        db.session.add(item)
        
        try:
            db.session.commit()
            flash(f'Item adicionado com sucesso! SKU: {sku}, Código de barras: {barcode}', 'success')
            return redirect(url_for('item_detail', item_id=item.id))
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao adicionar item: {str(e)}', 'danger')
    
    return render_template('inventory/item_form.html', form=form, title='Novo Item')

@app.route('/inventory/items/<int:item_id>')
@login_required
def item_detail(item_id):
    item = Item.query.get_or_404(item_id)
    
    # Get stock by substock
    substocks = SubStock.query.all()
    stock_by_substock = []
    
    for substock in substocks:
        inventory_item = InventoryItem.query.filter_by(item_id=item.id, substock_id=substock.id).first()
        quantity = inventory_item.quantity if inventory_item else 0
        
        stock_by_substock.append({
            'substock': substock,
            'quantity': quantity
        })
    
    # Get recent movements
    recent_movements = Movement.query.filter_by(item_id=item.id).order_by(Movement.created_at.desc()).limit(10).all()
    
    # Calculate totals
    total_stock = sum(s['quantity'] for s in stock_by_substock)
    
    context = {
        'title': f'Detalhes do Item: {item.name}',
        'item': item,
        'stock_by_substock': stock_by_substock,
        'total_stock': total_stock,
        'recent_movements': recent_movements
    }
    
    return render_template('inventory/item_detail.html', **context)

@app.route('/inventory/items/<int:item_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_item(item_id):
    item = Item.query.get_or_404(item_id)
    form = ItemForm(obj=item)
    
    # Populate dropdown options
    form.item_type_id.choices = [(t.id, t.name) for t in ItemType.query.all()]
    form.unit_id.choices = [(u.id, f"{u.name} ({u.symbol})") for u in MeasurementUnit.query.all()]
    form.brand_id.choices = [(b.id, b.name) for b in Brand.query.order_by(Brand.name).all()]
    form.brand_id.choices.insert(0, (-1, 'Sem marca'))
    
    if form.validate_on_submit():
        item.name = form.name.data
        item.description = form.description.data
        item.sku = form.sku.data
        item.barcode = form.barcode.data
        item.color = form.color.data
        item.minimum_stock = form.minimum_stock.data
        item.item_type_id = form.item_type_id.data
        item.unit_id = form.unit_id.data
        item.brand_id = form.brand_id.data if form.brand_id.data != -1 else None
        
        db.session.commit()
        
        flash('Item atualizado com sucesso', 'success')
        return redirect(url_for('item_detail', item_id=item.id))
    
    return render_template('inventory/item_form.html', form=form, title='Editar Item', item=item)

@app.route('/inventory/substocks')
@login_required
def substocks():
    substocks = SubStock.query.all()
    
    # For each substock, count items and get total inventory
    substock_data = []
    for substock in substocks:
        item_count = InventoryItem.query.filter_by(substock_id=substock.id).count()
        total_items = InventoryItem.query.filter_by(substock_id=substock.id).count()
        
        substock_data.append({
            'substock': substock,
            'item_count': item_count,
            'total_items': total_items
        })
    
    context = {
        'title': 'Sub-Estoques',
        'substock_data': substock_data
    }
    
    return render_template('inventory/substocks.html', **context)

@app.route('/inventory/substocks/new', methods=['GET', 'POST'])
@login_required
def new_substock():
    form = SubStockForm()
    
    if form.validate_on_submit():
        substock = SubStock(
            name=form.name.data,
            description=form.description.data,
            location=form.location.data
        )
        
        db.session.add(substock)
        db.session.commit()
        
        flash('Sub-estoque criado com sucesso', 'success')
        return redirect(url_for('substocks'))
    
    return render_template('inventory/substock_form.html', form=form, title='Novo Sub-Estoque')

@app.route('/inventory/substocks/<int:substock_id>')
@login_required
def substock_detail(substock_id):
    substock = SubStock.query.get_or_404(substock_id)
    
    # Get all inventory items in this substock
    inventory_items = InventoryItem.query.filter_by(substock_id=substock.id).all()
    
    # Recent movements
    incoming = Movement.query.filter_by(destination_substock_id=substock.id).order_by(Movement.created_at.desc()).limit(5).all()
    outgoing = Movement.query.filter_by(source_substock_id=substock.id).order_by(Movement.created_at.desc()).limit(5).all()
    
    context = {
        'title': f'Detalhes do Sub-Estoque: {substock.name}',
        'substock': substock,
        'inventory_items': inventory_items,
        'incoming': incoming,
        'outgoing': outgoing
    }
    
    return render_template('inventory/substock_detail.html', **context)

@app.route('/inventory/substocks/<int:substock_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_substock(substock_id):
    substock = SubStock.query.get_or_404(substock_id)
    form = SubStockForm(obj=substock)
    
    if form.validate_on_submit():
        substock.name = form.name.data
        substock.description = form.description.data
        substock.location = form.location.data
        
        db.session.commit()
        
        flash('Sub-estoque atualizado com sucesso', 'success')
        return redirect(url_for('substock_detail', substock_id=substock.id))
    
    return render_template('inventory/substock_form.html', form=form, title='Editar Sub-Estoque', substock=substock)

@app.route('/inventory/item_types')
@login_required
def item_types():
    types = ItemType.query.all()
    return render_template('inventory/item_types.html', types=types, title='Tipos de Item')

@app.route('/inventory/item_types/new', methods=['GET', 'POST'])
@login_required
def new_item_type():
    form = ItemTypeForm()
    
    if form.validate_on_submit():
        item_type = ItemType(
            name=form.name.data,
            description=form.description.data
        )
        
        db.session.add(item_type)
        db.session.commit()
        
        flash('Tipo de item criado com sucesso', 'success')
        return redirect(url_for('item_types'))
    
    return render_template('inventory/item_type_form.html', form=form, title='Novo Tipo de Item')

@app.route('/inventory/units')
@login_required
def units():
    units = MeasurementUnit.query.all()
    return render_template('inventory/units.html', units=units, title='Unidades de Medida')

@app.route('/inventory/units/new', methods=['GET', 'POST'])
@login_required
def new_unit():
    form = MeasurementUnitForm()
    
    if form.validate_on_submit():
        unit = MeasurementUnit(
            name=form.name.data,
            symbol=form.symbol.data,
            description=form.description.data
        )
        
        db.session.add(unit)
        db.session.commit()
        
        flash('Unidade de medida criada com sucesso', 'success')
        return redirect(url_for('units'))
    
    return render_template('inventory/unit_form.html', form=form, title='Nova Unidade de Medida')

@app.route('/brands')
@login_required
def brands():
    brands = Brand.query.all()
    return render_template('brands.html', brands=brands)

@app.route('/brand/new', methods=['GET', 'POST'])
@login_required
def new_brand():
    form = BrandForm()
    if form.validate_on_submit():
        brand = Brand(
            name=form.name.data,
            description=form.description.data
        )
        db.session.add(brand)
        db.session.commit()
        current_app.logger.info(f"Nova marca criada: {brand.name}")
        flash('Marca criada com sucesso', 'success')
        return redirect(url_for('brands'))
    return render_template('inventory/brand_form.html', form=form)

@app.route('/brand/<int:brand_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_brand(brand_id):
    brand = Brand.query.get_or_404(brand_id)
    form = BrandForm(obj=brand)
    
    if form.validate_on_submit():
        old_name = brand.name
        brand.name = form.name.data
        brand.description = form.description.data
        db.session.commit()
        current_app.logger.info(f"Marca atualizada: {old_name} -> {brand.name}")
        flash('Marca atualizada com sucesso', 'success')
        return redirect(url_for('brands'))
    
    return render_template('inventory/brand_form.html', form=form)

@app.route('/brand/<int:brand_id>/delete', methods=['POST'])
@login_required
def delete_brand(brand_id):
    brand = Brand.query.get_or_404(brand_id)
    
    # Verificar se a marca está sendo usada por algum item
    if brand.items:
        flash('Não é possível excluir esta marca porque ela está sendo usada por itens do estoque.', 'danger')
        current_app.logger.warning(f"Tentativa de excluir marca em uso: {brand.name}")
        return redirect(url_for('brands'))
    
    try:
        db.session.delete(brand)
        db.session.commit()
        current_app.logger.info(f"Marca excluída: {brand.name}")
        flash('Marca excluída com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Erro ao excluir marca: {str(e)}")
        flash(f'Erro ao excluir marca: {str(e)}', 'danger')
    
    return redirect(url_for('brands'))

@app.route('/logs')
@app.route('/inventory/logs')
@login_required
def logs():
    logs = Log.query.order_by(Log.created_at.desc()).all()
    return render_template('inventory/logs.html', logs=logs)

from flask import Blueprint

inventory_bp = Blueprint('inventory', __name__)

@inventory_bp.route('/')
def index():
    return "Inventory Home Page"  # Your actual view code
