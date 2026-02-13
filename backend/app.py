import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime, timedelta
import sqlite3
import json
from dateutil import parser

app = Flask(__name__)
CORS(app)

import os
DATABASE = os.path.join(os.path.dirname(__file__), 'payroll.db')

# Australian public holidays 2026 (can be updated yearly)
PUBLIC_HOLIDAYS = [
    '2026-01-01', '2026-01-26', '2026-04-03', '2026-04-04', '2026-04-06', '2026-04-25',
    '2026-06-08', '2026-12-25', '2026-12-26', '2026-12-28'
]

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()
    
    # Workplaces table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS workplaces (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            base_rate REAL NOT NULL,
            weekend_multiplier REAL DEFAULT 1.5,
            public_holiday_multiplier REAL DEFAULT 2.5,
            overtime_multiplier REAL DEFAULT 1.5,
            overtime_threshold REAL DEFAULT 8.0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Shifts table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS shifts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            workplace_id INTEGER NOT NULL,
            date TEXT NOT NULL,
            start_time TEXT NOT NULL,
            end_time TEXT NOT NULL,
            hours REAL NOT NULL,
            shift_type TEXT NOT NULL,
            total_pay REAL NOT NULL,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (workplace_id) REFERENCES workplaces (id)
        )
    ''')
    
    # Budget expenses table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT NOT NULL,
            amount REAL NOT NULL,
            due_date TEXT,
            is_recurring INTEGER DEFAULT 1,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Goals table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS goals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            target_amount REAL NOT NULL,
            current_amount REAL DEFAULT 0,
            deadline TEXT,
            auto_allocate REAL DEFAULT 0,
            priority INTEGER DEFAULT 1,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Savings table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS savings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            goal_id INTEGER,
            amount REAL NOT NULL,
            date TEXT NOT NULL,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (goal_id) REFERENCES goals (id)
        )
    ''')
    
    conn.commit()
    conn.close()

def calculate_shift_pay(workplace, date_str, hours):
    """Calculate pay based on shift type and hours"""
    date = datetime.strptime(date_str, '%Y-%m-%d')
    day_of_week = date.weekday()  # 0=Monday, 6=Sunday
    
    base_rate = workplace['base_rate']
    overtime_threshold = workplace['overtime_threshold']
    
    # Determine shift type and multiplier
    if date_str in PUBLIC_HOLIDAYS:
        shift_type = 'public_holiday'
        multiplier = workplace['public_holiday_multiplier']
    elif day_of_week >= 5:  # Saturday or Sunday
        shift_type = 'weekend'
        multiplier = workplace['weekend_multiplier']
    else:
        shift_type = 'weekday'
        multiplier = 1.0
    
    # Calculate regular and overtime pay
    if hours <= overtime_threshold:
        total_pay = hours * base_rate * multiplier
    else:
        regular_hours = overtime_threshold
        overtime_hours = hours - overtime_threshold
        regular_pay = regular_hours * base_rate * multiplier
        overtime_pay = overtime_hours * base_rate * workplace['overtime_multiplier'] * multiplier
        total_pay = regular_pay + overtime_pay
        shift_type += '_overtime'
    
    return shift_type, round(total_pay, 2)

# WORKPLACES ENDPOINTS
@app.route('/api/workplaces', methods=['GET', 'POST'])
def workplaces():
    conn = get_db()
    
    if request.method == 'GET':
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM workplaces ORDER BY name')
        workplaces = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return jsonify(workplaces)
    
    elif request.method == 'POST':
        data = request.json
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO workplaces (name, base_rate, weekend_multiplier, 
                                   public_holiday_multiplier, overtime_multiplier, overtime_threshold)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (data['name'], data['base_rate'], data.get('weekend_multiplier', 1.5),
              data.get('public_holiday_multiplier', 2.5), data.get('overtime_multiplier', 1.5),
              data.get('overtime_threshold', 8.0)))
        conn.commit()
        workplace_id = cursor.lastrowid
        conn.close()
        return jsonify({'id': workplace_id, 'message': 'Workplace created'}), 201

