# AstraFabric Configuration Management
# config.py - Secure configuration handling

import os
from datetime import timedelta


class Config:
    """Base configuration class with security best practices."""
    
    # Security Configuration
    SECRET_KEY = os.environ.get('SECRET_KEY')
    if not SECRET_KEY:
        raise ValueError("SECRET_KEY environment variable is required")
    
    # Session Configuration
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = timedelta(hours=2)
    
    # Database Configuration
    DATABASE_URL = os.environ.get('DATABASE_URL')
    if not DATABASE_URL:
        # Fallback to SQLite for development/free tier
        DATABASE_URL = 'sqlite:///astrafabric_secure.db'
    
    # Set SQLALCHEMY_DATABASE_URI for Flask-SQLAlchemy
    SQLALCHEMY_DATABASE_URI = DATABASE_URL
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Payment Gateway Configuration
    NOWPAYMENTS_API_KEY = os.environ.get('NOWPAYMENTS_API_KEY')
    NOWPAYMENTS_HMAC_KEY = os.environ.get('NOWPAYMENTS_HMAC_KEY')  # Optional - can be added later
    FLW_PUBLIC_KEY = os.environ.get('FLW_PUBLIC_KEY')
    FLW_SECRET_KEY = os.environ.get('FLW_SECRET_KEY')
    FLW_SECRET_HASH = os.environ.get('FLW_SECRET_HASH')
    
    # Application Configuration
    BASE_URL = os.environ.get('BASE_URL', 'http://localhost:10000')
    ASTRAFABRIC_ENV = os.environ.get('ASTRAFABRIC_ENV', 'development')
    
    # Rate Limiting
    RATELIMIT_STORAGE_URL = os.environ.get('REDIS_URL', 'memory://')
    
    # JWT Configuration
    JWT_SECRET_KEY = SECRET_KEY
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=15)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)
    
    # Talisman Security Configuration (using correct parameter names)
    TALISMAN_CONFIG = {
        'strict_transport_security': True,
        'strict_transport_security_max_age': 31536000,
        'strict_transport_security_include_subdomains': True,
        'content_type_options': True,
        'frame_options': 'DENY',
        'content_security_policy': {
            'default-src': "'self'",
            'script-src': "'self' 'unsafe-inline' cdn.jsdelivr.net",
            'style-src': "'self' 'unsafe-inline' cdn.jsdelivr.net fonts.googleapis.com",
            'font-src': "'self' fonts.gstatic.com",
            'img-src': "'self' data:",
            'connect-src': "'self'"
        }
    }


class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    SESSION_COOKIE_SECURE = False  # Allow HTTP in development
    TALISMAN_CONFIG = {}  # Disable strict headers in development


class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    
    # Require all payment keys in production
    required_keys = [
        'NOWPAYMENTS_API_KEY', 'NOWPAYMENTS_HMAC_KEY',
        'FLW_SECRET_KEY', 'FLW_SECRET_HASH'
    ]
    
    for key in required_keys:
        if not os.environ.get(key):
            raise ValueError(f"{key} environment variable is required in production")


class TestingConfig(Config):
    """Testing configuration."""
    TESTING = True
    DATABASE_URL = 'sqlite:///:memory:'
    SQLALCHEMY_DATABASE_URI = DATABASE_URL
    SESSION_COOKIE_SECURE = False
    WTF_CSRF_ENABLED = False  # Disable CSRF for testing
    TALISMAN_CONFIG = {}  # Disable strict headers in testing


# Configuration mapping
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}