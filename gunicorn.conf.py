# Gunicorn Configuration for AstraFabric Platform
# gunicorn.conf.py

import os

# Server socket
bind = f"0.0.0.0:{os.environ.get('PORT', 10000)}"
backlog = 2048

# Worker processes (optimized for free tier)
workers = int(os.environ.get('GUNICORN_WORKERS', 1))  # Free tier default
worker_class = "sync"
worker_connections = 500  # Reduced for free tier
timeout = int(os.environ.get('GUNICORN_TIMEOUT', 30))
keepalive = 2

# Restart workers after this many requests, to help prevent memory leaks
max_requests = 1000
max_requests_jitter = 50

# Application - Fixed WSGI module reference
wsgi_module = "app_factory:app"
pythonpath = "."

# Logging
accesslog = "-"
errorlog = "-"
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Process naming
proc_name = "astrafabric-gunicorn"

# Security
limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190

# Performance
preload_app = True