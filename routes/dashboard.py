# Dashboard Routes Blueprint
# routes/dashboard.py - Customer dashboard and subscription management

from flask import Blueprint, request, jsonify, render_template_string, session, redirect, url_for
from models import db, Customer, Subscription, Payment, SecurityEvent, VulnerabilityScan, SubscriptionStatus
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
    
    # Get active or cancelled subscription
    subscription = Subscription.query.filter_by(customer_id=customer_id).filter(
        Subscription.status.in_([SubscriptionStatus.ACTIVE, SubscriptionStatus.CANCELLED])
    ).order_by(Subscription.created_at.desc()).first()
    
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
        VulnerabilityScan.started_at.desc()
    ).limit(5).all()
    
    # Calculate days remaining
    days_remaining = 0
    if subscription and subscription.ends_at and subscription.status == SubscriptionStatus.ACTIVE:
        days_remaining = max(0, (subscription.ends_at - datetime.utcnow()).days)
    
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
                                            {% if subscription.status.value == 'active' %}
                                                <span class="badge bg-success">Active</span>
                                            {% elif subscription.status.value == 'cancelled' %}
                                                <span class="badge bg-warning">Cancelled</span>
                                            {% else %}
                                                <span class="badge bg-secondary">{{ subscription.status.value.title() }}</span>
                                            {% endif %}
                                        {% else %}
                                            No Active Subscription
                                            <span class="badge bg-warning">Inactive</span>
                                        {% endif %}
                                    </h5>
                                    <p class="text-muted mb-0">
                                        {% if subscription %}
                                            {% if subscription.status.value == 'cancelled' %}
                                                Cancelled on {{ subscription.cancelled_at.strftime('%B %d, %Y') }}
                                                {% if subscription.ends_at %}
                                                    • Access until {{ subscription.ends_at.strftime('%B %d, %Y') }}
                                                {% endif %}
                                            {% else %}
                                                {{ days_remaining }} days remaining • ${{ subscription.amount }}/{{ subscription.billing_cycle }}
                                            {% endif %}
                                        {% else %}
                                            Subscribe to activate security monitoring
                                        {% endif %}
                                    </p>
                                </div>
                                <div class="col-md-4 text-md-end">
                                    {% if subscription %}
                                        {% if subscription.status.value == 'active' %}
                                            <a href="/subscribe" class="btn btn-outline-primary me-2">Upgrade Plan</a>
                                            <a href="/dashboard/subscription/cancel" class="btn btn-outline-danger">Cancel</a>
                                        {% elif subscription.status.value == 'cancelled' %}
                                            <button onclick="reactivateSubscription()" class="btn btn-success">Reactivate</button>
                                        {% endif %}
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
        <script>
            async function reactivateSubscription() {
                if (!confirm('Are you sure you want to reactivate your subscription? Billing will resume according to your plan.')) {
                    return;
                }
                
                try {
                    const response = await fetch('/dashboard/subscription/reactivate', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        }
                    });
                    
                    const result = await response.json();
                    
                    if (result.success) {
                        alert(result.message);
                        window.location.reload();
                    } else {
                        alert('Error: ' + result.error);
                    }
                } catch (error) {
                    alert('An error occurred. Please try again.');
                }
            }
        </script>
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


