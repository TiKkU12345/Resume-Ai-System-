from flask import Blueprint, request, jsonify, session, render_template
from functools import wraps
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
import os
from werkzeug.security import check_password_hash

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

# Database connection function
def get_db_connection():
    conn = psycopg2.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        database=os.getenv('DB_NAME', 'your_database'),
        user=os.getenv('DB_USER', 'your_user'),
        password=os.getenv('DB_PASSWORD', 'your_password')
    )
    return conn

# Admin authentication decorator
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_email' not in session:
            return jsonify({'error': 'Unauthorized access'}), 401
        return f(*args, **kwargs)
    return decorated_function

# Admin Login Route
@admin_bp.route('/login', methods=['POST'])
def admin_login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        # Check if user is admin
        cur.execute("""
            SELECT * FROM users 
            WHERE email = %s AND is_admin = true
        """, (email,))
        
        admin = cur.fetchone()
        
        if admin and check_password_hash(admin['password'], password):
            session['admin_email'] = email
            session['admin_id'] = admin['id']
            return jsonify({
                'success': True,
                'message': 'Login successful',
                'admin': {
                    'email': admin['email'],
                    'name': admin['full_name']
                }
            }), 200
        else:
            return jsonify({'error': 'Invalid credentials'}), 401
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cur.close()
        conn.close()

# Admin Logout Route
@admin_bp.route('/logout', methods=['POST'])
@admin_required
def admin_logout():
    session.clear()
    return jsonify({'success': True, 'message': 'Logged out successfully'}), 200

# Get Pending Users
@admin_bp.route('/pending-users', methods=['GET'])
@admin_required
def get_pending_users():
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        cur.execute("""
            SELECT 
                id,
                full_name,
                email,
                created_at,
                device_id,
                is_approved,
                approved_at,
                approved_by
            FROM users 
            WHERE is_approved = false
            ORDER BY created_at DESC
        """)
        
        pending_users = cur.fetchall()
        
        # Convert datetime to string for JSON serialization
        for user in pending_users:
            user['created_at'] = user['created_at'].isoformat() if user['created_at'] else None
            
        return jsonify({
            'success': True,
            'pending_users': pending_users,
            'count': len(pending_users)
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cur.close()
        conn.close()

# Get All Users (Approved + Pending)
@admin_bp.route('/all-users', methods=['GET'])
@admin_required
def get_all_users():
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        cur.execute("""
            SELECT 
                id,
                full_name,
                email,
                created_at,
                device_id,
                is_approved,
                approved_at,
                approved_by
            FROM users 
            ORDER BY created_at DESC
        """)
        
        all_users = cur.fetchall()
        
        # Convert datetime to string for JSON serialization
        for user in all_users:
            user['created_at'] = user['created_at'].isoformat() if user['created_at'] else None
            user['approved_at'] = user['approved_at'].isoformat() if user['approved_at'] else None
            
        return jsonify({
            'success': True,
            'users': all_users,
            'count': len(all_users)
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cur.close()
        conn.close()

# Approve User
@admin_bp.route('/approve-user/<int:user_id>', methods=['POST'])
@admin_required
def approve_user(user_id):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    admin_email = session.get('admin_email')
    
    try:
        # Get user details first
        cur.execute("SELECT * FROM users WHERE id = %s", (user_id,))
        user = cur.fetchone()
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
            
        if user['is_approved']:
            return jsonify({'error': 'User already approved'}), 400
        
        # Approve user
        cur.execute("""
            UPDATE users 
            SET is_approved = true,
                approved_at = NOW(),
                approved_by = %s,
                approved_devices = ARRAY[%s]
            WHERE id = %s
            RETURNING *
        """, (admin_email, user['device_id'], user_id))
        
        approved_user = cur.fetchone()
        conn.commit()
        
        # TODO: Send approval email to user
        # send_approval_email(user['email'], user['full_name'])
        
        return jsonify({
            'success': True,
            'message': f'User {user["full_name"]} approved successfully',
            'user': {
                'id': approved_user['id'],
                'email': approved_user['email'],
                'name': approved_user['full_name'],
                'approved_at': approved_user['approved_at'].isoformat()
            }
        }), 200
        
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        cur.close()
        conn.close()

# Reject/Delete User
@admin_bp.route('/reject-user/<int:user_id>', methods=['DELETE'])
@admin_required
def reject_user(user_id):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        # Get user details first
        cur.execute("SELECT * FROM users WHERE id = %s", (user_id,))
        user = cur.fetchone()
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Delete user
        cur.execute("DELETE FROM users WHERE id = %s", (user_id,))
        conn.commit()
        
        return jsonify({
            'success': True,
            'message': f'User {user["full_name"]} rejected and deleted'
        }), 200
        
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        cur.close()
        conn.close()

# Admin Dashboard Page
@admin_bp.route('/dashboard')
@admin_required
def dashboard():
    return render_template('admin_dashboard.html')

# Check Admin Session
@admin_bp.route('/check-session', methods=['GET'])
def check_session():
    if 'admin_email' in session:
        return jsonify({
            'authenticated': True,
            'admin_email': session['admin_email']
        }), 200
    return jsonify({'authenticated': False}), 401