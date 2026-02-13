import os
import jwt
import bcrypt
from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime, timedelta
from functools import wraps
import re

app = Flask(__name__)
CORS(app)

# Configuration - Support both SQLite (local) and PostgreSQL (production)
DATABASE_URL = os.environ.get('DATABASE_URL', '')
JWT_SECRET = os.environ.get('JWT_SECRET', 'payroll-system-secret-key')
JWT_EXPIRATION = 86400 * 7  # 7 days

# Determine database type
if DATABASE_URL:
    # Production: Use PostgreSQL
    import psycopg2
    DB_TYPE = 'postgres'
else:
    # Local development: Use SQLite
    import sqlite3
    DB_TYPE = 'sqlite'
    DATABASE_PATH = os.path.join(os.path.dirname(__file__), 'payroll.db')

# ============ DATABASE CONNECTION ============
def get_db():
    """Get database connection (SQLite for local, PostgreSQL for production)"""
    try:
        if DB_TYPE == 'postgres':
            import psycopg2
            conn = psycopg2.connect(DATABASE_URL)
        else:
            import sqlite3
            conn = sqlite3.connect(DATABASE_PATH)
            conn.row_factory = sqlite3.Row
        return conn
    except Exception as e:
        print(f"Database connection error: {e}")
        raise

