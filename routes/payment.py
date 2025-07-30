# Payment Routes Blueprint
# routes/payment.py - Complete payment processing with NowPayments and Flutterwave

from flask import Blueprint, request, jsonify, render_template_string, current_app, redirect, url_for
from models import db, Customer, Subscription, Payment, PaymentStatus, SubscriptionPlan
from datetime import datetime, timedelta
import requests
import hashlib
import hmac
import uuid
import structlog

logger = structlog.get_logger()
payment_bp = Blueprint('payment', __name__)

# Pricing configuration
PRICING = {
    'essential': {'monthly': 99, 'yearly': 990},
    'professional': {'monthly': 199, 'yearly': 1990},
    'enterprise': {'monthly': 299, 'yearly': 2990}
}

@payment_bp.route('/subscribe')
def subscribe():
    """Subscription page with payment options."""
    plan = request.args.get('plan', 'professional')
    billing = request.args.get('billing', 'monthly')
    
    if plan not in PRICING:
        plan = 'professional'
    if billing not in ['monthly', 'yearly']:
        billing = 'monthly'
    
    price = PRICING[plan][billing]
    
    subscribe_template = '''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Subscribe - AstraFabric Security Platform</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        <style>
            .payment-card { border: 2px solid #e9ecef; border-radius: 15px; transition: all 0.3s; }
            .payment-card:hover { border-color: #007bff; transform: translateY(-2px); }
            .plan-badge { background: linear-gradient(45deg, #007bff, #0056b3); }
        </style>
    </head>
    <body>
        <nav class="navbar navbar-expand-lg navbar-dark bg-dark">
            <div class="container">
                <a class="navbar-brand fw-bold" href="/">🛡️ AstraFabric</a>
                <div class="navbar-nav ms-auto">
                    <a class="nav-link" href="/">Home</a>
                    <a class="nav-link" href="/contact">Contact</a>
                </div>
            </div>
        </nav>

        <div class="container py-5">
            <div class="row justify-content-center">
                <div class="col-lg-8">
                    <div class="text-center mb-5">
                        <h1 class="display-5 fw-bold">Complete Your Subscription</h1>
                        <p class="lead text-muted">Start your security autopilot journey today</p>
                    </div>
                    
                    <!-- Plan Selection -->
                    <div class="card mb-4">
                        <div class="card-body">
                            <div class="row align-items-center">
                                <div class="col-md-8">
                                    <h4 class="mb-1">{{ plan.title() }} Autopilot 
                                        <span class="badge plan-badge text-white">{{ billing.title() }}</span>
                                    </h4>
                                    <p class="text-muted mb-0">
                                        {% if plan == 'essential' %}
                                            Basic threat detection, email alerts, monthly reports, 24/7 monitoring
                                        {% elif plan == 'professional' %}
                                            Advanced AI detection, real-time alerts, weekly reports, vulnerability scanning, API access
                                        {% else %}
                                            Full security suite, instant notifications, daily reports, priority support, custom integrations
                                        {% endif %}
                                    </p>
                                </div>
                                <div class="col-md-4 text-md-end">
                                    <div class="h2 fw-bold text-primary">${{ price }}</div>
                                    <small class="text-muted">per {{ billing.replace('ly', '') }}</small>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- Customer Information -->
                    <div class="card mb-4">
                        <div class="card-header">
                            <h5 class="mb-0">Customer Information</h5>
                        </div>
                        <div class="card-body">
                            <form id="customerForm">
                                <div class="row">
                                    <div class="col-md-6 mb-3">
                                        <label class="form-label">Full Name *</label>
                                        <input type="text" class="form-control" name="name" required>
                                    </div>
                                    <div class="col-md-6 mb-3">
                                        <label class="form-label">Email Address *</label>
                                        <input type="email" class="form-control" name="email" required>
                                    </div>
                                </div>
                                <div class="row">
                                    <div class="col-md-6 mb-3">
                                        <label class="form-label">Company</label>
                                        <input type="text" class="form-control" name="company">
                                    </div>
                                    <div class="col-md-6 mb-3">
                                        <label class="form-label">Phone</label>
                                        <input type="tel" class="form-control" name="phone">
                                    </div>
                                </div>
                            </form>
                        </div>
                    </div>

                    <!-- Payment Methods -->
                    <div class="card">
                        <div class="card-header">
                            <h5 class="mb-0">Choose Payment Method</h5>
                        </div>
                        <div class="card-body">
                            <div class="row g-3">
                                <!-- Cryptocurrency Payment -->
                                <div class="col-md-6">
                                    <div class="payment-card p-4 h-100 text-center">
                                        <div class="fs-1 mb-3">₿</div>
                                        <h5>Cryptocurrency</h5>
                                        <p class="text-muted small">Bitcoin, Ethereum, USDT, and 100+ cryptocurrencies</p>
                                        <button class="btn btn-primary w-100" onclick="initiateCryptoPayment()">
                                            Pay with Crypto
                                        </button>
                                    </div>
                                </div>
                                
                                <!-- Card Payment -->
                                <div class="col-md-6">
                                    <div class="payment-card p-4 h-100 text-center">
                                        <div class="fs-1 mb-3">💳</div>
                                        <h5>Credit/Debit Card</h5>
                                        <p class="text-muted small">Visa, Mastercard, American Express</p>
                                        <button class="btn btn-outline-primary w-100" onclick="initiateCardPayment()">
                                            Pay with Card
                                        </button>
                                    </div>
                                </div>
                            </div>
                            
                            <div class="text-center mt-4">
                                <small class="text-muted">
                                    🔒 Secure payment processing • 30-day money-back guarantee • Cancel anytime
                                </small>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
        <script>
            const plan = '{{ plan }}';
            const billing = '{{ billing }}';
            const price = {{ price }};

            function validateCustomerForm() {
                const form = document.getElementById('customerForm');
                const formData = new FormData(form);
                const data = Object.fromEntries(formData);
                
                if (!data.name || !data.email) {
                    alert('Please fill in all required fields');
                    return null;
                }
                
                return data;
            }

            async function initiateCryptoPayment() {
                const customerData = validateCustomerForm();
                if (!customerData) return;

                try {
                    const response = await fetch('/payment/crypto/initiate', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            ...customerData,
                            plan: plan,
                            billing: billing,
                            amount: price
                        })
                    });

                    const result = await response.json();
                    if (result.success) {
                        window.location.href = result.payment_url;
                    } else {
                        alert('Error: ' + result.error);
                    }
                } catch (error) {
                    alert('Payment initiation failed. Please try again.');
                }
            }

            async function initiateCardPayment() {
                const customerData = validateCustomerForm();
                if (!customerData) return;

                try {
                    const response = await fetch('/payment/card/initiate', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            ...customerData,
                            plan: plan,
                            billing: billing,
                            amount: price
                        })
                    });

                    const result = await response.json();
                    if (result.success) {
                        window.location.href = result.payment_url;
                    } else {
                        alert('Error: ' + result.error);
                    }
                } catch (error) {
                    alert('Payment initiation failed. Please try again.');
                }
            }
        </script>
    </body>
    </html>
    '''
    
    return render_template_string(subscribe_template, plan=plan, billing=billing, price=price)


