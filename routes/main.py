# Main Routes Blueprint
# routes/main.py - Public website routes

from flask import Blueprint, render_template_string, request, jsonify, current_app
from models import db, ContactInquiry
from datetime import datetime
import structlog

logger = structlog.get_logger()
main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def home():
    """Homepage with professional branding."""
    
    homepage_template = '''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>AstraFabric - Enterprise Security Monitoring Platform</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        <style>
            .hero-section { background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%); color: white; }
            .feature-card { border: none; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
            .pricing-card { border: 2px solid #e9ecef; transition: all 0.3s; }
            .pricing-card:hover { border-color: #007bff; transform: translateY(-5px); }
        </style>
    </head>
    <body>
        <!-- Navigation -->
        <nav class="navbar navbar-expand-lg navbar-dark bg-dark">
            <div class="container">
                <a class="navbar-brand fw-bold" href="/">🛡️ AstraFabric</a>
                <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
                    <span class="navbar-toggler-icon"></span>
                </button>
                <div class="collapse navbar-collapse" id="navbarNav">
                    <ul class="navbar-nav ms-auto">
                        <li class="nav-item"><a class="nav-link" href="#features">Features</a></li>
                        <li class="nav-item"><a class="nav-link" href="#pricing">Pricing</a></li>
                        <li class="nav-item"><a class="nav-link" href="/contact">Contact</a></li>
                        <li class="nav-item"><a class="nav-link btn btn-primary ms-2 px-3" href="/subscribe">Get Started</a></li>
                    </ul>
                </div>
            </div>
        </nav>

        <!-- Hero Section -->
        <section class="hero-section py-5">
            <div class="container">
                <div class="row align-items-center">
                    <div class="col-lg-6">
                        <h1 class="display-4 fw-bold mb-4">Complete Security Autopilot</h1>
                        <p class="lead mb-4">24/7 autonomous threat detection with 99% automation. Our AI-powered platform monitors your digital infrastructure continuously and responds to threats automatically.</p>
                        <div class="d-flex gap-3">
                            <a href="/subscribe" class="btn btn-light btn-lg">Start Free Trial</a>
                            <a href="#features" class="btn btn-outline-light btn-lg">Learn More</a>
                        </div>
                    </div>
                    <div class="col-lg-6 text-center">
                        <div class="bg-white rounded-3 p-4 shadow-lg">
                            <h5 class="text-dark mb-3">Real-Time Security Dashboard</h5>
                            <div class="row text-center">
                                <div class="col-4"><div class="text-success h4">✓</div><small class="text-muted">Threats Blocked</small></div>
                                <div class="col-4"><div class="text-warning h4">⚠️</div><small class="text-muted">Monitoring</small></div>
                                <div class="col-4"><div class="text-info h4">📊</div><small class="text-muted">Analytics</small></div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </section>

        <!-- Features Section -->
        <section id="features" class="py-5">
            <div class="container">
                <div class="text-center mb-5">
                    <h2 class="fw-bold">Enterprise Security Features</h2>
                    <p class="text-muted">Comprehensive protection for your digital infrastructure</p>
                </div>
                <div class="row g-4">
                    <div class="col-md-4">
                        <div class="card feature-card h-100 text-center p-4">
                            <div class="card-body">
                                <div class="fs-1 text-primary mb-3">🤖</div>
                                <h5 class="card-title">AI-Powered Detection</h5>
                                <p class="card-text">Advanced machine learning algorithms detect and respond to threats in real-time with 99% accuracy.</p>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-4">
                        <div class="card feature-card h-100 text-center p-4">
                            <div class="card-body">
                                <div class="fs-1 text-success mb-3">🛡️</div>
                                <h5 class="card-title">24/7 Monitoring</h5>
                                <p class="card-text">Continuous surveillance of your infrastructure with instant alerts and automated response protocols.</p>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-4">
                        <div class="card feature-card h-100 text-center p-4">
                            <div class="card-body">
                                <div class="fs-1 text-info mb-3">📊</div>
                                <h5 class="card-title">Compliance Reports</h5>
                                <p class="card-text">Automated generation of security compliance reports for SOC 2, ISO 27001, and other standards.</p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </section>

        <!-- Pricing Section -->
        <section id="pricing" class="py-5 bg-light">
            <div class="container">
                <div class="text-center mb-5">
                    <h2 class="fw-bold">Choose Your Security Plan</h2>
                    <p class="text-muted">Professional security monitoring for businesses of all sizes</p>
                </div>
                <div class="row g-4">
                    <div class="col-lg-4">
                        <div class="card pricing-card h-100 text-center">
                            <div class="card-body p-4">
                                <h5 class="card-title text-primary">Essential Autopilot</h5>
                                <div class="display-4 fw-bold my-3">$99<small class="fs-6 text-muted">/month</small></div>
                                <ul class="list-unstyled">
                                    <li class="mb-2">✓ Basic threat detection</li>
                                    <li class="mb-2">✓ Email alerts</li>
                                    <li class="mb-2">✓ Monthly reports</li>
                                    <li class="mb-2">✓ 24/7 monitoring</li>
                                </ul>
                                <a href="/subscribe?plan=essential" class="btn btn-outline-primary">Get Started</a>
                            </div>
                        </div>
                    </div>
                    <div class="col-lg-4">
                        <div class="card pricing-card h-100 text-center border-primary">
                            <div class="card-header bg-primary text-white">
                                <span class="badge bg-warning text-dark">POPULAR</span>
                            </div>
                            <div class="card-body p-4">
                                <h5 class="card-title text-primary">Professional Autopilot</h5>
                                <div class="display-4 fw-bold my-3">$199<small class="fs-6 text-muted">/month</small></div>
                                <ul class="list-unstyled">
                                    <li class="mb-2">✓ Advanced AI detection</li>
                                    <li class="mb-2">✓ Real-time alerts</li>
                                    <li class="mb-2">✓ Weekly reports</li>
                                    <li class="mb-2">✓ Vulnerability scanning</li>
                                    <li class="mb-2">✓ API access</li>
                                </ul>
                                <a href="/subscribe?plan=professional" class="btn btn-primary">Get Started</a>
                            </div>
                        </div>
                    </div>
                    <div class="col-lg-4">
                        <div class="card pricing-card h-100 text-center">
                            <div class="card-body p-4">
                                <h5 class="card-title text-primary">Enterprise Autopilot</h5>
                                <div class="display-4 fw-bold my-3">$299<small class="fs-6 text-muted">/month</small></div>
                                <ul class="list-unstyled">
                                    <li class="mb-2">✓ Full security suite</li>
                                    <li class="mb-2">✓ Instant notifications</li>
                                    <li class="mb-2">✓ Daily reports</li>
                                    <li class="mb-2">✓ Priority support</li>
                                    <li class="mb-2">✓ Custom integrations</li>
                                </ul>
                                <a href="/subscribe?plan=enterprise" class="btn btn-outline-primary">Get Started</a>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </section>

        <!-- Contact Section -->
        <section class="py-5">
            <div class="container">
                <div class="row">
                    <div class="col-lg-8 mx-auto text-center">
                        <h2 class="fw-bold mb-4">Ready to Secure Your Infrastructure?</h2>
                        <p class="lead mb-4">Join 150+ businesses that trust AstraFabric for their security monitoring needs.</p>
                        <div class="d-flex justify-content-center gap-3 mb-4">
                            <div class="text-center">
                                <div class="fw-bold fs-4">📞</div>
                                <small>+234 904 383 9065</small>
                            </div>
                            <div class="text-center">
                                <div class="fw-bold fs-4">💬</div>
                                <small>WhatsApp Support</small>
                            </div>
                            <div class="text-center">
                                <div class="fw-bold fs-4">📧</div>
                                <small>contact@astrafabric.com</small>
                            </div>
                        </div>
                        <a href="/contact" class="btn btn-primary btn-lg">Contact Sales Team</a>
                    </div>
                </div>
            </div>
        </section>

        <!-- Footer -->
        <footer class="bg-dark text-white py-4">
            <div class="container">
                <div class="row">
                    <div class="col-md-6">
                        <h5>🛡️ AstraFabric</h5>
                        <p class="small">Enterprise Security Monitoring Platform</p>
                    </div>
                    <div class="col-md-6 text-md-end">
                        <p class="small mb-0">© 2024 AstraFabric. All rights reserved.</p>
                        <p class="small">Automated Security Monitoring</p>
                    </div>
                </div>
            </div>
        </footer>

        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
    </body>
    </html>
    '''
    
    return render_template_string(homepage_template)


