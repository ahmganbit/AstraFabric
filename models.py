# AstraFabric Database Models
# models.py - SQLAlchemy models with security best practices

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Numeric
from datetime import datetime
import uuid
from enum import Enum

db = SQLAlchemy()


class PaymentStatus(Enum):
    """Payment status enumeration."""
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"


class SubscriptionPlan(Enum):
    """Subscription plan enumeration."""
    ESSENTIAL = "essential"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"


class Customer(db.Model):
    """Customer model with secure data handling."""
    __tablename__ = 'customers'
    
    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    name = db.Column(db.String(255), nullable=False)
    company = db.Column(db.String(255))
    phone = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    
    # Relationships
    subscriptions = db.relationship('Subscription', backref='customer', lazy='dynamic')
    payments = db.relationship('Payment', backref='customer', lazy='dynamic')
    security_events = db.relationship('SecurityEvent', backref='customer', lazy='dynamic')
    
    def __repr__(self):
        return f'<Customer {self.email}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'uuid': self.uuid,
            'email': self.email,
            'name': self.name,
            'company': self.company,
            'created_at': self.created_at.isoformat(),
            'is_active': self.is_active
        }


class Subscription(db.Model):
    """Subscription model with plan management."""
    __tablename__ = 'subscriptions'
    
    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=False, index=True)
    plan = db.Column(db.Enum(SubscriptionPlan), nullable=False)
    status = db.Column(db.String(20), default='active', nullable=False)
    start_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    end_date = db.Column(db.DateTime)
    billing_cycle = db.Column(db.String(20), default='monthly', nullable=False)  # monthly, yearly
    amount = db.Column(Numeric(10, 2), nullable=False)
    currency = db.Column(db.String(3), default='USD', nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Subscription {self.plan.value} for Customer {self.customer_id}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'uuid': self.uuid,
            'plan': self.plan.value,
            'status': self.status,
            'start_date': self.start_date.isoformat(),
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'billing_cycle': self.billing_cycle,
            'amount': float(self.amount),
            'currency': self.currency
        }


class Payment(db.Model):
    """Payment model with comprehensive tracking."""
    __tablename__ = 'payments'
    
    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=False, index=True)
    subscription_id = db.Column(db.Integer, db.ForeignKey('subscriptions.id'), index=True)
    
    # Payment details
    payment_method = db.Column(db.String(50), nullable=False)  # crypto, card, mobile_money
    gateway = db.Column(db.String(50), nullable=False)  # nowpayments, flutterwave
    gateway_transaction_id = db.Column(db.String(255), index=True)
    reference = db.Column(db.String(255), unique=True, nullable=False, index=True)
    
    # Amount and currency
    amount = db.Column(Numeric(10, 2), nullable=False)
    currency = db.Column(db.String(10), nullable=False)
    exchange_rate = db.Column(Numeric(15, 8))  # For crypto payments
    
    # Status tracking
    status = db.Column(db.Enum(PaymentStatus), default=PaymentStatus.PENDING, nullable=False, index=True)
    gateway_status = db.Column(db.String(50))
    failure_reason = db.Column(db.Text)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    completed_at = db.Column(db.DateTime)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Security fields
    ip_address = db.Column(db.String(45))  # Support IPv6
    user_agent = db.Column(db.Text)
    webhook_verified = db.Column(db.Boolean, default=False)
    
    def __repr__(self):
        return f'<Payment {self.reference} - {self.status.value}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'uuid': self.uuid,
            'reference': self.reference,
            'payment_method': self.payment_method,
            'gateway': self.gateway,
            'amount': float(self.amount),
            'currency': self.currency,
            'status': self.status.value,
            'created_at': self.created_at.isoformat(),
            'completed_at': self.completed_at.isoformat() if self.completed_at else None
        }


