from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from datetime import datetime

from app import app, db
from models import Project, Item, project_items, Movement, MovementType
from forms import ProjectForm, ProjectItemForm

# Routes for project management

@app.route('/projects')
@login_required
def projects():
    # Filter projects by status if requested
    status_filter = request.args.get('status', 'all')
    
    if status_filter != 'all':
        projects = Project.query.filter_by(status=status_filter).order_by(Project.created_at.desc()).all()
    else:
        projects = Project.query.order_by(Project.created_at.desc()).all()
    
    context = {
        'title': 'Projetos',
        'projects': projects,
        'status_filter': status_filter,
        'statuses': [
            {'value': 'all', 'label': 'Todos'},
            {'value': 'active', 'label': 'Ativos'},
            {'value': 'completed', 'label': 'Concluídos'},
            {'value': 'cancelled', 'label': 'Cancelados'}
        ]
    }
    
    return render_template('projects/projects.html', **context)

@app.route('/projects/new', methods=['GET', 'POST'])
@login_required
def new_project():
    form = ProjectForm()
    
    if form.validate_on_submit():
        # Convert string dates to Python date objects
        start_date = datetime.strptime(form.start_date.data, '%Y-%m-%d').date() if form.start_date.data else None
        end_date = datetime.strptime(form.end_date.data, '%Y-%m-%d').date() if form.end_date.data else None
        
        project = Project(
            name=form.name.data,
            description=form.description.data,
            status=form.status.data,
            start_date=start_date,
            end_date=end_date,
            client_name=form.client_name.data
        )
        
        db.session.add(project)
        db.session.commit()
        
        flash('Projeto criado com sucesso', 'success')
        return redirect(url_for('project_detail', project_id=project.id))
    
    return render_template('projects/project_form.html', form=form, title='Novo Projeto')

@app.route('/projects/<int:project_id>')
@login_required
def project_detail(project_id):
    project = Project.query.get_or_404(project_id)
    
    # Get items associated with the project
    query = db.session.query(
        Item, project_items.c.quantity
    ).join(
        project_items
    ).filter(
        project_items.c.project_id == project_id
    )
    
    project_items_list = query.all()
    
    # Get related movements
    movements = Movement.query.filter_by(project_id=project_id).order_by(Movement.created_at.desc()).all()
    
    context = {
        'title': f'Projeto: {project.name}',
        'project': project,
        'project_items': project_items_list,
        'movements': movements
    }
    
    return render_template('projects/project_detail.html', **context)

@app.route('/projects/<int:project_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_project(project_id):
    project = Project.query.get_or_404(project_id)
    form = ProjectForm(obj=project)
    
    # Convert date objects to strings for the form
    if project.start_date:
        form.start_date.data = project.start_date.strftime('%Y-%m-%d')
    if project.end_date:
        form.end_date.data = project.end_date.strftime('%Y-%m-%d')
    
    if form.validate_on_submit():
        # Convert string dates to Python date objects
        start_date = datetime.strptime(form.start_date.data, '%Y-%m-%d').date() if form.start_date.data else None
        end_date = datetime.strptime(form.end_date.data, '%Y-%m-%d').date() if form.end_date.data else None
        
        project.name = form.name.data
        project.description = form.description.data
        project.status = form.status.data
        project.start_date = start_date
        project.end_date = end_date
        project.client_name = form.client_name.data
        
        db.session.commit()
        
        flash('Projeto atualizado com sucesso', 'success')
        return redirect(url_for('project_detail', project_id=project.id))
    
    return render_template('projects/project_form.html', form=form, title='Editar Projeto', project=project)

@app.route('/projects/<int:project_id>/add_item', methods=['GET', 'POST'])
@login_required
def add_project_item(project_id):
    project = Project.query.get_or_404(project_id)
    form = ProjectItemForm()
    
    # Populate item choices
    form.item_id.choices = [(i.id, i.name) for i in Item.query.order_by(Item.name).all()]
    
    if form.validate_on_submit():
        # Check if item is already in project
        exists = db.session.query(project_items).filter_by(
            project_id=project_id, 
            item_id=form.item_id.data
        ).first()
        
        if exists:
            flash('Item já adicionado ao projeto. Edite a quantidade existente.', 'warning')
        else:
            # Add new association
            stmt = project_items.insert().values(
                project_id=project_id,
                item_id=form.item_id.data,
                quantity=form.quantity.data
            )
            db.session.execute(stmt)
            db.session.commit()
            
            flash('Item adicionado ao projeto com sucesso', 'success')
            return redirect(url_for('project_detail', project_id=project_id))
    
    return render_template('projects/project_item_form.html', form=form, project=project, title='Adicionar Item ao Projeto')

@app.route('/projects/<int:project_id>/edit_item/<int:item_id>', methods=['GET', 'POST'])
@login_required
def edit_project_item(project_id, item_id):
    project = Project.query.get_or_404(project_id)
    item = Item.query.get_or_404(item_id)
    
    # Get current quantity
    current = db.session.query(project_items).filter_by(
        project_id=project_id, 
        item_id=item_id
    ).first()
    
    if not current:
        flash('Item não encontrado no projeto', 'danger')
        return redirect(url_for('project_detail', project_id=project_id))
    
    form = ProjectItemForm()
    form.item_id.choices = [(item.id, item.name)]
    form.item_id.data = item.id
    form.quantity.data = current.quantity
    
    if form.validate_on_submit():
        # Update quantity
        stmt = project_items.update().where(
            (project_items.c.project_id == project_id) & 
            (project_items.c.item_id == item_id)
        ).values(
            quantity=form.quantity.data
        )
        db.session.execute(stmt)
        db.session.commit()
        
        flash('Quantidade atualizada com sucesso', 'success')
        return redirect(url_for('project_detail', project_id=project_id))
    
    return render_template(
        'projects/project_item_form.html', 
        form=form, 
        project=project, 
        item=item, 
        title='Editar Item do Projeto'
    )

@app.route('/projects/<int:project_id>/remove_item/<int:item_id>')
@login_required
def remove_project_item(project_id, item_id):
    project = Project.query.get_or_404(project_id)
    item = Item.query.get_or_404(item_id)
    
    # Delete association
    stmt = project_items.delete().where(
        (project_items.c.project_id == project_id) & 
        (project_items.c.item_id == item_id)
    )
    db.session.execute(stmt)
    db.session.commit()
    
    flash(f'Item {item.name} removido do projeto', 'success')
    return redirect(url_for('project_detail', project_id=project_id))

@app.route('/projects/<int:project_id>/status/<status>')
@login_required
def update_project_status(project_id, status):
    project = Project.query.get_or_404(project_id)
    
    if status in ['active', 'completed', 'cancelled']:
        project.status = status
        
        # If completed, set end date to today if not already set
        if status == 'completed' and not project.end_date:
            project.end_date = datetime.utcnow().date()
            
        db.session.commit()
        flash(f'Status do projeto atualizado para {status}', 'success')
    else:
        flash('Status inválido', 'danger')
    
    return redirect(url_for('project_detail', project_id=project_id))
