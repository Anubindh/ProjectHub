
from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from sqlalchemy import inspect, text
from dotenv import load_dotenv
import os
import re
from datetime import datetime

load_dotenv()

app = Flask(__name__)

# Application configuration

app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')

if not app.config['SECRET_KEY']:
    raise RuntimeError("SECRET_KEY is not set. Please configure it in your .env file.")

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///projects.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_SECURE'] = (
    os.environ.get('FLASK_ENV') == 'production'
)

app.config['PERMANENT_SESSION_LIFETIME'] = 1800
app.config['WTF_CSRF_ENABLED'] = True
app.config['WTF_CSRF_TIME_LIMIT'] = 3600

db = SQLAlchemy(app)

# CSRF protection

csrf = CSRFProtect(app)


# Prevent Browser Caching

@app.after_request
def prevent_cache(response):

    response.headers["Cache-Control"] = (
        "no-store, no-cache, must-revalidate, max-age=0"
    )

    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"

    return response


# Allowed values

VALID_STATUSES = ['Pending', 'In Progress', 'Completed']

VALID_PROBABILITIES = ['Low', 'Medium', 'High']
VALID_IMPACTS = ['Low', 'Medium', 'High']
VALID_RISK_STATUSES = ['Open', 'In Progress', 'Resolved']


# User Database Model

class User(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(256), nullable=False)


# Project Database Model

class Project(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text)
    status = db.Column(db.String(50), default='Pending')
    progress = db.Column(db.Integer, default=0)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey('user.id'),
        nullable=True
    )


# Task Database Model

