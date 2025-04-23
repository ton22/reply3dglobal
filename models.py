from datetime import datetime
from app import db
from flask_login import UserMixin
from sqlalchemy import Table, Column, Integer, ForeignKey
from sqlalchemy.orm import relationship, backref

# Project-Item association table for many-to-many relationship
project_items = db.Table('project_items',
    db.Column('project_id', db.Integer, db.ForeignKey('project.id'), primary_key=True),
    db.Column('item_id', db.Integer, db.ForeignKey('item.id'), primary_key=True),
    db.Column('quantity', db.Float, default=0),
    db.Column('created_at', db.DateTime, default=datetime.utcnow)
)

class User(UserMixin, db.Model):
    """User model for authentication"""
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), default='user')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)

    def __repr__(self):
        return f'<User {self.username}>'

class ItemType(db.Model):
    """Type of inventory items (filament, part, tool, etc.)"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    items = relationship("Item", back_populates="item_type")

    def __repr__(self):
        return f'<ItemType {self.name}>'

class MeasurementUnit(db.Model):
    """Measurement units for items (kg, units, pieces, etc.)"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    symbol = db.Column(db.String(10), unique=True, nullable=False)
    description = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    items = relationship("Item", back_populates="unit")

    def __repr__(self):
        return f'<MeasurementUnit {self.symbol}>'

class SubStock(db.Model):
    """Represents different physical locations or departments for inventory"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(255))
    location = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    inventory_items = relationship("InventoryItem", back_populates="substock")
    outgoing_movements = relationship("Movement", foreign_keys="Movement.source_substock_id", back_populates="source_substock")
    incoming_movements = relationship("Movement", foreign_keys="Movement.destination_substock_id", back_populates="destination_substock")
    
    def __repr__(self):
        return f'<SubStock {self.name}>'

class Brand(db.Model):
    """Brands for items"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    items = relationship("Item", back_populates="brand")
    
    def __repr__(self):
        return f'<Brand {self.name}>'

class Item(db.Model):
    """Master item record"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    sku = db.Column(db.String(50), unique=True, nullable=True)
    barcode = db.Column(db.String(50), unique=True, nullable=True)
    color = db.Column(db.String(50))
    minimum_stock = db.Column(db.Float, default=0)
    
    # Foreign keys
    item_type_id = db.Column(db.Integer, db.ForeignKey('item_type.id'), nullable=False)
    unit_id = db.Column(db.Integer, db.ForeignKey('measurement_unit.id'), nullable=False)
    brand_id = db.Column(db.Integer, db.ForeignKey('brand.id'), nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    item_type = relationship("ItemType", back_populates="items")
    unit = relationship("MeasurementUnit", back_populates="items")
    brand = relationship("Brand", back_populates="items")
    inventory_items = relationship("InventoryItem", back_populates="item")
    movements = relationship("Movement", back_populates="item")
    projects = relationship("Project", secondary=project_items, back_populates="items")
    purchase_orders = relationship("PurchaseOrderItem", back_populates="item")
    
    def __repr__(self):
        return f'<Item {self.name}>'
    
    def get_total_stock(self):
        """Calculate total stock across all substocks"""
        return sum(inv_item.quantity for inv_item in self.inventory_items)
    
    def is_below_minimum(self):
        """Check if total stock is below minimum"""
        return self.get_total_stock() < self.minimum_stock
        
    def is_below_alert_threshold(self):
        """Check if total stock is below alert threshold percentage"""
        # Get alert threshold from settings
        key = f"stock_alert_{self.id}"
        alert_setting = db.session.query(Setting).filter_by(key=key).first()
        
        total_stock = self.get_total_stock()
        print(f"[DEBUG] Checking item {self.name} (ID: {self.id})")
        print(f"[DEBUG] Total stock: {total_stock}")
        print(f"[DEBUG] Minimum stock: {self.minimum_stock}")
        
        if alert_setting:
            threshold, _, _ = alert_setting.value.split(',')
            threshold_percentage = float(threshold)
            
            # Calculate threshold quantity based on minimum stock
            threshold_quantity = (threshold_percentage / 100.0) * self.minimum_stock
            
            print(f"[DEBUG] Alert threshold: {threshold_percentage}%")
            print(f"[DEBUG] Threshold quantity: {threshold_quantity}")
            
            # Check if current stock is below threshold
            is_below = total_stock < threshold_quantity
            print(f"[DEBUG] Is below threshold? {is_below}")
            return is_below
            
        # If no alert setting, use default minimum stock check
        is_below = self.is_below_minimum()
        print(f"[DEBUG] No alert setting, using minimum stock check. Is below? {is_below}")
        return is_below

class InventoryItem(db.Model):
    """Represents the quantity of an item in a specific substock"""
    id = db.Column(db.Integer, primary_key=True)
    quantity = db.Column(db.Float, default=0)
    
    # Foreign keys
    item_id = db.Column(db.Integer, db.ForeignKey('item.id'), nullable=False)
    substock_id = db.Column(db.Integer, db.ForeignKey('sub_stock.id'), nullable=False)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    item = relationship("Item", back_populates="inventory_items")
    substock = relationship("SubStock", back_populates="inventory_items")
    
    # Composite unique constraint
    __table_args__ = (db.UniqueConstraint('item_id', 'substock_id', name='_item_substock_uc'),)
    
    def __repr__(self):
        return f'<InventoryItem {self.item.name} in {self.substock.name}: {self.quantity}>'

class MovementType(db.Model):
    """Types of inventory movements (entry, exit, transfer, recycling, loss, etc.)"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.String(255))
    affects_stock = db.Column(db.Boolean, default=True)  
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    movements = relationship("Movement", back_populates="movement_type")
    
    def __repr__(self):
        return f'<MovementType {self.name}>'

