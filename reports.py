from flask import Blueprint, render_template, redirect, url_for, jsonify, request, make_response, send_file
from flask_login import login_required, current_user
from sqlalchemy import func
from datetime import datetime, timedelta
import json
import csv
import io

from app import app, db
from models import Item, SubStock, InventoryItem, Movement, Project, PurchaseOrder, MovementType, Setting

# Routes for reports and data visualization

@app.route('/reports')
@login_required
def reports():
    # Get items with low stock
    items = Item.query.filter(Item.minimum_stock > 0).all()
    low_stock_items = [item for item in items if item.is_below_alert_threshold()]
    
    return render_template('reports/reports.html', 
                          title='Relatórios',
                          Item=Item,
                          PurchaseOrder=PurchaseOrder,
                          MovementType=MovementType,
                          low_stock_items=low_stock_items)

@app.route('/reports/inventory')
@login_required
def inventory_report():
    # Get all inventory data
    substocks = SubStock.query.all()
    items = Item.query.order_by(Item.name).all()
    
    # Structure data for the report
    data = []
    for item in items:
        item_data = {
            'id': item.id,
            'name': item.name,
            'sku': item.sku,
            'type': item.item_type.name,
            'unit': item.unit.symbol,
            'minimum_stock': item.minimum_stock,
            'total_quantity': 0,
            'substocks': {}
        }
        
        # Get quantities by substock
        for substock in substocks:
            inv_item = InventoryItem.query.filter_by(
                item_id=item.id,
                substock_id=substock.id
            ).first()
            
            quantity = inv_item.quantity if inv_item else 0
            item_data['substocks'][substock.id] = quantity
            item_data['total_quantity'] += quantity
        
        # Add a flag for items below minimum stock
        item_data['below_minimum'] = item_data['total_quantity'] < item.minimum_stock
        
        data.append(item_data)
    
    context = {
        'title': 'Relatório de Estoque',
        'data': data,
        'substocks': substocks
    }
    
    return render_template('reports/inventory_report.html', **context)

@app.route('/reports/movements')
@login_required
def movements_report():
    # Get filter parameters
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')
    item_id = request.args.get('item_id')
    movement_type_id = request.args.get('movement_type_id')
    
    # Construct query
    query = Movement.query
    
    # Apply filters if provided
    if start_date_str:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
        query = query.filter(Movement.created_at >= start_date)
    
    if end_date_str:
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d') + timedelta(days=1)  # Include the end date
        query = query.filter(Movement.created_at < end_date)
    
    if item_id and item_id != 'all':
        query = query.filter(Movement.item_id == item_id)
    
    if movement_type_id and movement_type_id != 'all':
        query = query.filter(Movement.movement_type_id == movement_type_id)
    
    # Execute query
    movements = query.order_by(Movement.created_at.desc()).all()
    
    # Get filter options for the form
    items = Item.query.order_by(Item.name).all()
    movement_types = MovementType.query.order_by(MovementType.name).all()
    
    context = {
        'title': 'Relatório de Movimentações',
        'movements': movements,
        'items': items,
        'movement_types': movement_types,
        'start_date': start_date_str,
        'end_date': end_date_str,
        'selected_item': item_id,
        'selected_movement_type': movement_type_id
    }
    
    return render_template('reports/movements_report.html', **context)

@app.route('/reports/projects')
@login_required
def projects_report():
    # Get filter parameters
    status = request.args.get('status', 'all')
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')
    
    # Construct query
    query = Project.query
    
    # Apply filters
    if status != 'all':
        query = query.filter(Project.status == status)
    
    if start_date_str:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        query = query.filter(Project.start_date >= start_date)
    
    if end_date_str:
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        query = query.filter(Project.start_date <= end_date)
    
    # Execute query
    projects = query.order_by(Project.start_date.desc()).all()
    
    context = {
        'title': 'Relatório de Projetos',
        'projects': projects,
        'status': status,
        'start_date': start_date_str,
        'end_date': end_date_str,
        'statuses': [
            {'value': 'all', 'label': 'Todos'},
            {'value': 'active', 'label': 'Ativos'},
            {'value': 'completed', 'label': 'Concluídos'},
            {'value': 'cancelled', 'label': 'Cancelados'}
        ]
    }
    
    return render_template('reports/projects_report.html', **context)