@app.route('/api/workplaces/<int:workplace_id>', methods=['GET', 'PUT', 'DELETE'])
def workplace_detail(workplace_id):
    conn = get_db()
    cursor = conn.cursor()
    
    if request.method == 'GET':
        cursor.execute('SELECT * FROM workplaces WHERE id = ?', (workplace_id,))
        workplace = cursor.fetchone()
        conn.close()
        if workplace:
            return jsonify(dict(workplace))
        return jsonify({'error': 'Workplace not found'}), 404
    
    elif request.method == 'PUT':
        data = request.json
        cursor.execute('''
            UPDATE workplaces 
            SET name=?, base_rate=?, weekend_multiplier=?, 
                public_holiday_multiplier=?, overtime_multiplier=?, overtime_threshold=?
            WHERE id=?
        ''', (data['name'], data['base_rate'], data.get('weekend_multiplier', 1.5),
              data.get('public_holiday_multiplier', 2.5), data.get('overtime_multiplier', 1.5),
              data.get('overtime_threshold', 8.0), workplace_id))
        conn.commit()
        conn.close()
        return jsonify({'message': 'Workplace updated'})
    
    elif request.method == 'DELETE':
        cursor.execute('DELETE FROM workplaces WHERE id = ?', (workplace_id,))
        conn.commit()
        conn.close()
        return jsonify({'message': 'Workplace deleted'})

