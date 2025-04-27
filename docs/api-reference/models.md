# Database Models

This section describes the database models used in ThreeDStock.

## User Model

```python
class User(UserMixin, db.Model):
```

The User model handles authentication and user management.

### Fields

- `id`: Primary key
- `username`: Unique username
- `email`: Unique email address
- `password_hash`: Hashed password
- `role`: User role (default: 'user')
- `created_at`: Account creation timestamp
- `last_login`: Last login timestamp

### Relationships

- `movements`: Relationship to Movement
- `purchase_orders`: Relationship to PurchaseOrder
- `logs`: Relationship to Log

## Item Model

```python
class Item(db.Model):
```

Represents inventory items in the system.

### Fields

- `id`: Primary key
- `name`: Item name
- `description`: Item description
- `sku`: Stock Keeping Unit (unique)
- `barcode`: Barcode number (unique)
- `color`: Item color
- `minimum_stock`: Minimum stock level
- `item_type_id`: Foreign key to ItemType
- `unit_id`: Foreign key to MeasurementUnit
- `brand_id`: Foreign key to Brand

### Relationships

- `item_type`: Relationship to ItemType
- `unit`: Relationship to MeasurementUnit
- `brand`: Relationship to Brand
- `inventory_items`: Relationship to InventoryItem
- `movements`: Relationship to Movement
- `projects`: Relationship to Project
- `purchase_orders`: Relationship to PurchaseOrderItem

## ItemType Model

```python
class ItemType(db.Model):
```

Defines the types of items in the inventory.

### Fields

- `id`: Primary key
- `name`: Type name (unique)
- `description`: Type description
- `created_at`: Creation timestamp

### Relationships

- `items`: Relationship to Item

## MeasurementUnit Model

```python
class MeasurementUnit(db.Model):
```

Defines measurement units for items.

### Fields

- `id`: Primary key
- `name`: Unit name (unique)
- `symbol`: Unit symbol (unique)
- `description`: Unit description
- `created_at`: Creation timestamp

### Relationships

- `items`: Relationship to Item

## SubStock Model

```python
class SubStock(db.Model):
```

Represents different physical locations or departments for inventory.

### Fields

- `id`: Primary key
- `name`: SubStock name
- `description`: Description
- `location`: Physical location
- `created_at`: Creation timestamp

### Relationships

- `inventory_items`: Relationship to InventoryItem
- `outgoing_movements`: Relationship to Movement (outgoing)
- `incoming_movements`: Relationship to Movement (incoming)

## Brand Model

```python
class Brand(db.Model):
```

Represents item brands.

### Fields

- `id`: Primary key
- `name`: Brand name (unique)
- `description`: Brand description
- `created_at`: Creation timestamp

### Relationships

- `items`: Relationship to Item

## InventoryItem Model

```python
class InventoryItem(db.Model):
```

Represents the quantity of an item in a specific substock.

### Fields

- `id`: Primary key
- `quantity`: Quantity
- `item_id`: Foreign key to Item
- `substock_id`: Foreign key to SubStock
- `created_at`: Creation timestamp
- `updated_at`: Update timestamp

### Relationships

- `item`: Relationship to Item
- `substock`: Relationship to SubStock

## MovementType Model

```python
class MovementType(db.Model):
```

Defines types of inventory movements.

### Fields

- `id`: Primary key
- `name`: Movement type name (unique)
- `description`: Description
- `affects_stock`: Indicates if it affects stock
- `created_at`: Creation timestamp

### Relationships

- `movements`: Relationship to Movement

## Movement Model

```python
class Movement(db.Model):
```

Records movements of items between substocks.

### Fields

- `id`: Primary key
- `quantity`: Quantity moved
- `notes`: Notes
- `reference_code`: Reference code
- `item_id`: Foreign key to Item
- `movement_type_id`: Foreign key to MovementType
- `source_substock_id`: Foreign key to SubStock (source)
- `destination_substock_id`: Foreign key to SubStock (destination)
- `created_by_id`: Foreign key to User
- `project_id`: Foreign key to Project
- `purchase_order_id`: Foreign key to PurchaseOrder
- `created_at`: Creation timestamp

### Relationships

- `item`: Relationship to Item
- `movement_type`: Relationship to MovementType
- `source_substock`: Relationship to SubStock
- `destination_substock`: Relationship to SubStock
- `created_by`: Relationship to User
- `project`: Relationship to Project
- `purchase_order`: Relationship to PurchaseOrder

## Project Model

```python
class Project(db.Model):
```

Projects that consume inventory items.

### Fields

- `id`: Primary key
- `name`: Project name
- `description`: Description
- `status`: Project status
- `start_date`: Start date
- `end_date`: End date
- `client_name`: Client name
- `created_at`: Creation timestamp
- `updated_at`: Update timestamp

### Relationships

- `items`: Relationship to Item (via project_items)
- `movements`: Relationship to Movement

## PurchaseOrder Model

```python
class PurchaseOrder(db.Model):
```

Manages purchase orders for inventory replenishment.

### Fields

- `id`: Primary key
- `po_number`: Purchase order number (unique)
- `supplier`: Supplier
- `status`: Order status
- `notes`: Notes
- `created_by_id`: Foreign key to User
- `created_at`: Creation timestamp
- `updated_at`: Update timestamp
- `sent_at`: Sent timestamp
- `received_at`: Received timestamp

### Relationships

- `created_by`: Relationship to User
- `items`: Relationship to PurchaseOrderItem
- `movements`: Relationship to Movement

## PurchaseOrderItem Model

```python
class PurchaseOrderItem(db.Model):
```

Items included in a purchase order.

### Fields

- `id`: Primary key
- `quantity`: Requested quantity
- `received_quantity`: Received quantity
- `unit_price`: Unit price
- `purchase_order_id`: Foreign key to PurchaseOrder
- `item_id`: Foreign key to Item
- `created_at`: Creation timestamp

### Relationships

- `purchase_order`: Relationship to PurchaseOrder
- `item`: Relationship to Item

## Log Model

```python
class Log(db.Model):
```

Records system events.

### Fields

- `id`: Primary key
- `log_level`: Log level
- `message`: Message
- `user_id`: Foreign key to User
- `created_at`: Creation timestamp

### Relationships

- `user`: Relationship to User

## Setting Model

```python
class Setting(db.Model):
```

Stores system settings.

### Fields

- `id`: Primary key
- `key`: Setting key (unique)
- `value`: Setting value
- `description`: Description
- `created_at`: Creation timestamp
- `updated_at`: Update timestamp
