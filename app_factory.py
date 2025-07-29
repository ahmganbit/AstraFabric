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
from flask_wtf.csrf import CSRFProtect
from config import config
from models import db


# Initialize extensions
migrate = Migrate()
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"  # Explicitly set to avoid warnings
)
csrf = CSRFProtect()


def create_app(config_name=None):
    """Application factory function."""
    
    # Determine configuration
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'production')  # Default to production for deployment
    
    # Create Flask app
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # Configure structured logging
    configure_logging(app)
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    
    # Only enable CSRF in production with forms
    if not app.config.get('DEBUG'):
        csrf.init_app(app)
    
    # Skip Talisman for now - add manual security headers instead
    # if not app.config.get('DEBUG'):
    #     talisman_config = app.config.get('TALISMAN_CONFIG', {})
    #     if talisman_config:
    #         Talisman(app, **talisman_config)
    
    # Register error handlers
    register_error_handlers(app)
    
    # Register blueprints
    register_blueprints(app)
    
    # Add request/response hooks
    configure_hooks(app)
    
    # Create tables on startup
    with app.app_context():
        try:
            db.create_all()
            app.logger.info('Database tables created successfully')
        except Exception as e:
            app.logger.error(f'Database initialization error: {e}')
    
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
    
    try:
        # Import and register main blueprint
        from routes.main import main_bp
        app.register_blueprint(main_bp)
        app.logger.info('Main blueprint registered successfully')
    except ImportError as e:
        app.logger.error(f'Failed to import main blueprint: {e}')
    
    # Additional blueprints can be added here when they exist
    # try:
    #     from routes.auth import auth_bp
    #     app.register_blueprint(auth_bp, url_prefix='/auth')
    # except ImportError:
    #     app.logger.warning('Auth blueprint not found, skipping')
    
    # try:
    #     from routes.payment import payment_bp
    #     app.register_blueprint(payment_bp, url_prefix='/payment')
    # except ImportError:
    #     app.logger.warning('Payment blueprint not found, skipping')
    
    # try:
    #     from routes.api import api_bp
    #     app.register_blueprint(api_bp, url_prefix='/api/v1')
    # except ImportError:
    #     app.logger.warning('API blueprint not found, skipping')


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
    
    @app.after_request
    def after_request(response):
        """After request hook for manual security headers."""
        
        # Add manual security headers (since we disabled Talisman)
        if not app.config.get('DEBUG'):
            response.headers['X-Content-Type-Options'] = 'nosniff'
            response.headers['X-Frame-Options'] = 'DENY'
            response.headers['X-XSS-Protection'] = '1; mode=block'
            response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
            response.headers['Content-Security-Policy'] = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' cdn.jsdelivr.net; "
                "style-src 'self' 'unsafe-inline' cdn.jsdelivr.net fonts.googleapis.com; "
                "font-src 'self' fonts.gstatic.com; "
                "img-src 'self' data:; "
                "connect-src 'self'"
            )
        
        # Log response details
        app.logger.info('Response sent', extra={
            'status_code': response.status_code,
            'content_length': response.content_length
        })
        
        return response


# Create the application instance for gunicorn
app = create_app()

if __name__ == '__main__':
    # Create app for development
    dev_app = create_app('development')
    dev_app.run(debug=True, host='0.0.0.0', port=10000)