class Task(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    status = db.Column(db.String(50), default='Pending')
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'))
    user_id = db.Column(
        db.Integer,
        db.ForeignKey('user.id'),
        nullable=True
    )


# Risk Database Model

class Risk(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text)

    probability = db.Column(db.String(20), nullable=False)
    impact = db.Column(db.String(20), nullable=False)
    risk_level = db.Column(db.String(20), nullable=False)

    mitigation = db.Column(db.Text)
    status = db.Column(db.String(30), default='Open')

    project_id = db.Column(
        db.Integer,
        db.ForeignKey('project.id'),
        nullable=True
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey('user.id'),
        nullable=True
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    project = db.relationship(
        'Project',
        backref=db.backref('risks', lazy=True)
    )


# Login Protection

def login_required(route_function):

    @wraps(route_function)
    def decorated_function(*args, **kwargs):

        if 'user_id' not in session:
            flash('Please login to access your dashboard.')
            return redirect(url_for('login'))

        user = db.session.get(User, session['user_id'])

        if not user:
            session.clear()
            flash('Please login again.')
            return redirect(url_for('login'))

        return route_function(*args, **kwargs)

    return decorated_function


# Input Validation Helpers

def get_valid_status(value):

    if value in VALID_STATUSES:
        return value

    return None


def get_valid_progress(value):

    try:
        progress = int(value)
        return max(0, min(100, progress))
    except (ValueError, TypeError):
        return None


def get_valid_project_id(value):

    if not value:
        return None

    try:
        project_id = int(value)

        if project_id <= 0:
            return None

        return project_id

    except (ValueError, TypeError):
        return None


def calculate_risk_level(probability, impact):

    scores = {
        'Low': 1,
        'Medium': 2,
        'High': 3
    }

    score = scores[probability] * scores[impact]

    if score <= 2:
        return 'Low'
    elif score <= 4:
        return 'Medium'

    return 'High'


def get_valid_risk_project(project_value):

    if not project_value:
        return None

    project_id = get_valid_project_id(project_value)

    if project_id is None:
        return False

    project = Project.query.filter_by(
        id=project_id,
        user_id=session['user_id']
    ).first()

    return project if project else False


# User Registration

@app.route('/register', methods=['GET', 'POST'])
def register():

    if request.method == 'POST':

        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        if not name or len(name) > 100:
            flash('Enter a valid name.')
            return redirect(url_for('register'))

        if (
            not email
            or len(email) > 150
            or not re.fullmatch(r'[^@\s]+@[^@\s]+\.[^@\s]+', email)
        ):
            flash('Enter a valid email address.')
            return redirect(url_for('register'))

        if len(password) < 8:
            flash('Password must contain at least 8 characters.')
            return redirect(url_for('register'))

        existing_user = User.query.filter_by(email=email).first()

        if existing_user:
            flash('Email already registered. Please login.')
            return redirect(url_for('login'))

        new_user = User(
            name=name,
            email=email,
            password=generate_password_hash(password)
        )

        db.session.add(new_user)
        db.session.commit()

        flash('Registration successful. Please login.')
        return redirect(url_for('login'))

    return render_template('register.html')


# User Login

@app.route('/login', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':

        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password, password):

            session.clear()
            session.permanent = True
            session['user_id'] = user.id

            return redirect(url_for('dashboard'))

        flash('Invalid email or password.')

    return render_template('login.html')


# User Logout - POST Only with CSRF Protection

@app.route('/logout', methods=['POST'])
@login_required
def logout():

    session.clear()
    flash('You have been logged out.')

    return redirect(url_for('login'))


# Dashboard

@app.route('/')
@login_required
def dashboard():

    user_id = session['user_id']

    projects = Project.query.filter_by(user_id=user_id).all()
    tasks = Task.query.filter_by(user_id=user_id).all()

    total_projects = len(projects)
    total_tasks = len(tasks)

    completed_projects = Project.query.filter_by(
        user_id=user_id,
        status='Completed'
    ).count()

    pending_tasks = Task.query.filter_by(
        user_id=user_id,
        status='Pending'
    ).count()

    in_progress_tasks = Task.query.filter_by(
        user_id=user_id,
        status='In Progress'
    ).count()

    completed_tasks = Task.query.filter_by(
        user_id=user_id,
        status='Completed'
    ).count()

    current_user = db.session.get(User, user_id)

    return render_template(
        'index.html',
        projects=projects,
        tasks=tasks,
        total_projects=total_projects,
        total_tasks=total_tasks,
        completed_projects=completed_projects,
        pending_tasks=pending_tasks,
        in_progress_tasks=in_progress_tasks,
        completed_tasks=completed_tasks,
        current_user=current_user
    )


# Tasks Page

@app.route('/tasks')
@login_required
def tasks_page():

    user_id = session['user_id']

    tasks = Task.query.filter_by(
        user_id=user_id
    ).order_by(Task.id.desc()).all()

    projects = Project.query.filter_by(
        user_id=user_id
    ).all()

    total_tasks = len(tasks)

    pending_tasks = Task.query.filter_by(
        user_id=user_id,
        status='Pending'
    ).count()

    in_progress_tasks = Task.query.filter_by(
        user_id=user_id,
        status='In Progress'
    ).count()

    completed_tasks = Task.query.filter_by(
        user_id=user_id,
        status='Completed'
    ).count()

    current_user = db.session.get(User, user_id)

    return render_template(
        'tasks.html',
        tasks=tasks,
        projects=projects,
        total_tasks=total_tasks,
        pending_tasks=pending_tasks,
        in_progress_tasks=in_progress_tasks,
        completed_tasks=completed_tasks,
        current_user=current_user
    )


# Risks Page

@app.route('/risks')
@login_required
def risks_page():

    user_id = session['user_id']

    risks = Risk.query.filter_by(
        user_id=user_id
    ).order_by(Risk.id.desc()).all()

    projects = Project.query.filter_by(
        user_id=user_id
    ).all()

    total_risks = len(risks)

    open_risks = Risk.query.filter_by(
        user_id=user_id,
        status='Open'
    ).count()

    in_progress_risks = Risk.query.filter_by(
        user_id=user_id,
        status='In Progress'
    ).count()

    resolved_risks = Risk.query.filter_by(
        user_id=user_id,
        status='Resolved'
    ).count()

    high_risks = Risk.query.filter_by(
        user_id=user_id,
        risk_level='High'
    ).count()

    current_user = db.session.get(User, user_id)

    return render_template(
        'risks.html',
        risks=risks,
        projects=projects,
        total_risks=total_risks,
        open_risks=open_risks,
        in_progress_risks=in_progress_risks,
        resolved_risks=resolved_risks,
        high_risks=high_risks,
        current_user=current_user
    )


# Add Project

@app.route('/add_project', methods=['POST'])
@login_required
def add_project():

    name = request.form.get('name', '').strip()
    description = request.form.get('description', '').strip()
    status = get_valid_status(
        request.form.get('status', 'Pending')
    )
    progress = get_valid_progress(
        request.form.get('progress', 0)
    )

    if not name or len(name) > 150:
        flash('Project name is required and must be under 150 characters.')
        return redirect(url_for('dashboard'))

    if not status or progress is None:
        flash('Please enter valid project details.')
        return redirect(url_for('dashboard'))

    new_project = Project(
        name=name,
        description=description,
        status=status,
        progress=progress,
        user_id=session['user_id']
    )

    db.session.add(new_project)
    db.session.commit()

    flash('Project added successfully.')
    return redirect(url_for('dashboard'))


# Edit Project

@app.route('/edit_project/<int:id>', methods=['POST'])
@login_required
def edit_project(id):

    project = Project.query.filter_by(
        id=id,
        user_id=session['user_id']
    ).first_or_404()

    name = request.form.get('name', '').strip()
    description = request.form.get('description', '').strip()
    status = get_valid_status(request.form.get('status'))
    progress = get_valid_progress(request.form.get('progress'))

    if not name or len(name) > 150:
        flash('Enter a valid project name.')
        return redirect(url_for('dashboard'))

    if not status or progress is None:
        flash('Please enter valid project details.')
        return redirect(url_for('dashboard'))

    project.name = name
    project.description = description
    project.status = status
    project.progress = progress

    db.session.commit()

    flash('Project updated successfully.')
    return redirect(url_for('dashboard'))


# Delete Project

@app.route('/delete_project/<int:id>', methods=['POST'])
@login_required
def delete_project(id):

    project = Project.query.filter_by(
        id=id,
        user_id=session['user_id']
    ).first_or_404()

    Task.query.filter_by(
        project_id=project.id,
        user_id=session['user_id']
    ).update({'project_id': None})

    Risk.query.filter_by(
        project_id=project.id,
        user_id=session['user_id']
    ).update({'project_id': None})

    db.session.delete(project)
    db.session.commit()

    flash('Project deleted successfully.')
    return redirect(url_for('dashboard'))


# Add Task

@app.route('/add_task', methods=['POST'])
@login_required
def add_task():

    title = request.form.get('title', '').strip()
    project_value = request.form.get('project_id', '').strip()

    if not title or len(title) > 150:
        flash('Task title is required and must be under 150 characters.')
        return redirect(url_for('dashboard'))

    project_id = None

    if project_value:

        project_id = get_valid_project_id(project_value)

        if project_id is None:
            flash('Invalid project selection.')
            return redirect(url_for('dashboard'))

        project = Project.query.filter_by(
            id=project_id,
            user_id=session['user_id']
        ).first()

        if not project:
            flash('Invalid project selection.')
            return redirect(url_for('dashboard'))

    new_task = Task(
        title=title,
        project_id=project_id,
        user_id=session['user_id']
    )

    db.session.add(new_task)
    db.session.commit()

    flash('Task added successfully.')
    return redirect(url_for('dashboard'))


# Edit Task

@app.route('/edit_task/<int:id>', methods=['POST'])
@login_required
def edit_task(id):

    task = Task.query.filter_by(
        id=id,
        user_id=session['user_id']
    ).first_or_404()

    title = request.form.get('title', '').strip()
    status = get_valid_status(request.form.get('status'))
    project_value = request.form.get('project_id', '').strip()

    if not title or len(title) > 150:
        flash('Enter a valid task title.')
        return redirect(url_for('dashboard'))

    if not status:
        flash('Please select a valid task status.')
        return redirect(url_for('dashboard'))

    project_id = None

    if project_value:

        project_id = get_valid_project_id(project_value)

        if project_id is None:
            flash('Invalid project selection.')
            return redirect(url_for('dashboard'))

        project = Project.query.filter_by(
            id=project_id,
            user_id=session['user_id']
        ).first()

        if not project:
            flash('Invalid project selection.')
            return redirect(url_for('dashboard'))

    task.title = title
    task.status = status
    task.project_id = project_id

    db.session.commit()

    flash('Task updated successfully.')
    return redirect(url_for('dashboard'))


# Delete Task

@app.route('/delete_task/<int:id>', methods=['POST'])
@login_required
def delete_task(id):

    task = Task.query.filter_by(
        id=id,
        user_id=session['user_id']
    ).first_or_404()

    db.session.delete(task)
    db.session.commit()

    flash('Task deleted successfully.')
    return redirect(url_for('dashboard'))


# Add Risk

@app.route('/add_risk', methods=['POST'])
@login_required
def add_risk():

    title = request.form.get('title', '').strip()
    description = request.form.get('description', '').strip()
    probability = request.form.get('probability', '')
    impact = request.form.get('impact', '')
    mitigation = request.form.get('mitigation', '').strip()
    status = request.form.get('status', 'Open')
    project_value = request.form.get('project_id', '').strip()

    if not title or len(title) > 150:
        flash('Risk title is required and must be under 150 characters.')
        return redirect(url_for('risks_page'))

    if probability not in VALID_PROBABILITIES:
        flash('Please select a valid probability.')
        return redirect(url_for('risks_page'))

    if impact not in VALID_IMPACTS:
        flash('Please select a valid impact.')
        return redirect(url_for('risks_page'))

    if status not in VALID_RISK_STATUSES:
        flash('Please select a valid risk status.')
        return redirect(url_for('risks_page'))

    if len(description) > 3000 or len(mitigation) > 3000:
        flash('Description and mitigation plan must be under 3000 characters.')
        return redirect(url_for('risks_page'))

    project = get_valid_risk_project(project_value)

    if project is False:
        flash('Invalid project selection.')
        return redirect(url_for('risks_page'))

    new_risk = Risk(
        title=title,
        description=description,
        probability=probability,
        impact=impact,
        risk_level=calculate_risk_level(probability, impact),
        mitigation=mitigation,
        status=status,
        project_id=project.id if project else None,
        user_id=session['user_id']
    )

    db.session.add(new_risk)
    db.session.commit()

    flash('Risk added successfully.')
    return redirect(url_for('risks_page'))


# Edit Risk

@app.route('/edit_risk/<int:id>', methods=['POST'])
@login_required
def edit_risk(id):

    risk = Risk.query.filter_by(
        id=id,
        user_id=session['user_id']
    ).first_or_404()

    title = request.form.get('title', '').strip()
    description = request.form.get('description', '').strip()
    probability = request.form.get('probability', '')
    impact = request.form.get('impact', '')
    mitigation = request.form.get('mitigation', '').strip()
    status = request.form.get('status', '')
    project_value = request.form.get('project_id', '').strip()

    if not title or len(title) > 150:
        flash('Enter a valid risk title.')
        return redirect(url_for('risks_page'))

    if probability not in VALID_PROBABILITIES:
        flash('Please select a valid probability.')
        return redirect(url_for('risks_page'))

    if impact not in VALID_IMPACTS:
        flash('Please select a valid impact.')
        return redirect(url_for('risks_page'))

    if status not in VALID_RISK_STATUSES:
        flash('Please select a valid risk status.')
        return redirect(url_for('risks_page'))

    if len(description) > 3000 or len(mitigation) > 3000:
        flash('Description and mitigation plan must be under 3000 characters.')
        return redirect(url_for('risks_page'))

    project = get_valid_risk_project(project_value)

    if project is False:
        flash('Invalid project selection.')
        return redirect(url_for('risks_page'))

    risk.title = title
    risk.description = description
    risk.probability = probability
    risk.impact = impact
    risk.risk_level = calculate_risk_level(probability, impact)
    risk.mitigation = mitigation
    risk.status = status
    risk.project_id = project.id if project else None

    db.session.commit()

    flash('Risk updated successfully.')
    return redirect(url_for('risks_page'))


# Delete Risk

@app.route('/delete_risk/<int:id>', methods=['POST'])
@login_required
def delete_risk(id):

    risk = Risk.query.filter_by(
        id=id,
        user_id=session['user_id']
    ).first_or_404()

    db.session.delete(risk)
    db.session.commit()

    flash('Risk deleted successfully.')
    return redirect(url_for('risks_page'))


# Database Creation and Existing Data Migration

with app.app_context():

    db.create_all()

    inspector = inspect(db.engine)

    project_columns = [
        column['name']
        for column in inspector.get_columns('project')
    ]

    task_columns = [
        column['name']
        for column in inspector.get_columns('task')
    ]

    with db.engine.begin() as connection:

        if 'user_id' not in project_columns:
            connection.execute(
                text(
                    'ALTER TABLE project '
                    'ADD COLUMN user_id INTEGER REFERENCES user(id)'
                )
            )

        if 'user_id' not in task_columns:
            connection.execute(
                text(
                    'ALTER TABLE task '
                    'ADD COLUMN user_id INTEGER REFERENCES user(id)'
                )
            )

        connection.execute(text("""
            UPDATE project
            SET user_id = (SELECT MIN(id) FROM user)
            WHERE user_id IS NULL
              AND EXISTS (SELECT 1 FROM user)
        """))

        connection.execute(text("""
            UPDATE task
            SET user_id = (
                SELECT user_id
                FROM project
                WHERE project.id = task.project_id
            )
            WHERE user_id IS NULL
              AND project_id IS NOT NULL
        """))

        connection.execute(text("""
            UPDATE task
            SET user_id = (SELECT MIN(id) FROM user)
            WHERE user_id IS NULL
              AND EXISTS (SELECT 1 FROM user)
        """))


# Run Application

if __name__ == '__main__':
    app.run(debug=True)
