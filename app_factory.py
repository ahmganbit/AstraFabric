# AstraFabric Application Factory
# app_factory.py - Secure Flask application factory with proper structure

import os
import logging
import structlog
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_talisman import Talisman
from flask_wtf.csrf import CSRFProtect
from config import config
from models import db


# Initialize extensions
migrate = Migrate()
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)
csrf = CSRFProtect()


def create_app(config_name=None):
    """Application factory function."""
    
    # Determine configuration
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'default')
    
    # Create Flask app
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # Configure structured logging
    configure_logging(app)
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    limiter.init_app(app)
    csrf.init_app(app)
    
    # Configure security headers (only in production)
    if not app.config.get('DEBUG'):
        talisman_config = app.config.get('TALISMAN_CONFIG', {})
        if talisman_config:
            Talisman(app, **talisman_config)
    
    # Register error handlers
    register_error_handlers(app)
    
    # Register blueprints (when we create them)
    register_blueprints(app)
    
    # Add request/response hooks
    configure_hooks(app)
    
    return app


def configure_logging(app):
    """Configure structured logging."""
    
    if app.config.get('DEBUG'):
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)
    
    # Configure structlog for better log formatting
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )


def register_error_handlers(app):
    """Register error handlers."""
    
    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({
            'error': 'Bad Request',
            'message': 'The request could not be understood by the server'
        }), 400
    
    @app.errorhandler(401)
    def unauthorized(error):
        return jsonify({
            'error': 'Unauthorized',
            'message': 'Authentication is required'
        }), 401
    
    @app.errorhandler(403)
    def forbidden(error):
        return jsonify({
            'error': 'Forbidden',
            'message': 'You do not have permission to access this resource'
        }), 403
    
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            'error': 'Not Found',
            'message': 'The requested resource was not found'
        }), 404
    
    @app.errorhandler(429)
    def rate_limit_exceeded(error):
        return jsonify({
            'error': 'Rate Limit Exceeded',
            'message': 'Too many requests. Please try again later.'
        }), 429
    
    @app.errorhandler(500)
    def internal_error(error):
        app.logger.error(f'Internal server error: {error}')
        return jsonify({
            'error': 'Internal Server Error',
            'message': 'An unexpected error occurred'
        }), 500


def register_blueprints(app):
    """Register application blueprints."""
    
    # Import blueprints here to avoid circular imports
    from routes.main import main_bp
    
    # Register blueprints
    app.register_blueprint(main_bp)
    
    # Note: Other blueprints (auth, payment, api) will be added when they exist
    # from routes.auth import auth_bp
    # from routes.payment import payment_bp
    # from routes.api import api_bp
    # app.register_blueprint(auth_bp, url_prefix='/auth')
    # app.register_blueprint(payment_bp, url_prefix='/payment')
    # app.register_blueprint(api_bp, url_prefix='/api/v1')


def configure_hooks(app):
    """Configure request/response hooks."""
    
    @app.before_request
    def before_request():
        """Before request hook for security and logging."""
        
        # Log request details (excluding sensitive data)
        app.logger.info('Request received', extra={
            'method': request.method,
            'path': request.path,
            'ip_address': request.remote_addr,
            'user_agent': request.headers.get('User-Agent', '')[:200]  # Truncate long user agents
        })
        
        # Security headers for all responses
        if not app.config.get('DEBUG'):
            # Force HTTPS in production
            if not request.is_secure and request.headers.get('X-Forwarded-Proto') != 'https':
                return jsonify({'error': 'HTTPS required'}), 400
    
    @app.after_request
    def after_request(response):
        """After request hook for security headers."""
        
        # Add security headers if not already set
        if not app.config.get('DEBUG'):
            response.headers.setdefault('X-Content-Type-Options', 'nosniff')
            response.headers.setdefault('X-Frame-Options', 'DENY')
            response.headers.setdefault('X-XSS-Protection', '1; mode=block')
        
        # Log response details
        app.logger.info('Response sent', extra={
            'status_code': response.status_code,
            'content_length': response.content_length
        })
        
        return response


def create_tables(app):
    """Create database tables."""
    with app.app_context():
        db.create_all()
        app.logger.info('Database tables created')


def init_sample_data(app):
    """Initialize sample security monitoring data."""
    with app.app_context():
        from models import Customer, SecurityEvent, VulnerabilityScan
        
        # Check if data already exists
        if Customer.query.first():
            return
        
        # Create sample customer
        customer = Customer(
            email='demo@astrafabric.com',
            name='Demo Customer',
            company='AstraFabric Demo',
            phone='+1234567890'
        )
        db.session.add(customer)
        db.session.commit()
        
        # Create sample security events
        events = [
            {
                'event_type': 'malware_detected',
                'severity': 'high',
                'description': 'Malware detected on endpoint workstation-001',
                'source_ip': '192.168.1.100',
                'target_system': 'workstation-001'
            },
            {
                'event_type': 'failed_login',
                'severity': 'medium',
                'description': 'Multiple failed login attempts detected',
                'source_ip': '203.0.113.42',
                'target_system': 'web-server-01'
            },
            {
                'event_type': 'suspicious_network_traffic',
                'severity': 'low',
                'description': 'Unusual outbound network traffic pattern',
                'source_ip': '192.168.1.50',
                'target_system': 'firewall'
            }
        ]
        
        for event_data in events:
            event = SecurityEvent(
                customer_id=customer.id,
                **event_data
            )
            db.session.add(event)
        
        # Create sample vulnerability scan
        scan = VulnerabilityScan(
            customer_id=customer.id,
            scan_type='network',
            target='192.168.1.0/24',
            status='completed',
            vulnerabilities_found=5,
            critical_count=1,
            high_count=2,
            medium_count=2,
            low_count=0
        )
        db.session.add(scan)
        
        db.session.commit()
        app.logger.info('Sample security data initialized')


if __name__ == '__main__':
    # Create app for development
    app = create_app('development')
    
    with app.app_context():
        create_tables(app)
        init_sample_data(app)
    
    app.run(debug=True, host='0.0.0.0', port=10000)