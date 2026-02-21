import os
import jwt
import bcrypt
from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime, timedelta, timezone
from functools import wraps
import re

app = Flask(__name__)
CORS(app)

# Configuration - Support both SQLite (local) and PostgreSQL (production)
DATABASE_URL = os.environ.get('DATABASE_URL', '')
JWT_SECRET = os.environ.get('JWT_SECRET', 'payroll-system-secret-key-with-sufficient-length-32-bytes')
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
    success = False
    
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
                    budget_limit REAL DEFAULT 5000.0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )''',
                '''CREATE TABLE IF NOT EXISTS workplaces (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    name VARCHAR(255) NOT NULL,
                    base_rate REAL NOT NULL,
                    saturday_multiplier REAL DEFAULT 1.5,
                    sunday_multiplier REAL DEFAULT 2.0,
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
                    is_recurring BOOLEAN DEFAULT FALSE,
                    recurrence_type VARCHAR(50),
                    recurrence_end_date TEXT,
                    next_occurrence TEXT,
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
                )''',
                '''CREATE TABLE IF NOT EXISTS categories (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    name VARCHAR(100) NOT NULL,
                    type VARCHAR(20) NOT NULL,
                    icon VARCHAR(10),
                    color VARCHAR(7),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
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
                    budget_limit REAL DEFAULT 5000.0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )''',
                '''CREATE TABLE IF NOT EXISTS workplaces (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    name TEXT NOT NULL,
                    base_rate REAL NOT NULL,
                    saturday_multiplier REAL DEFAULT 1.5,
                    sunday_multiplier REAL DEFAULT 2.0,
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
                    is_recurring BOOLEAN DEFAULT 0,
                    recurrence_type TEXT,
                    recurrence_end_date TEXT,
                    next_occurrence TEXT,
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
                )''',
                '''CREATE TABLE IF NOT EXISTS categories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    name TEXT NOT NULL,
                    type TEXT NOT NULL,
                    icon TEXT,
                    color TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
                )'''
            ]
        
        for sql in sql_statements:
            cursor.execute(sql)
        
        # Schema migrations - add columns if they don't exist
        try:
            if DB_TYPE == 'postgres':
                cursor.execute("ALTER TABLE users ADD COLUMN budget_limit REAL DEFAULT 5000.0")
            else:
                cursor.execute("ALTER TABLE users ADD COLUMN budget_limit REAL DEFAULT 5000.0")
        except:
            # Column already exists, skip
            pass
        
        # Add recurring expense columns to expenses table
        try:
            if DB_TYPE == 'postgres':
                cursor.execute("ALTER TABLE expenses ADD COLUMN recurrence_type VARCHAR(50)")
                cursor.execute("ALTER TABLE expenses ADD COLUMN recurrence_end_date TEXT")
                cursor.execute("ALTER TABLE expenses ADD COLUMN next_occurrence TEXT")
            else:
                cursor.execute("ALTER TABLE expenses ADD COLUMN recurrence_type TEXT")
                cursor.execute("ALTER TABLE expenses ADD COLUMN recurrence_end_date TEXT")
                cursor.execute("ALTER TABLE expenses ADD COLUMN next_occurrence TEXT")
        except:
            # Columns already exist, skip
            pass
        
        conn.commit()
        print("✓ Database tables initialized successfully")
        success = True
    except Exception as e:
        print(f"Error initializing database: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()
    return success

# Initialize database lazily on first request to avoid import-time issues.
_db_initialized = False

@app.before_request
def ensure_db_initialized():
    global _db_initialized
    if _db_initialized:
        return

    exists = False
    conn = None
    cursor = None
    try:
        conn = get_db()
        cursor = conn.cursor()
        if DB_TYPE == 'postgres':
            cursor.execute("SELECT to_regclass('public.users')")
            exists = cursor.fetchone()[0] is not None
        else:
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
            exists = cursor.fetchone() is not None
    except Exception as e:
        print(f"Database preflight error: {e}")
        exists = False
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

    if not exists:
        if not init_db():
            return jsonify({'error': 'Database initialization failed'}), 500

    _db_initialized = True

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
        'exp': datetime.now(timezone.utc) + timedelta(seconds=JWT_EXPIRATION)
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

def calculate_shift_pay(base_rate, hours, date_str, workplace_data=None):
    """Calculate shift pay based on day of week and rates"""
    from datetime import datetime
    
    try:
        # Parse date
        shift_date = datetime.strptime(date_str, '%Y-%m-%d')
        day_of_week = shift_date.weekday()  # 0=Monday, 5=Saturday, 6=Sunday
        
        # Default multipliers if not provided
        saturday_mult = workplace_data.get('saturday_multiplier', 1.5) if workplace_data else 1.5
        sunday_mult = workplace_data.get('sunday_multiplier', 2.0) if workplace_data else 2.0
        
        # Apply multiplier based on day
        if day_of_week == 5:  # Saturday
            rate = base_rate * saturday_mult
        elif day_of_week == 6:  # Sunday
            rate = base_rate * sunday_mult
        else:  # Weekday
            rate = base_rate
        
        return rate * hours
    except:
        # Fallback to simple calculation
        return base_rate * hours

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

# ============ WORKPLACE ENDPOINTS ============
@app.route('/api/workplaces', methods=['GET'])
@token_required
def get_workplaces():
    """Get all workplaces for current user"""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            SELECT id, name, base_rate, saturday_multiplier, sunday_multiplier, 
                   public_holiday_multiplier, overtime_multiplier, overtime_threshold
            FROM workplaces WHERE user_id = ? ORDER BY name ASC
        ''', (request.user_id,))
        
        workplaces = []
        for row in cursor.fetchall():
            workplaces.append({
                'id': row[0],
                'name': row[1],
                'base_rate': row[2],
                'saturday_multiplier': row[3],
                'sunday_multiplier': row[4],
                'public_holiday_multiplier': row[5],
                'overtime_multiplier': row[6],
                'overtime_threshold': row[7]
            })
        
        return jsonify(workplaces), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/api/workplaces', methods=['POST'])