# SHIFTS ENDPOINTS
@app.route('/api/shifts', methods=['GET', 'POST'])
def shifts():
    conn = get_db()
    
    if request.method == 'GET':
        cursor = conn.cursor()
        cursor.execute('''
            SELECT s.*, w.name as workplace_name 
            FROM shifts s
            JOIN workplaces w ON s.workplace_id = w.id
            ORDER BY s.date DESC, s.start_time DESC
        ''')
        shifts = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return jsonify(shifts)
    
    elif request.method == 'POST':
        data = request.json
        cursor = conn.cursor()
        
        # Get workplace details
        cursor.execute('SELECT * FROM workplaces WHERE id = ?', (data['workplace_id'],))
        workplace = dict(cursor.fetchone())
        
        # Calculate hours and pay
        start = datetime.strptime(data['start_time'], '%H:%M')
        end = datetime.strptime(data['end_time'], '%H:%M')
        hours = (end - start).seconds / 3600
        
        shift_type, total_pay = calculate_shift_pay(workplace, data['date'], hours)
        
        cursor.execute('''
            INSERT INTO shifts (workplace_id, date, start_time, end_time, 
                               hours, shift_type, total_pay, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (data['workplace_id'], data['date'], data['start_time'], 
              data['end_time'], hours, shift_type, total_pay, data.get('notes', '')))
        
        conn.commit()
        shift_id = cursor.lastrowid
        conn.close()
        return jsonify({'id': shift_id, 'total_pay': total_pay, 'shift_type': shift_type}), 201

@app.route('/api/shifts/<int:shift_id>', methods=['GET', 'PUT', 'DELETE'])
def shift_detail(shift_id):
    conn = get_db()
    cursor = conn.cursor()
    
    if request.method == 'GET':
        cursor.execute('''
            SELECT s.*, w.name as workplace_name 
            FROM shifts s
            JOIN workplaces w ON s.workplace_id = w.id
            WHERE s.id = ?
        ''', (shift_id,))
        shift = cursor.fetchone()
        conn.close()
        if shift:
            return jsonify(dict(shift))
        return jsonify({'error': 'Shift not found'}), 404
    
    elif request.method == 'PUT':
        data = request.json
        cursor.execute('SELECT * FROM workplaces WHERE id = ?', (data['workplace_id'],))
        workplace = dict(cursor.fetchone())
        
        start = datetime.strptime(data['start_time'], '%H:%M')
        end = datetime.strptime(data['end_time'], '%H:%M')
        hours = (end - start).seconds / 3600
        
        shift_type, total_pay = calculate_shift_pay(workplace, data['date'], hours)
        
        cursor.execute('''
            UPDATE shifts 
            SET workplace_id=?, date=?, start_time=?, end_time=?, 
                hours=?, shift_type=?, total_pay=?, notes=?
            WHERE id=?
        ''', (data['workplace_id'], data['date'], data['start_time'], 
              data['end_time'], hours, shift_type, total_pay, 
              data.get('notes', ''), shift_id))
        
        conn.commit()
        conn.close()
        return jsonify({'message': 'Shift updated', 'total_pay': total_pay})
    
    elif request.method == 'DELETE':
        cursor.execute('DELETE FROM shifts WHERE id = ?', (shift_id,))
        conn.commit()
        conn.close()
        return jsonify({'message': 'Shift deleted'})

# BUDGET ENDPOINTS
@app.route('/api/expenses', methods=['GET', 'POST'])
def expenses():
    conn = get_db()
    cursor = conn.cursor()
    
    if request.method == 'GET':
        cursor.execute('SELECT * FROM expenses ORDER BY category')
        expenses = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return jsonify(expenses)
    
    elif request.method == 'POST':
        data = request.json
        cursor.execute('''
            INSERT INTO expenses (category, amount, due_date, is_recurring, notes)
            VALUES (?, ?, ?, ?, ?)
        ''', (data['category'], data['amount'], data.get('due_date'), 
              data.get('is_recurring', 1), data.get('notes', '')))
        conn.commit()
        expense_id = cursor.lastrowid
        conn.close()
        return jsonify({'id': expense_id, 'message': 'Expense created'}), 201

@app.route('/api/expenses/<int:expense_id>', methods=['GET', 'PUT', 'DELETE'])
def expense_detail(expense_id):
    conn = get_db()
    cursor = conn.cursor()
    
    if request.method == 'GET':
        cursor.execute('SELECT * FROM expenses WHERE id = ?', (expense_id,))
        expense = cursor.fetchone()
        conn.close()
        if expense:
            return jsonify(dict(expense))
        return jsonify({'error': 'Expense not found'}), 404
    
    elif request.method == 'PUT':
        data = request.json
        cursor.execute('''
            UPDATE expenses 
            SET category=?, amount=?, due_date=?, is_recurring=?, notes=?
            WHERE id=?
        ''', (data['category'], data['amount'], data.get('due_date'),
              data.get('is_recurring', 1), data.get('notes', ''), expense_id))
        conn.commit()
        conn.close()
        return jsonify({'message': 'Expense updated'})
    
    elif request.method == 'DELETE':
        cursor.execute('DELETE FROM expenses WHERE id = ?', (expense_id,))
        conn.commit()
        conn.close()
        return jsonify({'message': 'Expense deleted'})

# ANALYTICS ENDPOINTS
@app.route('/api/summary/fortnight', methods=['GET'])
def fortnight_summary():
    """Get financial summary with all-time totals (updates immediately)"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Get ALL shifts (not just fortnight - so it updates immediately!)
    cursor.execute('''
        SELECT SUM(total_pay) as total_earned, SUM(hours) as total_hours, COUNT(*) as shift_count
        FROM shifts
    ''')
    
    shift_data = dict(cursor.fetchone())
    
    # Get total ALL expenses (not just recurring)
    cursor.execute('SELECT SUM(amount) as total_expenses FROM expenses')
    expenses_data = dict(cursor.fetchone())
    
    # Get total contributed to goals (actual saved money)
    cursor.execute('SELECT SUM(current_amount) as goal_saved FROM goals')
    goals_data = dict(cursor.fetchone())
    
    total_earned = shift_data['total_earned'] or 0
    total_expenses = expenses_data['total_expenses'] or 0
    goal_saved = goals_data['goal_saved'] or 0
    
    # Financial breakdown: Earned - Expenses - Goals = Available
    available_money = total_earned - total_expenses - goal_saved
    
    conn.close()
    
    return jsonify({
        'total_earned': total_earned,
        'total_hours': shift_data['total_hours'] or 0,
        'shift_count': shift_data['shift_count'] or 0,
        'total_expenses': total_expenses,
        'goal_allocations': goal_saved,  # Keep same key name for frontend compatibility
        'net_after_goals': available_money
    })

@app.route('/api/summary/monthly', methods=['GET'])
def monthly_summary():
    """Get monthly breakdown"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT 
            strftime('%Y-%m', date) as month,
            SUM(total_pay) as total_earned,
            SUM(hours) as total_hours,
            COUNT(*) as shift_count
        FROM shifts
        GROUP BY strftime('%Y-%m', date)
        ORDER BY month DESC
        LIMIT 12
    ''')
    
    monthly_data = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return jsonify(monthly_data)