@payment_bp.route('/crypto/initiate', methods=['POST'])
def initiate_crypto_payment():
    """Initiate cryptocurrency payment via NowPayments."""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['name', 'email', 'plan', 'billing', 'amount']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'success': False, 'error': f'{field} is required'}), 400
        
        # Create or get customer
        customer = Customer.query.filter_by(email=data['email']).first()
        if not customer:
            customer = Customer(
                email=data['email'],
                name=data['name'],
                company=data.get('company', ''),
                phone=data.get('phone', '')
            )
            db.session.add(customer)
            db.session.flush()
        
        # Create payment record
        payment_reference = f"AF-{uuid.uuid4().hex[:8].upper()}"
        payment = Payment(
            customer_id=customer.id,
            payment_method='crypto',
            gateway='nowpayments',
            reference=payment_reference,
            amount=data['amount'],
            currency='USD',
            status=PaymentStatus.PENDING,
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent', '')
        )
        db.session.add(payment)
        db.session.commit()
        
        # Create NowPayments payment
        nowpayments_response = create_nowpayments_payment(
            amount=data['amount'],
            order_id=payment_reference,
            customer_email=data['email']
        )
        
        if nowpayments_response['success']:
            payment.gateway_transaction_id = nowpayments_response['payment_id']
            db.session.commit()
            
            return jsonify({
                'success': True,
                'payment_url': nowpayments_response['payment_url'],
                'payment_id': nowpayments_response['payment_id']
            })
        else:
            return jsonify({'success': False, 'error': nowpayments_response['error']}), 400
            
    except Exception as e:
        logger.error('Crypto payment initiation error', extra={'error': str(e)})
        return jsonify({'success': False, 'error': 'Payment initiation failed'}), 500


@payment_bp.route('/card/initiate', methods=['POST'])
def initiate_card_payment():
    """Initiate card payment via Flutterwave."""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['name', 'email', 'plan', 'billing', 'amount']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'success': False, 'error': f'{field} is required'}), 400
        
        # Create or get customer
        customer = Customer.query.filter_by(email=data['email']).first()
        if not customer:
            customer = Customer(
                email=data['email'],
                name=data['name'],
                company=data.get('company', ''),
                phone=data.get('phone', '')
            )
            db.session.add(customer)
            db.session.flush()
        
        # Create payment record
        payment_reference = f"AF-{uuid.uuid4().hex[:8].upper()}"
        payment = Payment(
            customer_id=customer.id,
            payment_method='card',
            gateway='flutterwave',
            reference=payment_reference,
            amount=data['amount'],
            currency='USD',
            status=PaymentStatus.PENDING,
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent', '')
        )
        db.session.add(payment)
        db.session.commit()
        
        # Create Flutterwave payment
        flutterwave_response = create_flutterwave_payment(
            amount=data['amount'],
            tx_ref=payment_reference,
            customer_email=data['email'],
            customer_name=data['name'],
            customer_phone=data.get('phone', '')
        )
        
        if flutterwave_response['success']:
            payment.gateway_transaction_id = flutterwave_response['payment_id']
            db.session.commit()
            
            return jsonify({
                'success': True,
                'payment_url': flutterwave_response['payment_url'],
                'payment_id': flutterwave_response['payment_id']
            })
        else:
            return jsonify({'success': False, 'error': flutterwave_response['error']}), 400
            
    except Exception as e:
        logger.error('Card payment initiation error', extra={'error': str(e)})
        return jsonify({'success': False, 'error': 'Payment initiation failed'}), 500


