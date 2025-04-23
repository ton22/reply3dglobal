from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, TextAreaField
from wtforms import SelectField, FloatField, HiddenField, DateField, IntegerField
from wtforms.validators import DataRequired, Email, EqualTo, Length, Optional, NumberRange

# Authentication Forms

class LoginForm(FlaskForm):
    username = StringField('Nome de Usuário', validators=[DataRequired()])
    password = PasswordField('Senha', validators=[DataRequired()])
    remember = BooleanField('Lembrar-me')
    submit = SubmitField('Entrar')

class RegisterForm(FlaskForm):
    username = StringField('Nome de Usuário', validators=[DataRequired(), Length(min=3, max=64)])
    email = StringField('Email', validators=[DataRequired(), Email(), Length(max=120)])
    password = PasswordField('Senha', validators=[
        DataRequired(), 
        Length(min=8, message='A senha deve ter pelo menos 8 caracteres')
    ])
    confirm_password = PasswordField('Confirmar Senha', validators=[
        DataRequired(), 
        EqualTo('password', message='As senhas devem ser iguais')
    ])
    submit = SubmitField('Registrar')

class ProfileForm(FlaskForm):
    username = StringField('Nome de Usuário', validators=[DataRequired(), Length(min=3, max=64)])
    email = StringField('Email', validators=[DataRequired(), Email(), Length(max=120)])
    current_password = PasswordField('Senha Atual')
    new_password = PasswordField('Nova Senha', validators=[
        Optional(), 
        Length(min=8, message='A senha deve ter pelo menos 8 caracteres')
    ])
    confirm_new_password = PasswordField('Confirmar Nova Senha', validators=[
        EqualTo('new_password', message='As senhas devem ser iguais')
    ])
    submit = SubmitField('Atualizar Perfil')

# Inventory Forms
class ItemForm(FlaskForm):
    name = StringField('Nome', validators=[DataRequired(), Length(max=100)])
    description = TextAreaField('Descrição')
    sku = StringField('SKU (deixe em branco para gerar automaticamente)', validators=[Optional(), Length(max=50)])
    barcode = StringField('Código de Barras (deixe em branco para gerar automaticamente)', validators=[Optional(), Length(max=50)])
    color = StringField('Cor', validators=[Optional(), Length(max=50)])
    minimum_stock = FloatField('Estoque Mínimo', validators=[DataRequired(), NumberRange(min=0)])
    item_type_id = SelectField('Tipo de Item', validators=[DataRequired()], coerce=int)
    unit_id = SelectField('Unidade de Medida', validators=[DataRequired()], coerce=int)
    brand_id = SelectField('Marca', validators=[Optional()], coerce=int)
    submit = SubmitField('Salvar')

class ItemTypeForm(FlaskForm):
    name = StringField('Nome', validators=[DataRequired(), Length(max=50)])
    description = StringField('Descrição', validators=[Optional(), Length(max=255)])
    submit = SubmitField('Salvar')

class MeasurementUnitForm(FlaskForm):
    name = StringField('Nome', validators=[DataRequired(), Length(max=50)])
    symbol = StringField('Símbolo', validators=[DataRequired(), Length(max=10)])
    description = StringField('Descrição', validators=[Optional(), Length(max=255)])
    submit = SubmitField('Salvar')

class SubStockForm(FlaskForm):
    name = StringField('Nome', validators=[DataRequired(), Length(max=100)])
    description = StringField('Descrição', validators=[Optional(), Length(max=255)])
    location = StringField('Localização', validators=[Optional(), Length(max=100)])
    submit = SubmitField('Salvar')

class InventorySearchForm(FlaskForm):
    search = StringField('Buscar por nome ou SKU')
    item_type = SelectField('Filtrar por tipo', coerce=int, validators=[Optional()])
    submit = SubmitField('Buscar')

# Project Forms