@token_required
def create_workplace():
    """Create new workplace"""
    data = request.get_json()
    
    # Validation
    if not data.get('name') or not data.get('base_rate'):
        return jsonify({'error': 'Name and base_rate are required'}), 400
    
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            INSERT INTO workplaces 
            (user_id, name, base_rate, saturday_multiplier, sunday_multiplier, 
             public_holiday_multiplier, overtime_multiplier, overtime_threshold)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            request.user_id,
            data['name'],
            data['base_rate'],
            data.get('saturday_multiplier', 1.5),
            data.get('sunday_multiplier', 2.0),
            data.get('public_holiday_multiplier', 2.5),
            data.get('overtime_multiplier', 1.5),
            data.get('overtime_threshold', 8.0)
        ))
        
        workplace_id = cursor.lastrowid
        conn.commit()
        
        return jsonify({'id': workplace_id, 'success': True}), 201
    
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/api/workplaces/<int:workplace_id>', methods=['PUT'])
@token_required
def update_workplace(workplace_id):
    """Update workplace"""
    data = request.get_json()
    
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        # Check ownership
        cursor.execute('SELECT user_id FROM workplaces WHERE id = ?', (workplace_id,))
        result = cursor.fetchone()
        if not result or result[0] != request.user_id:
            return jsonify({'error': 'Unauthorized'}), 403
        
        cursor.execute('''
            UPDATE workplaces SET 
                name = ?, base_rate = ?, saturday_multiplier = ?, sunday_multiplier = ?,
                public_holiday_multiplier = ?, overtime_multiplier = ?, overtime_threshold = ?
            WHERE id = ? AND user_id = ?
        ''', (
            data.get('name'),
            data.get('base_rate'),
            data.get('saturday_multiplier'),
            data.get('sunday_multiplier'),
            data.get('public_holiday_multiplier'),
            data.get('overtime_multiplier'),
            data.get('overtime_threshold'),
            workplace_id,
            request.user_id
        ))
        
        conn.commit()
        return jsonify({'success': True}), 200
    
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/api/workplaces/<int:workplace_id>', methods=['DELETE'])
@token_required
def delete_workplace(workplace_id):
    """Delete workplace"""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        # Check ownership
        cursor.execute('SELECT user_id FROM workplaces WHERE id = ?', (workplace_id,))
        result = cursor.fetchone()
        if not result or result[0] != request.user_id:
            return jsonify({'error': 'Unauthorized'}), 403
        
        cursor.execute('DELETE FROM workplaces WHERE id = ?', (workplace_id,))
        conn.commit()
        
        return jsonify({'success': True}), 200
    
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