class Movement(db.Model):
    """Record of item movements between substocks or in/out of the system"""
    id = db.Column(db.Integer, primary_key=True)
    quantity = db.Column(db.Float, nullable=False)
    notes = db.Column(db.Text)
    reference_code = db.Column(db.String(50))  
    
    # Foreign keys
    item_id = db.Column(db.Integer, db.ForeignKey('item.id'), nullable=False)
    movement_type_id = db.Column(db.Integer, db.ForeignKey('movement_type.id'), nullable=False)
    # source_substock_id = db.Column(db.Integer, db.ForeignKey('sub_stock.id'), nullable=False)
    # destination_substock_id = db.Column(db.Integer, db.ForeignKey('sub_stock.id'), nullable=False)

    source_substock_id = db.Column(db.Integer, db.ForeignKey('sub_stock.id'))
    destination_substock_id = db.Column(db.Integer, db.ForeignKey('sub_stock.id'))
    created_by_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'))
    purchase_order_id = db.Column(db.Integer, db.ForeignKey('purchase_order.id'))
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    item = relationship("Item", back_populates="movements")
    movement_type = relationship("MovementType", back_populates="movements")
    source_substock = relationship("SubStock", foreign_keys=[source_substock_id], back_populates="outgoing_movements")
    destination_substock = relationship("SubStock", foreign_keys=[destination_substock_id], back_populates="incoming_movements")
    created_by = relationship("User")
    project = relationship("Project", back_populates="movements")
    purchase_order = relationship("PurchaseOrder", back_populates="movements")
    
    def __repr__(self):
        return f'<Movement {self.id}: {self.quantity} of {self.item.name}>'

class Project(db.Model):
    """Projects that consume inventory items"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    status = db.Column(db.String(20), default='active')  
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)
    client_name = db.Column(db.String(100))
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    items = relationship("Item", secondary=project_items, back_populates="projects")
    movements = relationship("Movement", back_populates="project")
    
    def __repr__(self):
        return f'<Project {self.name}>'

class PurchaseOrder(db.Model):
    """Pedidos de compra para itens abaixo do estoque mínimo"""
    id = db.Column(db.Integer, primary_key=True)
    po_number = db.Column(db.String(50), unique=True)  # Número do pedido
    supplier = db.Column(db.String(100))  # Fornecedor
    status = db.Column(db.String(20), default='draft')  # Status do pedido
    notes = db.Column(db.Text)  # Observações

    # Chave estrangeira
    created_by_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    sent_at = db.Column(db.DateTime)
    received_at = db.Column(db.DateTime)

    # Relacionamentos
    created_by = relationship("User")
    items = relationship("PurchaseOrderItem", back_populates="purchase_order")
    movements = relationship("Movement", back_populates="purchase_order")

    def get_total_value(self, received_only=False):
        """
        Calcula o valor total do pedido de compra.
        Se `received_only=True`, considera apenas os itens recebidos.
        """
        if received_only:
            return sum(
                item.received_quantity * item.unit_price
                for item in self.items
                if item.received_quantity > 0
            )
        return sum(item.quantity * item.unit_price for item in self.items)

    def __repr__(self):
        return f'<PurchaseOrder {self.po_number}>'


class PurchaseOrderItem(db.Model):
    """Itens em um pedido de compra"""
    id = db.Column(db.Integer, primary_key=True)
    quantity = db.Column(db.Float, nullable=False)  # Quantidade do item
    received_quantity = db.Column(db.Float, default=0)  # Quantidade recebida
    unit_price = db.Column(db.Float, nullable=False)  # Preço unitário do item

    # Chaves estrangeiras
    purchase_order_id = db.Column(db.Integer, db.ForeignKey('purchase_order.id'), nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey('item.id'), nullable=False)

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relacionamentos
    purchase_order = relationship("PurchaseOrder", back_populates="items")
    item = relationship("Item", back_populates="purchase_orders")

    def __repr__(self):
        return f'<PurchaseOrderItem {self.quantity} of {self.item.name}>'

class Log(db.Model):
    """Modelo para armazenar logs do sistema"""
    id = db.Column(db.Integer, primary_key=True)
    log_level = db.Column(db.String(10), nullable=False)  # INFO, WARNING, ERROR, etc.
    message = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    user = relationship("User")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Log {self.id}: {self.log_level} - {self.message[:50]}>'

class Setting(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(50), unique=True, nullable=False)
    value = db.Column(db.Text, nullable=False)
    description = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<Setting {self.key}>'