@dashboard_bp.route('/subscription/cancel', methods=['GET', 'POST'])
def cancel_subscription():
    """Cancel customer subscription."""
    customer_id = session.get('customer_id')
    if not customer_id:
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    
    customer = Customer.query.get(customer_id)
    if not customer:
        return jsonify({'success': False, 'error': 'Customer not found'}), 404
    
    # Find active subscription
    subscription = Subscription.query.filter_by(
        customer_id=customer_id,
        status=SubscriptionStatus.ACTIVE
    ).first()
    
    if not subscription:
        return jsonify({'success': False, 'error': 'No active subscription found'}), 404
    
    if request.method == 'POST':
        try:
            data = request.get_json() or request.form
            reason = data.get('reason', '').strip()
            
            # Validate cancellation reason
            if not reason:
                return jsonify({'success': False, 'error': 'Cancellation reason is required'}), 400
            
            if len(reason) > 500:
                return jsonify({'success': False, 'error': 'Reason must be less than 500 characters'}), 400
            
            # Cancel the subscription
            subscription.cancel(reason=reason)
            
            logger.info('Subscription cancelled', extra={
                'customer_id': customer_id,
                'customer_email': customer.email,
                'subscription_id': subscription.id,
                'plan': subscription.plan.value,
                'reason': reason
            })
            
            return jsonify({
                'success': True,
                'message': 'Your subscription has been cancelled successfully. You will continue to have access until the end of your current billing period.'
            })
            
        except Exception as e:
            logger.error('Subscription cancellation error', extra={
                'error': str(e),
                'customer_id': customer_id,
                'subscription_id': subscription.id if subscription else None
            })
            return jsonify({'success': False, 'error': 'An error occurred while cancelling your subscription. Please contact support.'}), 500
    
    # GET request - show cancellation form
    cancellation_template = '''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Cancel Subscription - AstraFabric</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    </head>
    <body>
        <nav class="navbar navbar-expand-lg navbar-dark bg-dark">
            <div class="container">
                <a class="navbar-brand fw-bold" href="/">🛡️ AstraFabric</a>
                <div class="navbar-nav ms-auto">
                    <span class="navbar-text me-3">{{ customer.name }}</span>
                    <a class="nav-link" href="/dashboard">Dashboard</a>
                    <a class="nav-link" href="/dashboard/logout">Logout</a>
                </div>
            </div>
        </nav>

        <div class="container py-5">
            <div class="row justify-content-center">
                <div class="col-md-8 col-lg-6">
                    <div class="card">
                        <div class="card-header bg-warning text-dark">
                            <h4 class="mb-0">⚠️ Cancel Subscription</h4>
                        </div>
                        <div class="card-body">
                            <div class="alert alert-info">
                                <h5 class="alert-heading">Current Subscription Details</h5>
                                <p class="mb-1"><strong>Plan:</strong> {{ subscription.plan.value.title() }}</p>
                                <p class="mb-1"><strong>Amount:</strong> ${{ subscription.amount }}/{{ subscription.billing_cycle }}</p>
                                <p class="mb-0"><strong>Started:</strong> {{ subscription.started_at.strftime('%B %d, %Y') }}</p>
                            </div>
                            
                            <div class="alert alert-warning">
                                <h6 class="fw-bold">What happens when you cancel:</h6>
                                <ul class="mb-0">
                                    <li>You'll continue to have access until the end of your current billing period</li>
                                    <li>No future charges will be made to your payment method</li>
                                    <li>Your security monitoring data will be preserved for 90 days</li>
                                    <li>You can reactivate your subscription at any time</li>
                                </ul>
                            </div>
                            
                            <form id="cancellation-form">
                                <div class="mb-3">
                                    <label for="reason" class="form-label">Please tell us why you're cancelling (required):</label>
                                    <textarea class="form-control" id="reason" name="reason" rows="4" 
                                              placeholder="e.g., Too expensive, Not using enough, Found a better alternative, etc." 
                                              required maxlength="500"></textarea>
                                    <div class="form-text">This helps us improve our service (max 500 characters)</div>
                                </div>
                                
                                <div class="d-grid gap-2">
                                    <button type="submit" class="btn btn-danger">
                                        <i class="fas fa-times"></i> Cancel My Subscription
                                    </button>
                                    <a href="/dashboard" class="btn btn-outline-secondary">
                                        <i class="fas fa-arrow-left"></i> Back to Dashboard
                                    </a>
                                </div>
                            </form>
                            
                            <div id="success-message" class="alert alert-success mt-3" style="display: none;"></div>
                            <div id="error-message" class="alert alert-danger mt-3" style="display: none;"></div>
                        </div>
                    </div>
                    
                    <div class="text-center mt-4">
                        <p class="text-muted">Need help? Contact our support team:</p>
                        <p>
                            <strong>Email:</strong> support@astrafabric.com<br>
                            <strong>WhatsApp:</strong> +234 908 482 4238
                        </p>
                    </div>
                </div>
            </div>
        </div>

        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
        <script>
            document.getElementById('cancellation-form').addEventListener('submit', async function(e) {
                e.preventDefault();
                
                const reason = document.getElementById('reason').value.trim();
                if (!reason) {
                    showError('Please provide a reason for cancelling');
                    return;
                }
                
                try {
                    const response = await fetch('/dashboard/subscription/cancel', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({ reason: reason })
                    });
                    
                    const result = await response.json();
                    
                    if (result.success) {
                        showSuccess(result.message);
                        document.getElementById('cancellation-form').style.display = 'none';
                        setTimeout(() => {
                            window.location.href = '/dashboard';
                        }, 3000);
                    } else {
                        showError(result.error);
                    }
                } catch (error) {
                    showError('An error occurred. Please try again.');
                }
            });
            
            function showSuccess(message) {
                const div = document.getElementById('success-message');
                div.textContent = message;
                div.style.display = 'block';
                document.getElementById('error-message').style.display = 'none';
            }
            
            function showError(message) {
                const div = document.getElementById('error-message');
                div.textContent = message;
                div.style.display = 'block';
                document.getElementById('success-message').style.display = 'none';
            }
        </script>
    </body>
    </html>
    '''
    
    return render_template_string(cancellation_template, customer=customer, subscription=subscription)


@dashboard_bp.route('/subscription/reactivate', methods=['POST'])
def reactivate_subscription():
    """Reactivate a cancelled subscription."""
    customer_id = session.get('customer_id')
    if not customer_id:
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    
    customer = Customer.query.get(customer_id)
    if not customer:
        return jsonify({'success': False, 'error': 'Customer not found'}), 404
    
    # Find cancelled subscription
    subscription = Subscription.query.filter_by(
        customer_id=customer_id,
        status=SubscriptionStatus.CANCELLED
    ).order_by(Subscription.cancelled_at.desc()).first()
    
    if not subscription:
        return jsonify({'success': False, 'error': 'No cancelled subscription found'}), 404
    
    try:
        # Reactivate subscription
        subscription.status = SubscriptionStatus.ACTIVE
        subscription.cancelled_at = None
        subscription.cancellation_reason = None
        subscription.updated_at = datetime.utcnow()
        db.session.commit()
        
        logger.info('Subscription reactivated', extra={
            'customer_id': customer_id,
            'customer_email': customer.email,
            'subscription_id': subscription.id,
            'plan': subscription.plan.value
        })
        
        return jsonify({
            'success': True,
            'message': 'Your subscription has been reactivated successfully!'
        })
        
    except Exception as e:
        logger.error('Subscription reactivation error', extra={
            'error': str(e),
            'customer_id': customer_id,
            'subscription_id': subscription.id
        })
        return jsonify({'success': False, 'error': 'An error occurred while reactivating your subscription. Please contact support.'}), 500