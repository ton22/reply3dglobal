"""
Script para inicializar dados básicos no banco de dados.
Inclui tipos de movimentação, tipos de item, unidades de medida, etc.
"""
from app import app, db
from models import MovementType, ItemType, MeasurementUnit, Brand
from datetime import datetime

def initialize_movement_types():
    """Inicializa os tipos de movimentação no banco de dados"""
    
    # Lista de tipos de movimentação padrão
    movement_types = [
        {
            'name': 'Entrada',
            'description': 'Entrada de itens no estoque',
            'affects_stock': True
        },
        {
            'name': 'Saída',
            'description': 'Saída de itens do estoque',
            'affects_stock': True
        },
        {
            'name': 'Transferência',
            'description': 'Transferência de itens entre sub-estoques',
            'affects_stock': True
        },
        # {
        #     'name': 'Ajuste',
        #     'description': 'Ajuste de quantidade no estoque',
        #     'affects_stock': True
        # },
        # {
        #     'name': 'Inventário',
        #     'description': 'Contagem de inventário',
        #     'affects_stock': True
        # },
        # {
        #     'name': 'Consumo',
        #     'description': 'Consumo de material em projeto',
        #     'affects_stock': True
        # },
        # {
        #     'name': 'Perda',
        #     'description': 'Perda ou desperdício de material',
        #     'affects_stock': True
        # },
        # {
        #     'name': 'Devolução',
        #     'description': 'Devolução de material ao estoque',
        #     'affects_stock': True
        # },
        {
            'name': 'Reciclagem',
            'description': 'Material enviado para reciclagem',
            'affects_stock': True
        }
    ]
    
    # Verifica se já existem registros
    if MovementType.query.count() == 0:
        print("Inicializando tipos de movimentação...")
        for type_data in movement_types:
            movement_type = MovementType(
                name=type_data['name'],
                description=type_data['description'],
                affects_stock=type_data['affects_stock'],
                created_at=datetime.utcnow()
            )
            db.session.add(movement_type)
        
        db.session.commit()
        print(f"{len(movement_types)} tipos de movimentação criados.")
    else:
        print("Tipos de movimentação já existem no banco.")

def initialize_item_types():
    """Inicializa os tipos de item no banco de dados"""
    
    # Lista de tipos de item padrão para uma empresa de impressão 3D
    item_types = [
        {
            'name': 'Filamento',
            'description': 'Filamentos para impressão 3D (PLA, ABS, PETG, etc)'
        },
        {
            'name': 'Resina',
            'description': 'Resinas para impressão 3D SLA/DLP'
        },
        {
            'name': 'Peça',
            'description': 'Peças produzidas ou componentes'
        },
        {
            'name': 'Equipamento',
            'description': 'Equipamentos e máquinas'
        },
        {
            'name': 'Ferramenta',
            'description': 'Ferramentas e utensílios'
        },
        # {
        #     'name': 'Consumível',
        #     'description': 'Materiais consumíveis (luvas, álcool, acetona, etc)'
        # },
        {
            'name': 'Componente',
            'description': 'Componentes para montagem (parafusos, porcas, eletrônicos, etc)'
        }
    ]
    
    # Verifica se já existem registros
    if ItemType.query.count() == 0:
        print("Inicializando tipos de item...")
        for type_data in item_types:
            item_type = ItemType(
                name=type_data['name'],
                description=type_data['description'],
                created_at=datetime.utcnow()
            )
            db.session.add(item_type)
        
        db.session.commit()
        print(f"{len(item_types)} tipos de item criados.")
    else:
        print("Tipos de item já existem no banco.")