@app.route('/reports/purchase_orders', methods=['GET'])
@login_required
def purchase_orders_report():
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    status = request.args.get('status', 'all')

    query = PurchaseOrder.query
    if start_date:
        query = query.filter(PurchaseOrder.created_at >= start_date)
    if end_date:
        query = query.filter(PurchaseOrder.created_at <= end_date)
    if status != 'all':
        query = query.filter_by(status=status)

    purchase_orders = query.all()

    # Calcular o valor total dos pedidos recebidos
    total_received_value = sum(
        po.get_total_value(received_only=True) for po in purchase_orders if po.status == 'received'
    )

    # Calcular o valor total dos pedidos pendentes
    total_pending_value = sum(
        po.get_total_value(received_only=False) for po in purchase_orders if po.status != 'received'
    )

    return render_template(
        'reports/purchase_orders_report.html',
        purchase_orders=purchase_orders,
        total_received_value=total_received_value,
        total_pending_value=total_pending_value,
        start_date=start_date,
        end_date=end_date,
        status=status,
        statuses=[
            {'value': 'all', 'label': 'Todos'},
            {'value': 'draft', 'label': 'Rascunho'},
            {'value': 'sent', 'label': 'Enviado'},
            {'value': 'received', 'label': 'Recebido'},
            {'value': 'cancelled', 'label': 'Cancelado'}
        ]
    )
    
    return render_template('reports/purchase_orders_report.html', **context)

@app.route('/reports/low_stock')
@login_required
def low_stock_report():
    # Get items below minimum stock
    low_stock_items = []
    items = Item.query.all()
    
    # Lists for chart data
    item_names = []
    current_stocks = []
    minimum_stocks = []
    stock_percentages = []
    
    # Colors for charts
    colors = [
        'rgba(255, 99, 132, 0.7)',
        'rgba(54, 162, 235, 0.7)',
        'rgba(255, 206, 86, 0.7)',
        'rgba(75, 192, 192, 0.7)',
        'rgba(153, 102, 255, 0.7)',
        'rgba(255, 159, 64, 0.7)',
        'rgba(140, 158, 255, 0.7)',
        'rgba(174, 213, 129, 0.7)',
        'rgba(255, 213, 79, 0.7)',
        'rgba(77, 208, 225, 0.7)'
    ]
    
    # Counters for statistics
    total_items = 0
    critical_items = 0
    total_shortage = 0
    
    for item in items:
        if item.minimum_stock and item.minimum_stock > 0 and item.is_below_alert_threshold():
            total_items += 1
            total_stock = float(item.get_total_stock())
            
            # Get alert threshold if configured
            key = f"stock_alert_{item.id}"
            alert_setting = Setting.query.filter_by(key=key).first()
            threshold_percentage = 100.0  # Default to 100% if no setting
            
            if alert_setting:
                threshold, _, _ = alert_setting.value.split(',')
                threshold_percentage = float(threshold)
            
            # Calculate stock percentage
            stock_percentage = (total_stock / item.minimum_stock * 100)
            if stock_percentage < 25:
                critical_items += 1
                
            shortage = item.minimum_stock - total_stock
            total_shortage += shortage
            
            # Prepare item data
            item_data = {
                'id': item.id,
                'name': str(item.name),
                'sku': str(item.sku) if item.sku else '',
                'type': str(item.item_type.name),
                'unit': str(item.unit.symbol),
                'minimum_stock': float(item.minimum_stock),
                'current_stock': float(total_stock),
                'shortage': float(shortage),
                'alert_threshold': float(threshold_percentage),
                'stock_percentage': round(float(stock_percentage), 2),
                'status': 'Crítico' if stock_percentage < 25 else 'Baixo'
            }
            
            low_stock_items.append(item_data)
            
            # Add data for charts
            item_names.append(str(item.name))
            current_stocks.append(float(total_stock))
            minimum_stocks.append(float(item.minimum_stock))
            stock_percentages.append(round(float(stock_percentage), 2))
    
    # Statistics for dashboard cards
    statistics = {
        'total_items': int(total_items),
        'critical_items': int(critical_items),
        'total_shortage': float(total_shortage),
        'critical_percentage': round(float((critical_items / total_items * 100) if total_items > 0 else 0), 2)
    }
    
    # Chart data structures
    bar_chart_data = {
        'labels': item_names,
        'datasets': [
            {
                'label': 'Estoque Atual',
                'data': current_stocks,
                'backgroundColor': 'rgba(54, 162, 235, 0.7)',
                'borderColor': 'rgba(54, 162, 235, 1)',
                'borderWidth': 1
            },
            {
                'label': 'Estoque Mínimo',
                'data': minimum_stocks,
                'backgroundColor': 'rgba(255, 99, 132, 0.7)',
                'borderColor': 'rgba(255, 99, 132, 1)',
                'borderWidth': 1
            }
        ]
    }
    
    percentage_chart_data = {
        'labels': item_names,
        'datasets': [{
            'label': 'Porcentagem do Estoque Mínimo',
            'data': stock_percentages,
            'backgroundColor': colors[:len(item_names)],
            'borderColor': [color.replace('0.7', '1') for color in colors[:len(item_names)]],
            'borderWidth': 1
        }]
    }
    
    # Create context with all necessary data
    context = {
        'title': 'Relatório de Estoque Baixo',
        'low_stock_items': low_stock_items,
        'statistics': statistics,
        'colors': colors[:len(low_stock_items)],
        # Chart data
        'item_names': item_names,
        'current_stocks': current_stocks,
        'minimum_stocks': minimum_stocks,
        'stock_percentages': stock_percentages,
        # Pre-formatted chart data
        'bar_chart_data': bar_chart_data,
        'percentage_chart_data': percentage_chart_data
    }
    
    return render_template('reports/low_stock_report.html', **context)