class SecurityEvent(db.Model):
    """Security event model for monitoring."""
    __tablename__ = 'security_events'
    
    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=False, index=True)
    
    event_type = db.Column(db.String(50), nullable=False, index=True)
    severity = db.Column(db.String(20), nullable=False, index=True)  # low, medium, high, critical
    description = db.Column(db.Text, nullable=False)
    source_ip = db.Column(db.String(45))
    target_system = db.Column(db.String(255))
    
    # Event data
    raw_data = db.Column(db.JSON)
    is_resolved = db.Column(db.Boolean, default=False, index=True)
    resolved_at = db.Column(db.DateTime)
    resolution_notes = db.Column(db.Text)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<SecurityEvent {self.event_type} - {self.severity}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'uuid': self.uuid,
            'event_type': self.event_type,
            'severity': self.severity,
            'description': self.description,
            'source_ip': self.source_ip,
            'target_system': self.target_system,
            'is_resolved': self.is_resolved,
            'created_at': self.created_at.isoformat()
        }


class VulnerabilityScan(db.Model):
    """Vulnerability scan results model."""
    __tablename__ = 'vulnerability_scans'
    
    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=False, index=True)
    
    scan_type = db.Column(db.String(50), nullable=False)  # web, network, host
    target = db.Column(db.String(255), nullable=False)
    status = db.Column(db.String(20), default='pending', nullable=False, index=True)
    
    # Results
    vulnerabilities_found = db.Column(db.Integer, default=0)
    critical_count = db.Column(db.Integer, default=0)
    high_count = db.Column(db.Integer, default=0)
    medium_count = db.Column(db.Integer, default=0)
    low_count = db.Column(db.Integer, default=0)
    
    scan_results = db.Column(db.JSON)
    report_url = db.Column(db.String(500))
    
    started_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    completed_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f'<VulnerabilityScan {self.scan_type} for {self.target}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'uuid': self.uuid,
            'scan_type': self.scan_type,
            'target': self.target,
            'status': self.status,
            'vulnerabilities_found': self.vulnerabilities_found,
            'critical_count': self.critical_count,
            'high_count': self.high_count,
            'medium_count': self.medium_count,
            'low_count': self.low_count,
            'started_at': self.started_at.isoformat(),
            'completed_at': self.completed_at.isoformat() if self.completed_at else None
        }


class ContactInquiry(db.Model):
    """Contact form submissions model."""
    __tablename__ = 'contact_inquiries'
    
    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    
    name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), nullable=False, index=True)
    company = db.Column(db.String(255))
    phone = db.Column(db.String(20))
    subject = db.Column(db.String(255), nullable=False)
    message = db.Column(db.Text, nullable=False)
    
    # Tracking
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.Text)
    status = db.Column(db.String(20), default='new', nullable=False, index=True)
    assigned_to = db.Column(db.String(255))
    response_sent = db.Column(db.Boolean, default=False)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<ContactInquiry from {self.email}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'uuid': self.uuid,
            'name': self.name,
            'email': self.email,
            'company': self.company,
            'subject': self.subject,
            'message': self.message,
            'status': self.status,
            'created_at': self.created_at.isoformat()
        }


class WebhookLog(db.Model):
    """Webhook logging for debugging and audit."""
    __tablename__ = 'webhook_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    
    source = db.Column(db.String(50), nullable=False, index=True)  # nowpayments, flutterwave
    event_type = db.Column(db.String(50), nullable=False)
    payment_reference = db.Column(db.String(255), index=True)
    
    # Request data
    headers = db.Column(db.JSON)
    payload = db.Column(db.JSON)
    signature = db.Column(db.String(255))
    
    # Processing results
    signature_valid = db.Column(db.Boolean)
    processing_status = db.Column(db.String(20), default='pending')
    error_message = db.Column(db.Text)
    
    ip_address = db.Column(db.String(45))
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    def __repr__(self):
        return f'<WebhookLog {self.source} - {self.event_type}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'uuid': self.uuid,
            'source': self.source,
            'event_type': self.event_type,
            'payment_reference': self.payment_reference,
            'signature_valid': self.signature_valid,
            'processing_status': self.processing_status,
            'created_at': self.created_at.isoformat()
        }