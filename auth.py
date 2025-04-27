from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from app import app, db
from models import User
from forms import LoginForm, RegisterForm, ProfileForm

# Routes for authentication and user management
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        
        if user and check_password_hash(user.password_hash, form.password.data):
            login_user(user, remember=form.remember.data)
            
            # Update last login time
            user.last_login = datetime.utcnow()
            db.session.commit()
            
            # Redirect to the page the user was trying to access
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            return redirect(url_for('dashboard'))
        else:
            flash('Nome de usuário ou senha inválidos', 'danger')
    
    return render_template('login.html', form=form, year=datetime.now().year)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    # flash('Você saiu do sistema com sucesso', 'info')
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    # Check if there are any users yet
    first_user = User.query.first() is None
    
    # If not the first user and current user is not admin, redirect
    if not first_user and (not current_user.is_authenticated or current_user.role != 'admin'):
        flash('Apenas administradores podem adicionar novos usuários', 'danger')
        return redirect(url_for('login'))
    
    form = RegisterForm()
    if form.validate_on_submit():
        # Check if username or email already exists
        existing_user = User.query.filter(
            (User.username == form.username.data) | 
            (User.email == form.email.data)
        ).first()
        
        if existing_user:
            flash('Nome de usuário ou e-mail já cadastrado', 'danger')
        else:
            # Create new user
            hashed_password = generate_password_hash(form.password.data)
            
            # First user is admin, others are regular users
            role = 'admin' if first_user else 'user'
            
            new_user = User(
                username=form.username.data,
                email=form.email.data,
                password_hash=hashed_password,
                role=role
            )
            
            db.session.add(new_user)
            db.session.commit()
            
            flash('Usuário cadastrado com sucesso', 'success')
            
            # If it's the first user, log them in
            if first_user:
                login_user(new_user)
                return redirect(url_for('dashboard'))
            
            return redirect(url_for('login'))
    
    context = {
        'form': form, 
        'title': 'Registro de Usuário',
        'first_user': first_user
    }
    return render_template('register.html', **context)

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    form = ProfileForm(obj=current_user)
    
    if form.validate_on_submit():
        # Update user information
        current_user.username = form.username.data
        current_user.email = form.email.data
        
        # Update password if provided
        if form.new_password.data:
            if check_password_hash(current_user.password_hash, form.current_password.data):
                current_user.password_hash = generate_password_hash(form.new_password.data)
                flash('Senha atualizada com sucesso', 'success')
            else:
                flash('Senha atual incorreta', 'danger')
                return render_template('profile.html', form=form, title='Meu Perfil')
        
        db.session.commit()
        flash('Perfil atualizado com sucesso', 'success')
        return redirect(url_for('profile'))
    
    return render_template('profile.html', form=form, title='Meu Perfil')

@app.route('/users')
@login_required
def users():
    # Only admins can view all users
    if current_user.role != 'admin':
        flash('Acesso restrito a administradores', 'danger')
        return redirect(url_for('dashboard'))
    
    users = User.query.all()
    return render_template('users.html', users=users, title='Usuários')

@app.route('/users/toggle_role/<int:user_id>')
@login_required
def toggle_role(user_id):
    # Only admins can change roles
    if current_user.role != 'admin':
        flash('Acesso restrito a administradores', 'danger')
        return redirect(url_for('dashboard'))
    
    user = User.query.get_or_404(user_id)
    
    # Don't allow changing your own role
    if user.id == current_user.id:
        flash('Você não pode alterar seu próprio perfil', 'danger')
        return redirect(url_for('users'))
    
    # Toggle role
    user.role = 'admin' if user.role == 'user' else 'user'
    db.session.commit()
    
    flash(f'Perfil de {user.username} alterado para {user.role}', 'success')
    return redirect(url_for('users'))