# ============ SHIFT ENDPOINTS ============
@app.route('/api/shifts', methods=['GET'])
@token_required
def get_shifts():
    """Get all shifts for current user with workplace details"""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            SELECT s.id, s.workplace_id, w.name, s.date, s.start_time, s.end_time, 
                   s.hours, s.shift_type, s.total_pay, s.notes
            FROM shifts s
            LEFT JOIN workplaces w ON s.workplace_id = w.id
            WHERE s.user_id = ? ORDER BY s.date DESC
        ''', (request.user_id,))
        
        shifts = []
        for row in cursor.fetchall():
            shifts.append({
                'id': row[0],
                'workplace_id': row[1],
                'workplace_name': row[2],
                'date': row[3],
                'start_time': row[4],
                'end_time': row[5],
                'hours': row[6],
                'shift_type': row[7],
                'total_pay': row[8],
                'notes': row[9]
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
    """Create new shift - calculates pay based on day of week and workplace rates"""
    data = request.get_json()
    
    # Validation
    errors = validate_shift_data(data)
    if errors:
        return jsonify({'errors': errors}), 400
    
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        # Calculate pay based on day of week if workplace_id is provided
        total_pay = data.get('total_pay')
        if data.get('workplace_id'):
            cursor.execute('''
                SELECT base_rate, saturday_multiplier, sunday_multiplier 
                FROM workplaces WHERE id = ? AND user_id = ?
            ''', (data.get('workplace_id'), request.user_id))
            workplace = cursor.fetchone()
            
            if workplace:
                workplace_data = {
                    'base_rate': workplace[0],
                    'saturday_multiplier': workplace[1],
                    'sunday_multiplier': workplace[2]
                }
                total_pay = calculate_shift_pay(workplace[0], data['hours'], data['date'], workplace_data)
        
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
            total_pay,
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
        # Calculate next occurrence date for recurring expenses
        next_occurrence = None
        if data.get('is_recurring'):
            from dateutil.relativedelta import relativedelta
            try:
                base_date = datetime.strptime(data.get('due_date', datetime.now().strftime('%Y-%m-%d')), '%Y-%m-%d')
                recurrence_type = data.get('recurrence_type', 'monthly')
                
                if recurrence_type == 'weekly':
                    next_occurrence = (base_date + timedelta(weeks=1)).strftime('%Y-%m-%d')
                elif recurrence_type == 'monthly':
                    next_occurrence = (base_date + relativedelta(months=1)).strftime('%Y-%m-%d')
                elif recurrence_type == 'yearly':
                    next_occurrence = (base_date + relativedelta(years=1)).strftime('%Y-%m-%d')
            except:
                next_occurrence = None
        
        cursor.execute('''
            INSERT INTO expenses (user_id, category, amount, due_date, is_recurring, 
                                 recurrence_type, recurrence_end_date, next_occurrence, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            request.user_id,
            data['category'],
            data['amount'],
            data.get('due_date'),
            data.get('is_recurring', False),
            data.get('recurrence_type'),
            data.get('recurrence_end_date'),
            next_occurrence,
            data.get('notes', '')
        ))
        
        expense_id = cursor.lastrowid
        conn.commit()
        
        return jsonify({'id': expense_id, 'success': True, 'next_occurrence': next_occurrence}), 201
    
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