# GOALS ENDPOINTS
@app.route('/api/goals', methods=['GET', 'POST'])
def goals():
    conn = get_db()
    cursor = conn.cursor()
    
    if request.method == 'GET':
        cursor.execute('''
            SELECT g.*, 
                   COALESCE(SUM(s.amount), 0) as saved_amount,
                   g.target_amount - COALESCE(SUM(s.amount), 0) as remaining
            FROM goals g
            LEFT JOIN savings s ON g.id = s.goal_id
            GROUP BY g.id
            ORDER BY g.priority DESC, g.deadline ASC
        ''')
        goals = [dict(row) for row in cursor.fetchall()]
        
        # Calculate progress percentage
        for goal in goals:
            goal['progress'] = (goal['saved_amount'] / goal['target_amount'] * 100) if goal['target_amount'] > 0 else 0
            goal['remaining'] = goal['target_amount'] - goal['saved_amount']
            
        conn.close()
        return jsonify(goals)
    
    elif request.method == 'POST':
        data = request.json
        cursor.execute('''
            INSERT INTO goals (name, target_amount, deadline, auto_allocate, priority, notes)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (data['name'], data['target_amount'], data.get('deadline'),
              data.get('auto_allocate', 0), data.get('priority', 1), data.get('notes', '')))
        conn.commit()
        goal_id = cursor.lastrowid
        conn.close()
        return jsonify({'id': goal_id, 'message': 'Goal created'}), 201

@app.route('/api/goals/<int:goal_id>', methods=['GET', 'PUT', 'DELETE'])
def goal_detail(goal_id):
    conn = get_db()
    cursor = conn.cursor()
    
    if request.method == 'GET':
        cursor.execute('''
            SELECT g.*, 
                   COALESCE(SUM(s.amount), 0) as saved_amount
            FROM goals g
            LEFT JOIN savings s ON g.id = s.goal_id
            WHERE g.id = ?
            GROUP BY g.id
        ''', (goal_id,))
        goal = cursor.fetchone()
        conn.close()
        if goal:
            goal_dict = dict(goal)
            goal_dict['progress'] = (goal_dict['saved_amount'] / goal_dict['target_amount'] * 100) if goal_dict['target_amount'] > 0 else 0
            goal_dict['remaining'] = goal_dict['target_amount'] - goal_dict['saved_amount']
            return jsonify(goal_dict)
        return jsonify({'error': 'Goal not found'}), 404
    
    elif request.method == 'PUT':
        data = request.json
        cursor.execute('''
            UPDATE goals 
            SET name=?, target_amount=?, deadline=?, auto_allocate=?, priority=?, notes=?
            WHERE id=?
        ''', (data['name'], data['target_amount'], data.get('deadline'),
              data.get('auto_allocate', 0), data.get('priority', 1), 
              data.get('notes', ''), goal_id))
        conn.commit()
        conn.close()
        return jsonify({'message': 'Goal updated'})
    
    elif request.method == 'DELETE':
        cursor.execute('DELETE FROM goals WHERE id = ?', (goal_id,))
        cursor.execute('DELETE FROM savings WHERE goal_id = ?', (goal_id,))
        conn.commit()
        conn.close()
        return jsonify({'message': 'Goal deleted'})

@app.route('/api/goals/<int:goal_id>/contribute', methods=['POST'])
def contribute_to_goal(goal_id):
    """Add money to a goal"""
    conn = get_db()
    cursor = conn.cursor()
    data = request.json
    
    cursor.execute('''
        INSERT INTO savings (goal_id, amount, date, notes)
        VALUES (?, ?, ?, ?)
    ''', (goal_id, data['amount'], data.get('date', datetime.now().strftime('%Y-%m-%d')),
          data.get('notes', '')))
    
    conn.commit()
    conn.close()
    return jsonify({'message': 'Contribution added'}), 201

@app.route('/api/expenses/summary', methods=['GET'])
def expense_summary():
    """Get expense breakdown by category"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT category, 
               SUM(amount) as total,
               COUNT(*) as count
        FROM expenses
        GROUP BY category
        ORDER BY total DESC
    ''')
    
    summary = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return jsonify(summary)

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get overall statistics"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Total earnings all time
    cursor.execute('SELECT SUM(total_pay) as total, SUM(hours) as hours FROM shifts')
    earnings = dict(cursor.fetchone())
    
    # Average hourly rate
    avg_rate = (earnings['total'] / earnings['hours']) if earnings['hours'] and earnings['hours'] > 0 else 0
    
    # Total saved towards goals
    cursor.execute('SELECT SUM(amount) as saved FROM savings')
    goals_saved = dict(cursor.fetchone())['saved'] or 0
    
    # Total expenses
    cursor.execute('SELECT SUM(amount) as total FROM expenses WHERE is_recurring = 1')
    monthly_expenses = dict(cursor.fetchone())['total'] or 0
    
    # Number of active goals
    cursor.execute('SELECT COUNT(*) as count FROM goals')
    goal_count = dict(cursor.fetchone())['count']
    
    # This week's shifts
    cursor.execute('''
        SELECT COUNT(*) as count, SUM(hours) as hours, SUM(total_pay) as earned
        FROM shifts
        WHERE date >= date('now', '-7 days')
    ''')
    week_data = dict(cursor.fetchone())
    
    conn.close()
    
    return jsonify({
        'total_earned': earnings['total'] or 0,
        'total_hours': earnings['hours'] or 0,
        'average_rate': avg_rate,
        'goals_saved': goals_saved,
        'fortnight_expenses': monthly_expenses,
        'active_goals': goal_count,
        'this_week': {
            'shifts': week_data['count'] or 0,
            'hours': week_data['hours'] or 0,
            'earned': week_data['earned'] or 0
        }
    })