# API routes for chart data

@app.route('/api/chart/inventory_value')
@login_required
def chart_inventory_value():
    # Get data for inventory value by substock
    substocks = SubStock.query.all()
    
    labels = [s.name for s in substocks]
    data = []
    
    for substock in substocks:
        count = InventoryItem.query.filter_by(substock_id=substock.id).count()
        data.append(count)
    
    return jsonify({
        'labels': labels,
        'datasets': [{
            'label': 'Número de Itens por Sub-estoque',
            'data': data,
            'backgroundColor': [
                '#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF',
                '#FF9F40', '#8C9EFF', '#AED581', '#FFD54F', '#4DD0E1'
            ]
        }]
    })

@app.route('/api/chart/movements_by_type')
@login_required
def chart_movements_by_type():
    # Get movement counts by type
    movement_counts = db.session.query(
        MovementType.name, 
        func.count(Movement.id)
    ).join(
        Movement
    ).group_by(
        MovementType.name
    ).all()
    
    labels = [m[0] for m in movement_counts]
    data = [m[1] for m in movement_counts]
    
    return jsonify({
        'labels': labels,
        'datasets': [{
            'label': 'Movimentações por Tipo',
            'data': data,
            'backgroundColor': [
                '#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF',
                '#FF9F40', '#8C9EFF', '#AED581', '#FFD54F', '#4DD0E1'
            ]
        }]
    })

@app.route('/api/chart/projects_by_status')
@login_required
def chart_projects_by_status():
    # Get project counts by status
    active_count = Project.query.filter_by(status='active').count()
    completed_count = Project.query.filter_by(status='completed').count()
    cancelled_count = Project.query.filter_by(status='cancelled').count()
    
    return jsonify({
        'labels': ['Ativos', 'Concluídos', 'Cancelados'],
        'datasets': [{
            'label': 'Projetos por Status',
            'data': [active_count, completed_count, cancelled_count],
            'backgroundColor': ['#36A2EB', '#4BC0C0', '#FF6384']
        }]
    })

# Export routes

@app.route('/reports/export/inventory/csv')
@login_required
def export_inventory_csv():
    # Generate CSV file for inventory report
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    substocks = SubStock.query.all()
    header = ['ID', 'Nome', 'SKU', 'Tipo', 'Unidade', 'Estoque Mínimo']
    for substock in substocks:
        header.append(f'Estoque em {substock.name}')
    header.append('Estoque Total')
    
    writer.writerow(header)
    
    # Write data rows
    items = Item.query.order_by(Item.name).all()
    for item in items:
        row = [
            item.id,
            item.name,
            item.sku or '',
            item.item_type.name,
            item.unit.symbol,
            item.minimum_stock
        ]
        
        total_quantity = 0
        for substock in substocks:
            inv_item = InventoryItem.query.filter_by(
                item_id=item.id,
                substock_id=substock.id
            ).first()
            
            quantity = inv_item.quantity if inv_item else 0
            row.append(quantity)
            total_quantity += quantity
        
        row.append(total_quantity)
        writer.writerow(row)
    
    # Create response
    output.seek(0)
    response = make_response(output.getvalue())
    response.headers['Content-Disposition'] = 'attachment; filename=inventory_report.csv'
    response.headers['Content-type'] = 'text/csv'
    
    return response

@app.route('/reports/export/movements/csv')
@login_required
def export_movements_csv():
    # Get filter parameters
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')
    item_id = request.args.get('item_id')
    movement_type_id = request.args.get('movement_type_id')
    
    # Construct query
    query = Movement.query
    
    # Apply filters if provided
    if start_date_str:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
        query = query.filter(Movement.created_at >= start_date)
    
    if end_date_str:
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d') + timedelta(days=1)
        query = query.filter(Movement.created_at < end_date)
    
    if item_id and item_id != 'all':
        query = query.filter(Movement.item_id == item_id)
    
    if movement_type_id and movement_type_id != 'all':
        query = query.filter(Movement.movement_type_id == movement_type_id)
    
    # Execute query
    movements = query.order_by(Movement.created_at.desc()).all()
    
    # Generate CSV
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow([
        'ID', 'Data', 'Item', 'Tipo', 'Quantidade', 'Origem', 'Destino', 
        'Projeto', 'Pedido de Compra', 'Referência', 'Notas'
    ])
    
    # Write data rows
    for movement in movements:
        source = movement.source_substock.name if movement.source_substock else ''
        destination = movement.destination_substock.name if movement.destination_substock else ''
        project = movement.project.name if movement.project else ''
        purchase_order = movement.purchase_order.po_number if movement.purchase_order else ''
        
        writer.writerow([
            movement.id,
            movement.created_at.strftime('%Y-%m-%d %H:%M'),
            movement.item.name,
            movement.movement_type.name,
            f"{movement.quantity} {movement.item.unit.symbol}",
            source,
            destination,
            project,
            purchase_order,
            movement.reference_code or '',
            movement.notes or ''
        ])
    
    # Create response
    output.seek(0)
    response = make_response(output.getvalue())
    response.headers['Content-Disposition'] = 'attachment; filename=movements_report.csv'
    response.headers['Content-type'] = 'text/csv'
    
    return response