def initialize_measurement_units():
    """Inicializa as unidades de medida no banco de dados"""
    
    # Lista de unidades de medida padrão
    units = [
        {
            'name': 'Quilograma',
            'symbol': 'kg',
            'description': 'Unidade de massa'
        },
        # {
        #     'name': 'Grama',
        #     'symbol': 'g',
        #     'description': 'Unidade de massa'
        # },
        # {
        #     'name': 'Metro',
        #     'symbol': 'm',
        #     'description': 'Unidade de comprimento'
        # },
        # {
        #     'name': 'Centímetro',
        #     'symbol': 'cm',
        #     'description': 'Unidade de comprimento'
        # },
        # {
        #     'name': 'Milímetro',
        #     'symbol': 'mm',
        #     'description': 'Unidade de comprimento'
        # },
        # {
        #     'name': 'Litro',
        #     'symbol': 'L',
        #     'description': 'Unidade de volume'
        # },
        # {
        #     'name': 'Mililitro',
        #     'symbol': 'mL',
        #     'description': 'Unidade de volume'
        # },
        {
            'name': 'Unidade',
            'symbol': 'un',
            'description': 'Unidade de contagem'
        },
        {
            'name': 'Peça',
            'symbol': 'pç',
            'description': 'Unidade de contagem de peças'
        },
        {
            'name': 'Rolo',
            'symbol': 'rolo',
            'description': 'Unidade de contagem de rolos'
        },
        {
            'name': 'Caixa',
            'symbol': 'cx',
            'description': 'Unidade de contagem de caixas'
        },
        {
            'name': 'Par',
            'symbol': 'par',
            'description': 'Unidade de contagem de pares'
        }
    ]
    
    # Verifica se já existem registros
    if MeasurementUnit.query.count() == 0:
        print("Inicializando unidades de medida...")
        for unit_data in units:
            unit = MeasurementUnit(
                name=unit_data['name'],
                symbol=unit_data['symbol'],
                description=unit_data['description'],
                created_at=datetime.utcnow()
            )
            db.session.add(unit)
        
        db.session.commit()
        print(f"{len(units)} unidades de medida criadas.")
    else:
        print("Unidades de medida já existem no banco.")

def initialize_brands():
    """Inicializa as marcas no banco de dados"""
    brands = [
        {
            'name': 'Sem Marca',
            'description': 'Item sem marca específica'
        },
        {
            'name': 'XYZ Industries',
            'description': 'Fabricante de componentes industriais'
        },
        {
            'name': 'Premium Parts',
            'description': 'Componentes de alta qualidade'
        },
        {
            'name': 'Basic Tools',
            'description': 'Ferramentas básicas'
        },
        {
            'name': 'Tech Solutions',
            'description': 'Soluções tecnológicas'
        },
        {
            'name': 'Filament Pro',
            'description': 'Filamentos 3D de alta qualidade'
        },
        {
            'name': 'PrintMate',
            'description': 'Acessórios e peças para impressoras 3D'
        }
    ]
    
    for brand_data in brands:
        brand = Brand(
            name=brand_data['name'],
            description=brand_data['description']
        )
        db.session.add(brand)
    db.session.commit()
    print("Marcas inicializadas com sucesso!")

def initialize_all():
    """Inicializa todos os dados básicos"""
    try:
        # Verifica se já existem tipos de movimentação
        if MovementType.query.count() > 0:
            print("Tipos de movimentação já existem no banco.")
        else:
            initialize_movement_types()
            print("Tipos de movimentação criados.")

        # Verifica se já existem tipos de item
        if ItemType.query.count() > 0:
            print("Tipos de item já existem no banco.")
        else:
            initialize_item_types()
            print("Tipos de item criados.")

        # Verifica se já existem unidades de medida
        if MeasurementUnit.query.count() > 0:
            print("Unidades de medida já existem no banco.")
        else:
            initialize_measurement_units()
            print("Unidades de medida criadas.")

        # Verifica se já existem marcas
        if Brand.query.count() > 0:
            print("Marcas já existem no banco.")
        else:
            initialize_brands()
            print("Marcas criadas.")

        db.session.commit()
        print("Inicialização de dados concluída com sucesso!")

    except Exception as e:
        db.session.rollback()
        print(f"Erro ao inicializar dados: {str(e)}")
        raise

if __name__ == "__main__":
    with app.app_context():
        initialize_all()