# ============ MILESTONES TRACKING ============
@app.route('/api/goals/milestones', methods=['GET'])
@token_required
def get_milestones():
    """Get goals with milestone tracking analytics"""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            SELECT id, name, target_amount, current_amount, deadline, priority, notes
            FROM goals WHERE user_id = ? ORDER BY priority, deadline
        ''', (request.user_id,))
        
        milestones = []
        for row in cursor.fetchall():
            goal_id, name, target, current, deadline, priority, notes = row
            
            progress_percentage = (current / target * 100) if target > 0 else 0
            remaining = target - current
            
            # Determine status milestones
            status = 'not_started'
            if progress_percentage >= 100:
                status = 'completed'
            elif progress_percentage >= 75:
                status = 'almost_there'
            elif progress_percentage >= 50:
                status = 'halfway'
            elif progress_percentage >= 25:
                status = 'in_progress'
            elif progress_percentage > 0:
                status = 'just_started'
            
            milestones.append({
                'id': goal_id,
                'name': name,
                'target_amount': target,
                'current_amount': current,
                'remaining': remaining,
                'progress_percentage': round(progress_percentage, 2),
                'deadline': deadline,
                'priority': priority,
                'status': status,
                'notes': notes
            })
        
        return jsonify(milestones), 200
    
    except Exception as e:
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


# ============ BUDGET ENDPOINTS ============
@app.route('/api/budget', methods=['GET'])
@token_required
def get_budget():
    """Get budget limit and current spending"""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        # Get user's budget limit
        cursor.execute('SELECT budget_limit FROM users WHERE id = ?', (request.user_id,))
        result = cursor.fetchone()
        budget_limit = result[0] if result else 5000.0
        
        # Get total expenses
        cursor.execute('SELECT COALESCE(SUM(amount), 0) FROM expenses WHERE user_id = ?', (request.user_id,))
        total_spent = cursor.fetchone()[0]
        
        # Calculate remaining and percentage
        remaining = budget_limit - total_spent
        percentage_used = (total_spent / budget_limit * 100) if budget_limit > 0 else 0
        
        return jsonify({
            'budget_limit': budget_limit,
            'total_spent': total_spent,
            'remaining': remaining,
            'percentage_used': round(percentage_used, 2),
            'warning': total_spent > budget_limit * 0.8,  # Alert if >80% spent
            'exceeded': total_spent > budget_limit
        }), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/api/budget', methods=['POST'])
@token_required
def set_budget():
    """Set user's budget limit"""
    data = request.get_json()
    budget_limit = data.get('budget_limit')
    
    # Validate
    if budget_limit is None:
        return jsonify({'error': 'budget_limit is required'}), 400
    
    try:
        budget_limit = float(budget_limit)
        if budget_limit < 0:
            return jsonify({'error': 'budget_limit must be non-negative'}), 400
    except (TypeError, ValueError):
        return jsonify({'error': 'budget_limit must be a valid number'}), 400
    
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute('UPDATE users SET budget_limit = ? WHERE id = ?', (budget_limit, request.user_id))
        conn.commit()
        
        return jsonify({
            'success': True,
            'budget_limit': budget_limit,
            'message': f'Budget limit set to ${budget_limit:.2f}'
        }), 200
    
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

# ============ CATEGORY ENDPOINTS ============
@app.route('/api/categories', methods=['GET'])
@token_required
def get_categories():
    """Get all categories for user"""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            SELECT id, name, type, icon, color
            FROM categories
            WHERE user_id = ?
            ORDER BY name
        ''', (request.user_id,))
        
        categories = []
        for row in cursor.fetchall():
            categories.append({
                'id': row[0],
                'name': row[1],
                'type': row[2],
                'icon': row[3],
                'color': row[4]
            })
        
        return jsonify(categories), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/api/categories', methods=['POST'])
