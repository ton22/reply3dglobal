from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from datetime import datetime

from app import app, db
from models import Setting, Item, SubStock, User, InventoryItem
from forms import SettingsForm, StockAlertForm
import email_service

# Adicionar ao main.py o import deste arquivo
# e.g. import settings

# Routes for settings and alerts

@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    form = SettingsForm()
    
    # Populate substock choices
    substocks = SubStock.query.all()
    form.default_substock_id.choices = [(0, 'Selecione um Sub-estoque')] + [(s.id, s.name) for s in substocks]
    
    # On form submission
    if form.validate_on_submit():
        # Update settings in database
        update_setting('company_name', form.company_name.data)
        update_setting('default_substock_id', str(form.default_substock_id.data))
        update_setting('po_prefix', form.po_prefix.data)
        update_setting('low_stock_alert', 'yes' if form.low_stock_alert.data else 'no')
        update_setting('theme', form.theme.data)
        update_setting('email_notifications', 'yes' if form.email_notifications.data else 'no')
        update_setting('email_address', form.email_address.data)
        
        flash('Configurações salvas com sucesso', 'success')
        return redirect(url_for('settings'))
    
    # Load current settings to populate form
    if request.method == 'GET':
        form.company_name.data = get_setting('company_name', '3D Global Store')
        form.default_substock_id.data = int(get_setting('default_substock_id', '0'))
        form.po_prefix.data = get_setting('po_prefix', 'PO-')
        form.low_stock_alert.data = get_setting('low_stock_alert', 'yes') == 'yes'
        form.theme.data = get_setting('theme', 'dark')
        form.email_notifications.data = get_setting('email_notifications', 'no') == 'yes'
        form.email_address.data = get_setting('email_address', '')
    
    # Prepare UI specific data
    context = {
        'title': 'Configurações',
        'form': form,
        'User': User,
        'Item': Item,
        'SubStock': SubStock
    }
    
    return render_template('settings.html', **context)

@app.route('/stock_alerts', methods=['GET', 'POST'])
@login_required
def stock_alerts():
    form = StockAlertForm()
    
    # Populate item choices
    items = Item.query.order_by(Item.name).all()
    form.item_id.choices = [(i.id, f"{i.name} - Estoque mín.: {i.minimum_stock} {i.unit.symbol}") for i in items]
    
    # On form submission
    if form.validate_on_submit():
        # Create or update stock alerts settings
        item_id = form.item_id.data
        
        # We'll store alerts as settings in a structured format
        # Format: "stock_alert_{item_id}"
        key = f"stock_alert_{item_id}"
        value = f"{form.alert_threshold.data},{form.email_alert.data},{form.dashboard_alert.data}"
        
        update_setting(key, value)
        
        flash('Configuração de alerta salva com sucesso', 'success')
        return redirect(url_for('stock_alerts'))
    
    # Get all existing alerts
    alerts = []
    for item in items:
        key = f"stock_alert_{item.id}"
        alert_setting = get_setting(key, None)
        
        if alert_setting:
            threshold, email_alert, dashboard_alert = alert_setting.split(',')
            alerts.append({
                'item': item,
                'threshold': float(threshold),
                'email_alert': email_alert == 'True',
                'dashboard_alert': dashboard_alert == 'True'
            })
    
    # Prepare UI specific data
    context = {
        'title': 'Alertas de Estoque',
        'form': form,
        'alerts': alerts
    }
    
    return render_template('stock_alerts.html', **context)

@app.route('/stock_alerts/delete/<int:item_id>', methods=['POST'])
@login_required
def delete_stock_alert(item_id):
    key = f"stock_alert_{item_id}"
    
    # Delete the setting
    setting = Setting.query.filter_by(key=key).first()
    if setting:
        db.session.delete(setting)
        db.session.commit()
        flash('Alerta de estoque removido com sucesso', 'success')
    
    return redirect(url_for('stock_alerts'))

# Helper functions

def get_setting(key, default=None):
    """Get setting value from database or return default if not found"""
    setting = Setting.query.filter_by(key=key).first()
    return setting.value if setting else default

def update_setting(key, value):
    """Create or update a setting in the database"""
    # Garantir que value não seja None
    if value is None:
        value = ''
        
    setting = Setting.query.filter_by(key=key).first()
    
    if setting:
        setting.value = value
        setting.updated_at = datetime.utcnow()
    else:
        setting = Setting(
            key=key,
            value=value,
            description=f"Setting for {key}"
        )
        db.session.add(setting)
    
    db.session.commit()