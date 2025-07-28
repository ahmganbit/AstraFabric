# AstraFabric Platform - Agent Development Guide

## Build/Test/Run Commands
- **Local Development**: `python app_factory.py` (runs on port 10000)
- **Production Server**: `gunicorn --config gunicorn.conf.py app_factory:create_app()`
- **Install Dependencies**: `pip install -r requirements.txt`
- **Run Tests**: `pytest test_app.py -v`
- **Database Migration**: `python migrate_db.py`
- **Health Check**: Visit `/health` endpoint

## Architecture Overview
- **Framework**: Flask application factory with blueprints
- **Security**: Flask-Talisman, CSRF protection, rate limiting, Argon2 passwords
- **Database**: SQLAlchemy ORM with PostgreSQL/SQLite support
- **Payment Integration**: NowPayments (crypto) and Flutterwave (fiat)
- **Deployment**: Render.com platform with Gunicorn WSGI server

## File Structure
- **app_factory.py**: Application factory with security extensions
- **models.py**: SQLAlchemy database models with relationships
- **auth.py**: Secure authentication with JWT and rate limiting
- **config.py**: Environment-based configuration classes
- **routes/**: Blueprint modules (main, auth, payment, api)

## Database & Storage
- **Production**: PostgreSQL with SQLAlchemy ORM
- **Development**: SQLite fallback for local development
- **Models**: Customer, Subscription, Payment, SecurityEvent, VulnerabilityScan
- **Migrations**: Flask-Migrate for schema versioning

## Security Features
- **Authentication**: Argon2 password hashing, JWT tokens, account lockout
- **CSRF Protection**: Flask-WTF with token validation
- **Rate Limiting**: Flask-Limiter with Redis backend
- **Security Headers**: Flask-Talisman with CSP, HSTS, XSS protection
- **Input Validation**: SQLAlchemy parameterized queries, form validation

## Code Style & Conventions
- **Python**: PEP 8 formatting, type hints, structured logging
- **Templates**: Jinja2 templates with Bootstrap 5 styling
- **Error Handling**: Centralized error handlers with JSON responses
- **Logging**: Structlog with JSON formatting for production
- **Testing**: Pytest with fixtures and comprehensive coverage

## Environment Variables (Required)
- **Security**: SECRET_KEY, ADMIN_PASSWORD
- **Database**: DATABASE_URL (PostgreSQL connection string)
- **Payments**: NOWPAYMENTS_API_KEY, NOWPAYMENTS_HMAC_KEY, FLW_SECRET_KEY, FLW_SECRET_HASH
- **Application**: BASE_URL, FLASK_ENV, REDIS_URL
