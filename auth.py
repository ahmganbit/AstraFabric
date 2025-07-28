# AstraFabric Authentication Module
# auth.py - Secure authentication with proper password handling

import os
import jwt
import bcrypt
from datetime import datetime, timedelta
from passlib.hash import argon2
from flask import current_app, request, session
from functools import wraps
import sqlite3
import logging

logger = logging.getLogger(__name__)


class AuthManager:
    """Secure authentication manager with proper password hashing."""
    
    def __init__(self, db_path='astrafabric_secure.db'):
        self.db_path = db_path
        self.init_auth_tables()
    
    def init_auth_tables(self):
        """Initialize authentication tables."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Admin users table with secure password storage
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS admin_users (
                id INTEGER PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                email TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP,
                failed_attempts INTEGER DEFAULT 0,
                locked_until TIMESTAMP,
                is_active BOOLEAN DEFAULT 1
            )
        ''')
        
        # Login attempts table for security monitoring
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS login_attempts (
                id INTEGER PRIMARY KEY,
                username TEXT,
                ip_address TEXT,
                user_agent TEXT,
                success BOOLEAN,
                attempted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # JWT token blacklist for logout functionality
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS token_blacklist (
                id INTEGER PRIMARY KEY,
                jti TEXT UNIQUE NOT NULL,
                expires_at TIMESTAMP NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
        
        # Create default admin user if none exists
        self.create_default_admin()
    
    def create_default_admin(self):
        """Create default admin user with secure password."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Check if admin exists
        cursor.execute('SELECT COUNT(*) FROM admin_users WHERE username = ?', ('admin',))
        if cursor.fetchone()[0] == 0:
            # Create admin with environment-based password or generate secure default
            admin_password = os.environ.get('ADMIN_PASSWORD', 'AstraFabric2024!Secure')
            password_hash = argon2.hash(admin_password)
            
            cursor.execute('''
                INSERT INTO admin_users (username, password_hash, email)
                VALUES (?, ?, ?)
            ''', ('admin', password_hash, 'admin@astrafabric.com'))
            
            logger.info("Default admin user created")
            if not os.environ.get('ADMIN_PASSWORD'):
                logger.warning("Using default admin password - set ADMIN_PASSWORD environment variable")
        
        conn.commit()
        conn.close()
    
    def verify_password(self, username, password):
        """Verify user password with secure timing."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Check if account is locked
        cursor.execute('''
            SELECT password_hash, failed_attempts, locked_until, is_active
            FROM admin_users WHERE username = ?
        ''', (username,))
        
        result = cursor.fetchone()
        conn.close()
        
        if not result:
            # User doesn't exist - still hash to prevent timing attacks
            argon2.hash("dummy_password")
            return False
        
        password_hash, failed_attempts, locked_until, is_active = result
        
        # Check if account is active
        if not is_active:
            return False
        
        # Check if account is locked
        if locked_until and datetime.fromisoformat(locked_until) > datetime.now():
            return False
        
        # Verify password
        if argon2.verify(password, password_hash):
            self.reset_failed_attempts(username)
            self.update_last_login(username)
            return True
        else:
            self.increment_failed_attempts(username)
            return False
    
    def increment_failed_attempts(self, username):
        """Increment failed login attempts and lock account if needed."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE admin_users 
            SET failed_attempts = failed_attempts + 1
            WHERE username = ?
        ''', (username,))
        
        # Lock account after 5 failed attempts for 15 minutes
        cursor.execute('''
            UPDATE admin_users 
            SET locked_until = datetime('now', '+15 minutes')
            WHERE username = ? AND failed_attempts >= 5
        ''', (username,))
        
        conn.commit()
        conn.close()
    
    def reset_failed_attempts(self, username):
        """Reset failed attempts counter."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE admin_users 
            SET failed_attempts = 0, locked_until = NULL
            WHERE username = ?
        ''', (username,))
        
        conn.commit()
        conn.close()
    
    def update_last_login(self, username):
        """Update last login timestamp."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE admin_users 
            SET last_login = CURRENT_TIMESTAMP
            WHERE username = ?
        ''', (username,))
        
        conn.commit()
        conn.close()
    
    def log_login_attempt(self, username, ip_address, user_agent, success):
        """Log login attempt for security monitoring."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO login_attempts (username, ip_address, user_agent, success)
            VALUES (?, ?, ?, ?)
        ''', (username, ip_address, user_agent, success))
        
        conn.commit()
        conn.close()
    
    def generate_jwt_token(self, username):
        """Generate JWT token with proper claims."""
        payload = {
            'username': username,
            'exp': datetime.utcnow() + current_app.config['JWT_ACCESS_TOKEN_EXPIRES'],
            'iat': datetime.utcnow(),
            'jti': os.urandom(16).hex()
        }
        
        return jwt.encode(payload, current_app.config['JWT_SECRET_KEY'], algorithm='HS256')
    
    def verify_jwt_token(self, token):
        """Verify JWT token and check blacklist."""
        try:
            payload = jwt.decode(token, current_app.config['JWT_SECRET_KEY'], algorithms=['HS256'])
            
            # Check if token is blacklisted
            if self.is_token_blacklisted(payload['jti']):
                return None
            
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
    
    def blacklist_token(self, jti, expires_at):
        """Add token to blacklist for logout."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR IGNORE INTO token_blacklist (jti, expires_at)
            VALUES (?, ?)
        ''', (jti, expires_at))
        
        conn.commit()
        conn.close()
    
    def is_token_blacklisted(self, jti):
        """Check if token is blacklisted."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM token_blacklist WHERE jti = ?', (jti,))
        result = cursor.fetchone()[0] > 0
        
        conn.close()
        return result
    
    def cleanup_expired_tokens(self):
        """Clean up expired blacklisted tokens."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM token_blacklist WHERE expires_at < CURRENT_TIMESTAMP')
        
        conn.commit()
        conn.close()


def login_required(f):
    """Decorator for routes requiring authentication."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_logged_in' not in session:
            return {'error': 'Authentication required'}, 401
        return f(*args, **kwargs)
    return decorated_function


def jwt_required(f):
    """Decorator for API routes requiring JWT authentication."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return {'error': 'Token missing'}, 401
        
        try:
            token = token.split(' ')[1]  # Remove 'Bearer ' prefix
            auth_manager = AuthManager()
            payload = auth_manager.verify_jwt_token(token)
            
            if not payload:
                return {'error': 'Invalid token'}, 401
            
            request.current_user = payload['username']
            return f(*args, **kwargs)
        except Exception as e:
            return {'error': 'Token verification failed'}, 401
    
    return decorated_function