@app.route('/api/export/shifts', methods=['GET'])
def export_shifts():
    """Export shifts as CSV"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT s.date, w.name as workplace, s.start_time, s.end_time,
               s.hours, s.shift_type, s.total_pay, s.notes
        FROM shifts s
        JOIN workplaces w ON s.workplace_id = w.id
        ORDER BY s.date DESC
    ''')
    
    shifts = cursor.fetchall()
    conn.close()
    
    # Create CSV
    import io
    output = io.StringIO()
    output.write('Date,Workplace,Start Time,End Time,Hours,Type,Pay,Notes\n')
    
    for shift in shifts:
        output.write(f'{shift[0]},{shift[1]},{shift[2]},{shift[3]},{shift[4]},{shift[5]},{shift[6]},"{shift[7] or ""}"\n')
    
    return output.getvalue(), 200, {'Content-Type': 'text/csv', 'Content-Disposition': 'attachment; filename=shifts.csv'}

@app.route('/api/search/shifts', methods=['GET'])
def search_shifts():
    """Search shifts by date range or workplace"""
    conn = get_db()
    cursor = conn.cursor()
    
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    workplace_id = request.args.get('workplace_id')
    
    query = '''
        SELECT s.*, w.name as workplace_name
        FROM shifts s
        JOIN workplaces w ON s.workplace_id = w.id
        WHERE 1=1
    '''
    params = []
    
    if start_date:
        query += ' AND s.date >= ?'
        params.append(start_date)
    
    if end_date:
        query += ' AND s.date <= ?'
        params.append(end_date)
    
    if workplace_id:
        query += ' AND s.workplace_id = ?'
        params.append(workplace_id)
    
    query += ' ORDER BY s.date DESC, s.start_time DESC'
    
    cursor.execute(query, params)
    shifts = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return jsonify(shifts)

# TAX CALCULATOR

if __name__ == '__main__':
    init_db()
    port = int(os.environ.get('PORT', 5001))
    app.run(host='0.0.0.0', port=port)