class ProjectForm(FlaskForm):
    name = StringField('Nome', validators=[DataRequired(), Length(max=100)])
    description = TextAreaField('Descrição')
    status = SelectField('Status', choices=[
        ('active', 'Ativo'),
        ('completed', 'Concluído'),
        ('cancelled', 'Cancelado')
    ], default='active')
    start_date = StringField('Data de Início')
    end_date = StringField('Data de Término')
    client_name = StringField('Cliente', validators=[Optional(), Length(max=100)])
    submit = SubmitField('Salvar')

class ProjectItemForm(FlaskForm):
    item_id = SelectField('Item', validators=[DataRequired()], coerce=int)
    quantity = FloatField('Quantidade', validators=[DataRequired(), NumberRange(min=0.01)])
    submit = SubmitField('Salvar')

# Movement Forms

class MovementForm(FlaskForm):
    item_id = SelectField('Item', validators=[DataRequired()], coerce=int)
    movement_type_id = SelectField('Tipo de Movimentação', validators=[DataRequired()], coerce=int)
    item_name = StringField('Nome do Item', validators=[Optional()])
    quantity = FloatField('Quantidade', validators=[DataRequired(), NumberRange(min=0.01)])
    source_substock_id = SelectField('Origem', coerce=int)
    destination_substock_id = SelectField('Destino', coerce=int)
    project_id = SelectField('Projeto', coerce=int)
    purchase_order_id = SelectField('Pedido de Compra', coerce=int)
    reference_code = StringField('Código de Referência', validators=[Optional(), Length(max=50)])
    notes = TextAreaField('Observações')
    submit = SubmitField('Registrar Movimentação')

class PurchaseOrderForm(FlaskForm):
    po_number = StringField('Número do Pedido', validators=[Optional(), Length(max=50)])
    supplier = StringField('Fornecedor', validators=[DataRequired(), Length(max=100)])
    notes = TextAreaField('Observações')
    submit = SubmitField('Salvar')

class PurchaseOrderItemForm(FlaskForm):
    item_id = SelectField('Item', validators=[DataRequired()], coerce=int)
    quantity = FloatField('Quantidade', validators=[DataRequired(), NumberRange(min=0.01)])
    unit_price = FloatField('Preço Unitário', validators=[DataRequired()])  # Novo campo
    submit = SubmitField('Adicionar Item')

# Report Forms

class DateRangeForm(FlaskForm):
    start_date = StringField('Data Inicial')
    end_date = StringField('Data Final')
    submit = SubmitField('Filtrar')

# Settings Forms

class SettingsForm(FlaskForm):
    company_name = StringField('Nome da Empresa', validators=[DataRequired(), Length(max=100)])
    default_substock_id = SelectField('Sub-estoque Padrão', coerce=int)
    po_prefix = StringField('Prefixo de Pedido de Compra', validators=[Optional(), Length(max=20)])
    low_stock_alert = BooleanField('Mostrar alertas de estoque baixo no dashboard')
    theme = SelectField('Tema do Sistema', choices=[('dark', 'Escuro'), ('light', 'Claro')])
    email_notifications = BooleanField('Ativar notificações por e-mail')
    email_address = StringField('E-mail para notificações', validators=[Optional(), Email(), Length(max=120)])
    submit = SubmitField('Salvar Configurações')

# Stock Alert Form

class StockAlertForm(FlaskForm):
    item_id = SelectField('Item', validators=[DataRequired()], coerce=int)
    alert_threshold = FloatField('Limite para Alerta (%)', validators=[DataRequired(), NumberRange(min=1, max=200)])
    email_alert = BooleanField('Enviar alerta por e-mail')
    dashboard_alert = BooleanField('Mostrar alerta no dashboard')
    submit = SubmitField('Salvar Configuração de Alerta')

# Brand Form

class BrandForm(FlaskForm):
    name = StringField('Nome', validators=[DataRequired(), Length(max=100)])
    description = TextAreaField('Descrição', validators=[Length(max=255)])
    submit = SubmitField('Salvar')