def create_nowpayments_payment(amount, order_id, customer_email):
    """Create payment with NowPayments API."""
    try:
        api_key = current_app.config.get('NOWPAYMENTS_API_KEY')
        if not api_key:
            return {'success': False, 'error': 'NowPayments not configured'}
        
        url = "https://api.nowpayments.io/v1/payment"
        headers = {
            'x-api-key': api_key,
            'Content-Type': 'application/json'
        }
        
        payload = {
            'price_amount': amount,
            'price_currency': 'USD',
            'pay_currency': 'btc',  # Default to Bitcoin
            'order_id': order_id,
            'order_description': f'AstraFabric Security Subscription - {order_id}',
            'success_url': f"{current_app.config.get('BASE_URL')}/payment/success",
            'cancel_url': f"{current_app.config.get('BASE_URL')}/payment/cancel"
        }
        
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        
        if response.status_code == 201:
            data = response.json()
            return {
                'success': True,
                'payment_id': data['payment_id'],
                'payment_url': data['invoice_url']
            }
        else:
            logger.error('NowPayments API error', extra={
                'status_code': response.status_code,
                'response': response.text
            })
            return {'success': False, 'error': 'Payment gateway error'}
            
    except Exception as e:
        logger.error('NowPayments creation error', extra={'error': str(e)})
        return {'success': False, 'error': 'Payment service unavailable'}


def create_flutterwave_payment(amount, tx_ref, customer_email, customer_name, customer_phone):
    """Create payment with Flutterwave API."""
    try:
        secret_key = current_app.config.get('FLW_SECRET_KEY')
        if not secret_key:
            return {'success': False, 'error': 'Flutterwave not configured'}
        
        url = "https://api.flutterwave.com/v3/payments"
        headers = {
            'Authorization': f'Bearer {secret_key}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            'tx_ref': tx_ref,
            'amount': amount,
            'currency': 'USD',
            'redirect_url': f"{current_app.config.get('BASE_URL')}/payment/flutterwave/callback",
            'customer': {
                'email': customer_email,
                'name': customer_name,
                'phonenumber': customer_phone
            },
            'customizations': {
                'title': 'AstraFabric Security Subscription',
                'description': f'Security monitoring subscription - {tx_ref}',
                'logo': f"{current_app.config.get('BASE_URL')}/static/logo.png"
            }
        }
        
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            if data['status'] == 'success':
                return {
                    'success': True,
                    'payment_id': data['data']['id'],
                    'payment_url': data['data']['link']
                }
        
        logger.error('Flutterwave API error', extra={
            'status_code': response.status_code,
            'response': response.text
        })
        return {'success': False, 'error': 'Payment gateway error'}
        
    except Exception as e:
        logger.error('Flutterwave creation error', extra={'error': str(e)})
        return {'success': False, 'error': 'Payment service unavailable'}


@payment_bp.route('/success')
def payment_success():
    """Payment success page."""
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Payment Successful - AstraFabric</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    </head>
    <body>
        <div class="container py-5">
            <div class="row justify-content-center">
                <div class="col-md-6 text-center">
                    <div class="card">
                        <div class="card-body p-5">
                            <div class="text-success fs-1 mb-3">✅</div>
                            <h2 class="text-success mb-3">Payment Successful!</h2>
                            <p class="lead">Your AstraFabric subscription is now active.</p>
                            <p class="text-muted">You will receive a confirmation email shortly with your account details.</p>
                            <a href="/" class="btn btn-primary">Return to Dashboard</a>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </body>
    </html>
    ''')


@payment_bp.route('/cancel')
def payment_cancel():
    """Payment cancellation page."""
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Payment Cancelled - AstraFabric</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    </head>
    <body>
        <div class="container py-5">
            <div class="row justify-content-center">
                <div class="col-md-6 text-center">
                    <div class="card">
                        <div class="card-body p-5">
                            <div class="text-warning fs-1 mb-3">⚠️</div>
                            <h2 class="text-warning mb-3">Payment Cancelled</h2>
                            <p class="lead">Your payment was cancelled.</p>
                            <p class="text-muted">No charges were made to your account.</p>
                            <a href="/subscribe" class="btn btn-primary">Try Again</a>
                            <a href="/" class="btn btn-outline-secondary ms-2">Return Home</a>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </body>
    </html>
    ''')


# Webhook handlers will be added in the next file...