@main_bp.route('/subscribe')
def subscribe():
    """Subscription page placeholder."""
    return render_template_string('''
    <h1>Subscribe to AstraFabric</h1>
    <p>Subscription functionality coming soon!</p>
    <a href="/">← Back to Home</a>
    ''')


@main_bp.route('/contact', methods=['GET', 'POST'])
def contact():
    """Contact form."""
    if request.method == 'POST':
        try:
            # Validate required fields
            required_fields = ['name', 'email', 'subject', 'message']
            data = request.get_json() or request.form
            
            for field in required_fields:
                if not data.get(field):
                    return jsonify({'error': f'{field.capitalize()} is required'}), 400
            
            # Create contact inquiry
            inquiry = ContactInquiry(
                name=data['name'][:255],
                email=data['email'][:255],
                company=data.get('company', '')[:255],
                phone=data.get('phone', '')[:20],
                subject=data['subject'][:255],
                message=data['message'][:5000],
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent', '')
            )
            
            db.session.add(inquiry)
            db.session.commit()
            
            logger.info('Contact inquiry submitted', extra={
                'email': inquiry.email,
                'subject': inquiry.subject,
                'ip_address': inquiry.ip_address
            })
            
            return jsonify({
                'success': True,
                'message': 'Thank you for your inquiry. We will contact you within 24 hours.'
            })
            
        except Exception as e:
            logger.error('Contact form error', extra={'error': str(e)})
            return jsonify({'error': 'An error occurred. Please try again.'}), 500
    
    # GET request - show contact form
    return render_template_string('''
    <h1>Contact Us</h1>
    <p>Contact form coming soon!</p>
    <a href="/">← Back to Home</a>
    ''')


@main_bp.route('/health')
def health():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'version': '2.0.0'
    })