def init_db():
    """Initialize database tables"""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        if DB_TYPE == 'postgres':
            # PostgreSQL syntax
            sql_statements = [
                '''CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    email VARCHAR(255) UNIQUE NOT NULL,
                    password_hash VARCHAR(255) NOT NULL,
                    name VARCHAR(255) NOT NULL,
                    role VARCHAR(50) DEFAULT 'employee',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )''',
                '''CREATE TABLE IF NOT EXISTS workplaces (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    name VARCHAR(255) NOT NULL,
                    base_rate REAL NOT NULL,
                    weekend_multiplier REAL DEFAULT 1.5,
                    public_holiday_multiplier REAL DEFAULT 2.5,
                    overtime_multiplier REAL DEFAULT 1.5,
                    overtime_threshold REAL DEFAULT 8.0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
                )''',
                '''CREATE TABLE IF NOT EXISTS shifts (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    workplace_id INTEGER,
                    date TEXT NOT NULL,
                    start_time TEXT NOT NULL,
                    end_time TEXT NOT NULL,
                    hours REAL NOT NULL,
                    shift_type TEXT NOT NULL,
                    total_pay REAL NOT NULL,
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
                    FOREIGN KEY (workplace_id) REFERENCES workplaces (id)
                )''',
                '''CREATE TABLE IF NOT EXISTS expenses (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    category VARCHAR(100) NOT NULL,
                    amount REAL NOT NULL,
                    due_date TEXT,
                    is_recurring BOOLEAN DEFAULT TRUE,
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
                )''',
                '''CREATE TABLE IF NOT EXISTS goals (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    name VARCHAR(255) NOT NULL,
                    target_amount REAL NOT NULL,
                    current_amount REAL DEFAULT 0,
                    deadline TEXT,
                    auto_allocate REAL DEFAULT 0,
                    priority INTEGER DEFAULT 1,
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
                )''',
                '''CREATE TABLE IF NOT EXISTS savings (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    goal_id INTEGER,
                    amount REAL NOT NULL,
                    date TEXT NOT NULL,
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
                    FOREIGN KEY (goal_id) REFERENCES goals (id)
                )'''
            ]
        else:
            # SQLite syntax
            sql_statements = [
                '''CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    name TEXT NOT NULL,
                    role TEXT DEFAULT 'employee',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )''',
                '''CREATE TABLE IF NOT EXISTS workplaces (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    name TEXT NOT NULL,
                    base_rate REAL NOT NULL,
                    weekend_multiplier REAL DEFAULT 1.5,
                    public_holiday_multiplier REAL DEFAULT 2.5,
                    overtime_multiplier REAL DEFAULT 1.5,
                    overtime_threshold REAL DEFAULT 8.0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
                )''',
                '''CREATE TABLE IF NOT EXISTS shifts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    workplace_id INTEGER,
                    date TEXT NOT NULL,
                    start_time TEXT NOT NULL,
                    end_time TEXT NOT NULL,
                    hours REAL NOT NULL,
                    shift_type TEXT NOT NULL,
                    total_pay REAL NOT NULL,
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
                    FOREIGN KEY (workplace_id) REFERENCES workplaces (id)
                )''',
                '''CREATE TABLE IF NOT EXISTS expenses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    category TEXT NOT NULL,
                    amount REAL NOT NULL,
                    due_date TEXT,
                    is_recurring BOOLEAN DEFAULT 1,
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
                )''',
                '''CREATE TABLE IF NOT EXISTS goals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    name TEXT NOT NULL,
                    target_amount REAL NOT NULL,
                    current_amount REAL DEFAULT 0,
                    deadline TEXT,
                    auto_allocate REAL DEFAULT 0,
                    priority INTEGER DEFAULT 1,
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
                )''',
                '''CREATE TABLE IF NOT EXISTS savings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    goal_id INTEGER,
                    amount REAL NOT NULL,
                    date TEXT NOT NULL,
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
                    FOREIGN KEY (goal_id) REFERENCES goals (id)
                )'''
            ]
        
        for sql in sql_statements:
            cursor.execute(sql)
        
        conn.commit()
        print("✓ Database tables initialized successfully")
    except Exception as e:
        print(f"Error initializing database: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

# ============ QUERY HELPER ============
class SmartCursor:
    """Wrapper that converts ? to ? for SQLite automatically"""
    def __init__(self, cursor, db_type):
        self.cursor = cursor
        self.db_type = db_type
    
    def execute(self, sql, params=()):
        if self.db_type == 'sqlite':
            sql = sql.replace('?', '?')
        return self.cursor.execute(sql, params)
    
    def fetchone(self):
        return self.cursor.fetchone()
    
    def fetchall(self):
        return self.cursor.fetchall()
    
    def close(self):
        return self.cursor.close()

def execute_query(sql, params=()):
    """Execute query with automatic parameter conversion"""
    conn = get_db()
    cursor = SmartCursor(conn.cursor(), DB_TYPE)
    try:
        cursor.execute(sql, params)
        return cursor, conn
    except Exception as e:
        conn.close()
        raise e
def hash_password(password):
    """Hash password using bcrypt"""
    if not isinstance(password, bytes):
        password = password.encode('utf-8')
    return bcrypt.hashpw(password, bcrypt.gensalt()).decode('utf-8')

def verify_password(password, hashed):
    """Verify password against hash"""
    if not isinstance(password, bytes):
        password = password.encode('utf-8')
    if not isinstance(hashed, bytes):
        hashed = hashed.encode('utf-8')
    return bcrypt.checkpw(password, hashed)

def create_jwt_token(user_id, email, role):
    """Create JWT token"""
    payload = {
        'user_id': user_id,
        'email': email,
        'role': role,
        'exp': datetime.utcnow() + timedelta(seconds=JWT_EXPIRATION)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm='HS256')

def verify_jwt_token(token):
    """Verify JWT token and return payload"""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

def token_required(f):
    """Decorator to require valid JWT token"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            try:
                token = auth_header.split(" ")[1]
            except IndexError:
                return jsonify({'error': 'Invalid token format'}), 401
        
        if not token:
            return jsonify({'error': 'Token is missing'}), 401
        
        payload = verify_jwt_token(token)
        if not payload:
            return jsonify({'error': 'Invalid or expired token'}), 401
        
        request.user_id = payload['user_id']
        request.user_email = payload['email']
        request.user_role = payload['role']
        
        return f(*args, **kwargs)
    
    return decorated

# ============ VALIDATION HELPERS ============
def validate_email(email):
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_password(password):
    """Validate password strength"""
    if len(password) < 6:
        return False, "Password must be at least 6 characters"
    return True, None

def validate_shift_data(data):
    """Validate shift input data"""
    errors = []
    
    if 'date' not in data or not data['date']:
        errors.append("Date is required")
    
    if 'hours' not in data:
        errors.append("Hours is required")
    elif not isinstance(data['hours'], (int, float)):
        errors.append("Hours must be a number")
    elif data['hours'] <= 0 or data['hours'] > 24:
        errors.append("Hours must be between 0 and 24")
    
    if 'total_pay' not in data:
        errors.append("Total pay is required")
    elif not isinstance(data['total_pay'], (int, float)):
        errors.append("Total pay must be a number")
    elif data['total_pay'] < 0:
        errors.append("Total pay cannot be negative")
    
    return errors

def validate_expense_data(data):
    """Validate expense input data"""
    errors = []
    
    if 'category' not in data or not data['category']:
        errors.append("Category is required")
    
    if 'amount' not in data:
        errors.append("Amount is required")
    elif not isinstance(data['amount'], (int, float)):
        errors.append("Amount must be a number")
    elif data['amount'] <= 0:
        errors.append("Amount must be greater than 0")
    
    return errors

def validate_goal_data(data):
    """Validate goal input data"""
    errors = []
    
    if 'name' not in data or not data['name']:
        errors.append("Goal name is required")
    
    if 'target_amount' not in data:
        errors.append("Target amount is required")
    elif not isinstance(data['target_amount'], (int, float)):
        errors.append("Target amount must be a number")
    elif data['target_amount'] <= 0:
        errors.append("Target amount must be greater than 0")
    
    return errors

# ============ AUTHENTICATION ENDPOINTS ============
@app.route('/api/auth/register', methods=['POST'])
def register():
    """Register new user"""
    data = request.get_json()
    
    # Validation
    if not data.get('email') or not validate_email(data['email']):
        return jsonify({'error': 'Invalid email format'}), 400
    
    if not data.get('password'):
        return jsonify({'error': 'Password is required'}), 400
    
    valid, msg = validate_password(data['password'])
    if not valid:
        return jsonify({'error': msg}), 400
    
    if not data.get('name'):
        return jsonify({'error': 'Name is required'}), 400
    
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        # Check if user exists - convert ? to ? for SQLite
        sql = 'SELECT id FROM users WHERE email = ?'.replace('?', '?')
        cursor.execute(sql, (data['email'],))
        if cursor.fetchone():
            return jsonify({'error': 'Email already registered'}), 400
        
        # Create user
        hashed_password = hash_password(data['password'])
        sql = 'INSERT INTO users (email, password_hash, name, role) VALUES (?, ?, ?, ?)'.replace('?', '?')
        cursor.execute(sql, (data['email'], hashed_password, data['name'], 'employee'))
        
        # Get user ID
        if DB_TYPE == 'postgres':
            cursor.execute('SELECT lastval()')
            user_id = cursor.fetchone()[0]
        else:
            user_id = cursor.lastrowid
        
        conn.commit()
        
        # Create token
        token = create_jwt_token(user_id, data['email'], 'employee')
        
        return jsonify({
            'success': True,
            'token': token,
            'user': {'id': user_id, 'email': data['email'], 'name': data['name']}
        }), 201
    
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/api/auth/login', methods=['POST'])
def login():
    """Login user"""
    data = request.get_json()
    
    if not data.get('email') or not data.get('password'):
        return jsonify({'error': 'Email and password required'}), 400
    
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute('SELECT id, email, name, password_hash, role FROM users WHERE email = ?', (data['email'],))
        user = cursor.fetchone()
        
        if not user:
            return jsonify({'error': 'Invalid email or password'}), 401
        
        user_id, email, name, password_hash, role = user
        
        if not verify_password(data['password'], password_hash):
            return jsonify({'error': 'Invalid email or password'}), 401
        
        token = create_jwt_token(user_id, email, role)
        
        return jsonify({
            'success': True,
            'token': token,
            'user': {'id': user_id, 'email': email, 'name': name, 'role': role}
        }), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/api/auth/profile', methods=['GET'])
@token_required
def get_profile():
    """Get current user profile"""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute('SELECT id, email, name, role FROM users WHERE id = ?', (request.user_id,))
        user = cursor.fetchone()
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        user_id, email, name, role = user
        return jsonify({
            'id': user_id,
            'email': email,
            'name': name,
            'role': role
        }), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

# ============ SHIFT ENDPOINTS ============
@app.route('/api/shifts', methods=['GET'])
@token_required
def get_shifts():
    """Get all shifts for current user"""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            SELECT id, workplace_id, date, start_time, end_time, hours, shift_type, total_pay, notes
            FROM shifts WHERE user_id = ? ORDER BY date DESC
        ''', (request.user_id,))
        
        shifts = []
        for row in cursor.fetchall():
            shifts.append({
                'id': row[0],
                'workplace_id': row[1],
                'date': row[2],
                'start_time': row[3],
                'end_time': row[4],
                'hours': row[5],
                'shift_type': row[6],
                'total_pay': row[7],
                'notes': row[8]
            })
        
        return jsonify(shifts), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/api/shifts', methods=['POST'])
@token_required
def create_shift():
    """Create new shift"""
    data = request.get_json()
    
    # Validation
    errors = validate_shift_data(data)
    if errors:
        return jsonify({'errors': errors}), 400
    
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            INSERT INTO shifts (user_id, workplace_id, date, start_time, end_time, hours, shift_type, total_pay, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            request.user_id,
            data.get('workplace_id'),
            data['date'],
            data.get('start_time', ''),
            data.get('end_time', ''),
            data['hours'],
            data.get('shift_type', 'regular'),
            data['total_pay'],
            data.get('notes', '')
        ))
        
        shift_id = cursor.lastrowid
        conn.commit()
        
        return jsonify({'id': shift_id, 'success': True}), 201
    
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/api/shifts/<int:shift_id>', methods=['PUT'])
@token_required
def update_shift(shift_id):
    """Update shift"""
    data = request.get_json()
    
    # Validation
    errors = validate_shift_data(data)
    if errors:
        return jsonify({'errors': errors}), 400
    
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        # Check ownership
        cursor.execute('SELECT user_id FROM shifts WHERE id = ?', (shift_id,))
        result = cursor.fetchone()
        if not result or result[0] != request.user_id:
            return jsonify({'error': 'Unauthorized'}), 403
        
        cursor.execute('''
            UPDATE shifts SET date = ?, hours = ?, total_pay = ?, notes = ?
            WHERE id = ? AND user_id = ?
        ''', (data['date'], data['hours'], data['total_pay'], data.get('notes', ''), shift_id, request.user_id))
        
        conn.commit()
        return jsonify({'success': True}), 200
    
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/api/shifts/<int:shift_id>', methods=['DELETE'])
@token_required
def delete_shift(shift_id):
    """Delete shift"""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        # Check ownership
        cursor.execute('SELECT user_id FROM shifts WHERE id = ?', (shift_id,))
        result = cursor.fetchone()
        if not result or result[0] != request.user_id:
            return jsonify({'error': 'Unauthorized'}), 403
        
        cursor.execute('DELETE FROM shifts WHERE id = ?', (shift_id,))
        conn.commit()
        
        return jsonify({'success': True}), 200
    
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

# ============ EXPENSE ENDPOINTS ============
@app.route('/api/expenses', methods=['GET'])
@token_required
def get_expenses():
    """Get all expenses for current user"""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            SELECT id, category, amount, due_date, is_recurring, notes
            FROM expenses WHERE user_id = ? ORDER BY created_at DESC
        ''', (request.user_id,))
        
        expenses = []
        for row in cursor.fetchall():
            expenses.append({
                'id': row[0],
                'category': row[1],
                'amount': row[2],
                'due_date': row[3],
                'is_recurring': row[4],
                'notes': row[5]
            })
        
        return jsonify(expenses), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/api/expenses', methods=['POST'])
@token_required
def create_expense():
    """Create new expense"""
    data = request.get_json()
    
    # Validation
    errors = validate_expense_data(data)
    if errors:
        return jsonify({'errors': errors}), 400
    
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            INSERT INTO expenses (user_id, category, amount, due_date, is_recurring, notes)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            request.user_id,
            data['category'],
            data['amount'],
            data.get('due_date'),
            data.get('is_recurring', True),
            data.get('notes', '')
        ))
        
        expense_id = cursor.lastrowid
        conn.commit()
        
        return jsonify({'id': expense_id, 'success': True}), 201
    
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/api/expenses/<int:expense_id>', methods=['DELETE'])
@token_required
def delete_expense(expense_id):
    """Delete expense"""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute('SELECT user_id FROM expenses WHERE id = ?', (expense_id,))
        result = cursor.fetchone()
        if not result or result[0] != request.user_id:
            return jsonify({'error': 'Unauthorized'}), 403
        
        cursor.execute('DELETE FROM expenses WHERE id = ?', (expense_id,))
        conn.commit()
        
        return jsonify({'success': True}), 200
    
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

# ============ GOALS ENDPOINTS ============
@app.route('/api/goals', methods=['GET'])
@token_required
def get_goals():
    """Get all goals for current user"""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            SELECT id, name, target_amount, current_amount, deadline, priority, notes
            FROM goals WHERE user_id = ? ORDER BY priority, deadline
        ''', (request.user_id,))
        
        goals = []
        for row in cursor.fetchall():
            goals.append({
                'id': row[0],
                'name': row[1],
                'target_amount': row[2],
                'current_amount': row[3],
                'deadline': row[4],
                'priority': row[5],
                'notes': row[6]
            })
        
        return jsonify(goals), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/api/goals', methods=['POST'])
@token_required
def create_goal():
    """Create new goal"""
    data = request.get_json()
    
    # Validation
    errors = validate_goal_data(data)
    if errors:
        return jsonify({'errors': errors}), 400
    
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            INSERT INTO goals (user_id, name, target_amount, deadline, priority, notes)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            request.user_id,
            data['name'],
            data['target_amount'],
            data.get('deadline'),
            data.get('priority', 1),
            data.get('notes', '')
        ))
        
        goal_id = cursor.lastrowid
        conn.commit()
        
        return jsonify({'id': goal_id, 'success': True}), 201
    
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/api/goals/<int:goal_id>', methods=['DELETE'])
@token_required
def delete_goal(goal_id):
    """Delete goal"""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute('SELECT user_id FROM goals WHERE id = ?', (goal_id,))
        result = cursor.fetchone()
        if not result or result[0] != request.user_id:
            return jsonify({'error': 'Unauthorized'}), 403
        
        cursor.execute('DELETE FROM goals WHERE id = ?', (goal_id,))
        conn.commit()
        
        return jsonify({'success': True}), 200
    
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

# ============ SUMMARY & STATS ENDPOINTS ============
@app.route('/api/summary/fortnight', methods=['GET'])
@token_required
def get_fortnight_summary():
    """Get 2-week summary"""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        # Get shifts from last 14 days
        cursor.execute('''
            SELECT SUM(hours), SUM(total_pay), COUNT(*)
            FROM shifts
            WHERE user_id = ? AND date >= (CURRENT_DATE - INTERVAL '14 days')
        ''', (request.user_id,))
        
        result = cursor.fetchone()
        total_hours = result[0] or 0
        total_earned = result[1] or 0
        shift_count = result[2] or 0
        
        # Get expenses
        cursor.execute('SELECT SUM(amount) FROM expenses WHERE user_id = ?', (request.user_id,))
        total_expenses = cursor.fetchone()[0] or 0
        
        return jsonify({
            'total_hours': total_hours,
            'total_earned': total_earned,
            'total_expenses': total_expenses,
            'shift_count': shift_count,
            'net_income': total_earned - total_expenses
        }), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/api/stats', methods=['GET'])
@token_required
def get_stats():
    """Get overall statistics"""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        # Total earned
        cursor.execute('SELECT COALESCE(SUM(total_pay), 0) FROM shifts WHERE user_id = ?', (request.user_id,))
        total_earned = cursor.fetchone()[0]
        
        # Total hours
        cursor.execute('SELECT COALESCE(SUM(hours), 0) FROM shifts WHERE user_id = ?', (request.user_id,))
        total_hours = cursor.fetchone()[0]
        
        # Active goals
        cursor.execute('SELECT COUNT(*) FROM goals WHERE user_id = ? AND current_amount < target_amount', (request.user_id,))
        active_goals = cursor.fetchone()[0]
        
        # Goals saved
        cursor.execute('SELECT COALESCE(SUM(current_amount), 0) FROM goals WHERE user_id = ?', (request.user_id,))
        goals_saved = cursor.fetchone()[0]
        
        # Expense info
        cursor.execute('SELECT COALESCE(SUM(amount), 0) FROM expenses WHERE user_id = ?', (request.user_id,))
        fortnight_expenses = cursor.fetchone()[0]
        
        return jsonify({
            'total_earned': total_earned,
            'total_hours': total_hours,
            'active_goals': active_goals,
            'goals_saved': goals_saved,
            'fortnight_expenses': fortnight_expenses,
            'this_week': {'earned': 0, 'hours': 0, 'shifts': 0},
            'average_rate': total_earned / max(total_hours, 1) if total_hours > 0 else 0
        }), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

# ============ ERROR HANDLERS ============
@app.route('/api/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({'status': 'ok'}), 200

@app.errorhandler(404)
def not_found(e):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(e):
    return jsonify({'error': 'Internal server error'}), 500

# ============ APP INITIALIZATION ============
if __name__ == '__main__':
    init_db()
    port = int(os.environ.get('PORT', 5001))
    app.run(host='0.0.0.0', port=port, debug=False)