@token_required
def create_category():
    """Create custom category"""
    data = request.get_json()
    
    # Validation
    if not data.get('name'):
        return jsonify({'error': 'Category name is required'}), 400
    if not data.get('type') or data.get('type') not in ['expense', 'income']:
        return jsonify({'error': 'Type must be "expense" or "income"'}), 400
    
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            INSERT INTO categories (user_id, name, type, icon, color)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            request.user_id,
            data['name'],
            data['type'],
            data.get('icon', '📁'),
            data.get('color', '#3b82f6')
        ))
        
        category_id = cursor.lastrowid
        conn.commit()
        
        return jsonify({'id': category_id, 'success': True}), 201
    
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/api/categories/<int:category_id>', methods=['DELETE'])
@token_required
def delete_category(category_id):
    """Delete category"""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        # Verify ownership
        cursor.execute('SELECT user_id FROM categories WHERE id = ?', (category_id,))
        result = cursor.fetchone()
        if not result or result[0] != request.user_id:
            return jsonify({'error': 'Unauthorized'}), 403
        
        cursor.execute('DELETE FROM categories WHERE id = ?', (category_id,))
        conn.commit()
        
        return jsonify({'success': True}), 200
    
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/api/expenses/process-recurring', methods=['POST'])
@token_required
def process_recurring_expenses():
    """Process recurring expenses - create new instances if due"""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        from dateutil.relativedelta import relativedelta
        today = datetime.now().strftime('%Y-%m-%d')
        created_count = 0
        
        # Get all recurring expenses where next_occurrence is today or before
        cursor.execute('''
            SELECT id, category, amount, recurrence_type, next_occurrence, recurrence_end_date, notes
            FROM expenses
            WHERE user_id = ? AND is_recurring = ? AND next_occurrence <= ?
        ''', (request.user_id, True, today))
        
        due_expenses = cursor.fetchall()
        
        for expense in due_expenses:
            expense_id, category, amount, recurrence_type, next_occurrence, recurrence_end_date, notes = expense
            
            # Skip if past end date
            if recurrence_end_date and next_occurrence > recurrence_end_date:
                continue
            
            # Create new expense for this occurrence
            cursor.execute('''
                INSERT INTO expenses (user_id, category, amount, due_date, is_recurring, notes)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (request.user_id, category, amount, next_occurrence, False, f'Auto-generated from recurring expense'))
            created_count += 1
            
            # Calculate next occurrence
            current_date = datetime.strptime(next_occurrence, '%Y-%m-%d')
            new_next_occurrence = None
            
            if recurrence_type == 'weekly':
                new_next_occurrence = (current_date + timedelta(weeks=1)).strftime('%Y-%m-%d')
            elif recurrence_type == 'monthly':
                new_next_occurrence = (current_date + relativedelta(months=1)).strftime('%Y-%m-%d')
            elif recurrence_type == 'yearly':
                new_next_occurrence = (current_date + relativedelta(years=1)).strftime('%Y-%m-%d')
            
            # Update the recurring expense with new next_occurrence
            if new_next_occurrence:
                cursor.execute('''
                    UPDATE expenses SET next_occurrence = ? WHERE id = ?
                ''', (new_next_occurrence, expense_id))
        
        conn.commit()
        
        return jsonify({
            'success': True,
            'created_count': created_count,
            'message': f'Processed {created_count} recurring expense(s)'
        }), 200
    
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

# ============ TAX CALCULATOR ENDPOINT ============
@app.route('/api/tax/calculate', methods=['POST'])
@token_required
def calculate_tax():
    """Calculate tax based on income (simplified Australian tax rates)"""
    data = request.get_json()
    
    annual_income = data.get('annual_income')
    if annual_income is None:
        return jsonify({'error': 'annual_income is required'}), 400
    
    try:
        annual_income = float(annual_income)
        if annual_income < 0:
            return jsonify({'error': 'annual_income must be non-negative'}), 400
    except (TypeError, ValueError):
        return jsonify({'error': 'annual_income must be a valid number'}), 400
    
    # Simplified Australian Tax Brackets (2026) - example rates
    tax = 0
    
    if annual_income <= 18200:
        tax = 0
    elif annual_income <= 45000:
        tax = (annual_income - 18200) * 0.19
    elif annual_income <= 120000:
        tax = 5092 + (annual_income - 45000) * 0.325
    elif annual_income <= 180000:
        tax = 29467 + (annual_income - 120000) * 0.37
    else:
        tax = 51667 + (annual_income - 180000) * 0.45
    
    # Medicare Levy (2%)
    medicare_levy = annual_income * 0.02 if annual_income > 23226 else 0
    
    total_tax = tax + medicare_levy
    net_income = annual_income - total_tax
    effective_tax_rate = (total_tax / annual_income * 100) if annual_income > 0 else 0
    
    return jsonify({
        'annual_income': annual_income,
        'income_tax': round(tax, 2),
        'medicare_levy': round(medicare_levy, 2),
        'total_tax': round(total_tax, 2),
        'net_income': round(net_income, 2),
        'effective_tax_rate': round(effective_tax_rate, 2),
        'monthly_net': round(net_income / 12, 2),
        'fortnightly_net': round(net_income / 26, 2)
    }), 200

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
        
        # Budget info
        cursor.execute('SELECT budget_limit FROM users WHERE id = ?', (request.user_id,))
        budget_result = cursor.fetchone()
        budget_limit = budget_result[0] if budget_result else 5000.0
        budget_remaining = budget_limit - fortnight_expenses
        
        return jsonify({
            'total_earned': total_earned,
            'total_hours': total_hours,
            'active_goals': active_goals,
            'goals_saved': goals_saved,
            'fortnight_expenses': fortnight_expenses,
            'budget_limit': budget_limit,
            'budget_remaining': budget_remaining,
            'budget_exceeded': fortnight_expenses > budget_limit,
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
    port = int(os.environ.get('PORT', 5001))
    app.run(host='0.0.0.0', port=port, debug=False)
