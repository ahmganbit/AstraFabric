# Dashboard Routes Blueprint
# routes/dashboard.py - Customer dashboard and subscription management

from flask import Blueprint, request, jsonify, render_template_string, session, redirect, url_for
from models import db, Customer, Subscription, Payment, SecurityEvent, VulnerabilityScan
from datetime import datetime, timedelta
import structlog

logger = structlog.get_logger()
dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Simple email-based login for customers."""
    if request.method == 'POST':
        data = request.get_json() or request.form
        email = data.get('email')
        
        if not email:
            return jsonify({'success': False, 'error': 'Email is required'}), 400
        
        customer = Customer.query.filter_by(email=email).first()
        if not customer:
            return jsonify({'success': False, 'error': 'Customer not found'}), 404
        
        # Simple session-based auth (for demo purposes)
        session['customer_id'] = customer.id
        session['customer_email'] = customer.email
        
        return jsonify({'success': True, 'redirect': '/dashboard'})
    
    # GET request - show login form
    login_template = '''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Customer Login - AstraFabric</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    </head>
    <body>
        <nav class="navbar navbar-expand-lg navbar-dark bg-dark">
            <div class="container">
                <a class="navbar-brand fw-bold" href="/">🛡️ AstraFabric</a>
            </div>
        </nav>

        <div class="container py-5">
            <div class="row justify-content-center">
                <div class="col-md-4">
                    <div class="card">
                        <div class="card-body p-4">
                            <h3 class="text-center mb-4">Customer Login</h3>
                            <form id="loginForm">
                                <div class="mb-3">
                                    <label class="form-label">Email Address</label>
                                    <input type="email" class="form-control" name="email" required>
                                </div>
                                <button type="submit" class="btn btn-primary w-100">Access Dashboard</button>
                            </form>
                            <div class="text-center mt-3">
                                <small class="text-muted">Enter the email used for your subscription</small>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
        <script>
            document.getElementById('loginForm').addEventListener('submit', async function(e) {
                e.preventDefault();
                
                const formData = new FormData(this);
                const data = Object.fromEntries(formData);
                
                try {
                    const response = await fetch('/dashboard/login', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(data)
                    });
                    
                    const result = await response.json();
                    if (result.success) {
                        window.location.href = result.redirect;
                    } else {
                        alert('Error: ' + result.error);
                    }
                } catch (error) {
                    alert('Login failed. Please try again.');
                }
            });
        </script>
    </body>
    </html>
    '''
    
    return render_template_string(login_template)


@dashboard_bp.route('/')
def dashboard():
    """Customer dashboard with subscription and security overview."""
    customer_id = session.get('customer_id')
    if not customer_id:
        return redirect('/dashboard/login')
    
    customer = Customer.query.get(customer_id)
    if not customer:
        session.clear()
        return redirect('/dashboard/login')
    
    # Get active subscription
    subscription = Subscription.query.filter_by(
        customer_id=customer_id,
        status='active'
    ).first()
    
    # Get recent payments
    payments = Payment.query.filter_by(customer_id=customer_id).order_by(
        Payment.created_at.desc()
    ).limit(5).all()
    
    # Get security events (simulated data for demo)
    security_events = SecurityEvent.query.filter_by(customer_id=customer_id).order_by(
        SecurityEvent.created_at.desc()
    ).limit(10).all()
    
    # Get vulnerability scans
    vulnerability_scans = VulnerabilityScan.query.filter_by(customer_id=customer_id).order_by(
        VulnerabilityScan.created_at.desc()
    ).limit(5).all()
    
    # Calculate days remaining
    days_remaining = 0
    if subscription and subscription.end_date:
        days_remaining = max(0, (subscription.end_date - datetime.utcnow()).days)
    
    dashboard_template = '''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Security Dashboard - AstraFabric</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        <style>
            .metric-card { border-left: 4px solid #007bff; }
            .threat-high { border-left-color: #dc3545; }
            .threat-medium { border-left-color: #ffc107; }
            .threat-low { border-left-color: #28a745; }
            .status-active { color: #28a745; }
            .status-inactive { color: #dc3545; }
        </style>
    </head>
    <body>
        <nav class="navbar navbar-expand-lg navbar-dark bg-dark">
            <div class="container">
                <a class="navbar-brand fw-bold" href="/">🛡️ AstraFabric</a>
                <div class="navbar-nav ms-auto">
                    <span class="navbar-text me-3">{{ customer.name }}</span>
                    <a class="nav-link" href="/dashboard/logout">Logout</a>
                </div>
            </div>
        </nav>

        <div class="container-fluid py-4">
            <div class="row">
                <!-- Subscription Status -->
                <div class="col-12 mb-4">
                    <div class="card">
                        <div class="card-body">
                            <div class="row align-items-center">
                                <div class="col-md-8">
                                    <h5 class="mb-1">
                                        {% if subscription %}
                                            {{ subscription.plan.value.title() }} Plan
                                            <span class="badge bg-success">Active</span>
                                        {% else %}
                                            No Active Subscription
                                            <span class="badge bg-warning">Inactive</span>
                                        {% endif %}
                                    </h5>
                                    <p class="text-muted mb-0">
                                        {% if subscription %}
                                            {{ days_remaining }} days remaining • ${{ subscription.amount }}/{{ subscription.billing_cycle }}
                                        {% else %}
                                            Subscribe to activate security monitoring
                                        {% endif %}
                                    </p>
                                </div>
                                <div class="col-md-4 text-md-end">
                                    {% if subscription %}
                                        <a href="/subscribe" class="btn btn-outline-primary">Upgrade Plan</a>
                                    {% else %}
                                        <a href="/subscribe" class="btn btn-primary">Subscribe Now</a>
                                    {% endif %}
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Security Metrics -->
                <div class="col-md-3 mb-4">
                    <div class="card metric-card">
                        <div class="card-body text-center">
                            <h3 class="text-primary">{{ security_events|length }}</h3>
                            <p class="mb-0">Security Events</p>
                            <small class="text-muted">Last 30 days</small>
                        </div>
                    </div>
                </div>
                
                <div class="col-md-3 mb-4">
                    <div class="card metric-card threat-high">
                        <div class="card-body text-center">
                            <h3 class="text-danger">
                                {{ security_events|selectattr("severity", "equalto", "high")|list|length }}
                            </h3>
                            <p class="mb-0">High Priority</p>
                            <small class="text-muted">Threats blocked</small>
                        </div>
                    </div>
                </div>
                
                <div class="col-md-3 mb-4">
                    <div class="card metric-card threat-medium">
                        <div class="card-body text-center">
                            <h3 class="text-warning">
                                {{ security_events|selectattr("severity", "equalto", "medium")|list|length }}
                            </h3>
                            <p class="mb-0">Medium Priority</p>
                            <small class="text-muted">Threats detected</small>
                        </div>
                    </div>
                </div>
                
                <div class="col-md-3 mb-4">
                    <div class="card metric-card threat-low">
                        <div class="card-body text-center">
                            <h3 class="text-success">99.8%</h3>
                            <p class="mb-0">Uptime</p>
                            <small class="text-muted">System availability</small>
                        </div>
                    </div>
                </div>

                <!-- Recent Security Events -->
                <div class="col-md-8 mb-4">
                    <div class="card">
                        <div class="card-header">
                            <h5 class="mb-0">Recent Security Events</h5>
                        </div>
                        <div class="card-body">
                            {% if security_events %}
                                <div class="table-responsive">
                                    <table class="table table-sm">
                                        <thead>
                                            <tr>
                                                <th>Time</th>
                                                <th>Event</th>
                                                <th>Severity</th>
                                                <th>Status</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {% for event in security_events %}
                                            <tr>
                                                <td>{{ event.created_at.strftime('%m/%d %H:%M') }}</td>
                                                <td>{{ event.event_type.replace('_', ' ').title() }}</td>
                                                <td>
                                                    <span class="badge bg-{% if event.severity == 'high' %}danger{% elif event.severity == 'medium' %}warning{% else %}success{% endif %}">
                                                        {{ event.severity.title() }}
                                                    </span>
                                                </td>
                                                <td>
                                                    {% if event.is_resolved %}
                                                        <span class="text-success">✓ Resolved</span>
                                                    {% else %}
                                                        <span class="text-warning">⚠ Monitoring</span>
                                                    {% endif %}
                                                </td>
                                            </tr>
                                            {% endfor %}
                                        </tbody>
                                    </table>
                                </div>
                            {% else %}
                                <div class="text-center py-4">
                                    <div class="text-muted">
                                        <div class="fs-1 mb-3">🛡️</div>
                                        <p>No security events detected</p>
                                        <small>Your systems are secure</small>
                                    </div>
                                </div>
                            {% endif %}
                        </div>
                    </div>
                </div>

                <!-- Payment History -->
                <div class="col-md-4 mb-4">
                    <div class="card">
                        <div class="card-header">
                            <h5 class="mb-0">Payment History</h5>
                        </div>
                        <div class="card-body">
                            {% if payments %}
                                {% for payment in payments %}
                                <div class="d-flex justify-content-between align-items-center mb-3">
                                    <div>
                                        <div class="fw-bold">${{ payment.amount }}</div>
                                        <small class="text-muted">{{ payment.created_at.strftime('%Y-%m-%d') }}</small>
                                    </div>
                                    <span class="badge bg-{% if payment.status.value == 'completed' %}success{% elif payment.status.value == 'pending' %}warning{% else %}danger{% endif %}">
                                        {{ payment.status.value.title() }}
                                    </span>
                                </div>
                                {% endfor %}
                            {% else %}
                                <div class="text-center py-3">
                                    <div class="text-muted">
                                        <div class="fs-2 mb-2">💳</div>
                                        <p class="mb-0">No payments yet</p>
                                        <a href="/subscribe" class="btn btn-sm btn-primary mt-2">Subscribe</a>
                                    </div>
                                </div>
                            {% endif %}
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
    </body>
    </html>
    '''
    
    return render_template_string(
        dashboard_template,
        customer=customer,
        subscription=subscription,
        payments=payments,
        security_events=security_events,
        vulnerability_scans=vulnerability_scans,
        days_remaining=days_remaining
    )


@dashboard_bp.route('/logout')
def logout():
    """Logout customer."""
    session.clear()
    return redirect('/')


@dashboard_bp.route('/api/metrics')
def api_metrics():
    """API endpoint for dashboard metrics."""
    customer_id = session.get('customer_id')
    if not customer_id:
        return jsonify({'error': 'Not authenticated'}), 401
    
    # Get security metrics
    total_events = SecurityEvent.query.filter_by(customer_id=customer_id).count()
    high_priority = SecurityEvent.query.filter_by(
        customer_id=customer_id, severity='high'
    ).count()
    medium_priority = SecurityEvent.query.filter_by(
        customer_id=customer_id, severity='medium'
    ).count()
    
    return jsonify({
        'total_events': total_events,
        'high_priority': high_priority,
        'medium_priority': medium_priority,
        'uptime': 99.8,
        'last_updated': datetime.utcnow().isoformat()
    })