@app.route('/reports/export/low_stock/csv')
@login_required
def export_low_stock_csv():
    # Get items below minimum stock
    low_stock_items = []
    items = Item.query.all()
    
    for item in items:
        total_stock = item.get_total_stock()  # Use get_total_stock method
        if item.is_below_alert_threshold():  # Use is_below_alert_threshold
            # Get alert threshold if configured
            key = f"stock_alert_{item.id}"
            alert_setting = Setting.query.filter_by(key=key).first()
            threshold_percentage = 100  # Default to 100% if no setting
            
            if alert_setting:
                threshold, _, _ = alert_setting.value.split(',')
                threshold_percentage = float(threshold)
            
            low_stock_items.append({
                'id': item.id,
                'name': item.name,
                'sku': item.sku or '',
                'type': item.item_type.name,
                'unit': item.unit.symbol,
                'minimum_stock': item.minimum_stock,
                'current_stock': total_stock,
                'shortage': item.minimum_stock - total_stock,
                'alert_threshold': threshold_percentage
            })
    
    # Generate CSV
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow([
        'ID', 'Nome', 'SKU', 'Tipo', 'Unidade', 
        'Estoque Mínimo', 'Estoque Atual', 'Falta', 'Alerta em'
    ])
    
    # Write data rows
    for item in low_stock_items:
        writer.writerow([
            item['id'],
            item['name'],
            item['sku'],
            item['type'],
            item['unit'],
            item['minimum_stock'],
            item['current_stock'],
            item['shortage'],
            f"{item['alert_threshold']}%"
        ])
    
    # Create response
    output.seek(0)
    response = make_response(output.getvalue())
    response.headers['Content-Disposition'] = 'attachment; filename=low_stock_report.csv'
    response.headers['Content-type'] = 'text/csv'
    
    return response

@app.route('/reports/export/low_stock/pdf')
@login_required
def export_low_stock_pdf():
    # Get items below minimum stock
    low_stock_items = []
    items = Item.query.all()
    
    # Counters for statistics
    total_items = 0
    critical_items = 0
    total_shortage = 0
    
    for item in items:
        if item.minimum_stock and item.minimum_stock > 0 and item.is_below_alert_threshold():
            total_items += 1
            total_stock = float(item.get_total_stock())
            
            # Get alert threshold if configured
            key = f"stock_alert_{item.id}"
            alert_setting = Setting.query.filter_by(key=key).first()
            threshold_percentage = 100.0  # Default to 100% if no setting
            
            if alert_setting:
                threshold, _, _ = alert_setting.value.split(',')
                threshold_percentage = float(threshold)
            
            # Calculate stock percentage
            stock_percentage = (total_stock / item.minimum_stock * 100)
            if stock_percentage < 25:
                critical_items += 1
                
            shortage = item.minimum_stock - total_stock
            total_shortage += shortage
            
            # Prepare item data
            item_data = {
                'id': item.id,
                'name': str(item.name),
                'sku': str(item.sku) if item.sku else '',
                'type': str(item.item_type.name),
                'unit': str(item.unit.symbol),
                'minimum_stock': float(item.minimum_stock),
                'current_stock': float(total_stock),
                'shortage': float(shortage),
                'alert_threshold': float(threshold_percentage),
                'stock_percentage': round(float(stock_percentage), 2),
                'status': 'Crítico' if stock_percentage < 25 else 'Baixo'
            }
            
            low_stock_items.append(item_data)
    
    # Statistics for dashboard cards
    statistics = {
        'total_items': int(total_items),
        'critical_items': int(critical_items),
        'total_shortage': float(total_shortage),
        'critical_percentage': round(float((critical_items / total_items * 100) if total_items > 0 else 0), 2)
    }
    
    # Render template with print-specific layout
    return render_template(
        'reports/low_stock_print.html',
        low_stock_items=low_stock_items,
        statistics=statistics,
        generated_at=datetime.now().strftime('%d/%m/%Y %H:%M'),
        print_mode=True
    )
