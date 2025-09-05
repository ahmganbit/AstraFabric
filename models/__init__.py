from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from enum import Enum
import uuid
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, ForeignKey, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

db = SQLAlchemy()

class PaymentStatus(Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"

class SubscriptionPlan(Enum):
    ESSENTIAL = "essential"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"

class SubscriptionStatus(Enum):
    ACTIVE = "active"
    CANCELLED = "cancelled"
    SUSPENDED = "suspended"
    EXPIRED = "expired"

class Customer(db.Model):
    __tablename__ = 'customers'
    
    id = Column(Integer, primary_key=True)
    uuid = Column(UUID(as_uuid=True), unique=True, default=uuid.uuid4, nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    company = Column(String(255))
    phone = Column(String(20))
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    subscriptions = relationship("Subscription", back_populates="customer", lazy="dynamic")
    payments = relationship("Payment", back_populates="customer", lazy="dynamic")
    security_events = relationship("SecurityEvent", back_populates="customer", lazy="dynamic")
    vulnerability_scans = relationship("VulnerabilityScan", back_populates="customer", lazy="dynamic")
    
    def __repr__(self):
        return f'<Customer {self.email}>'

class Subscription(db.Model):
    __tablename__ = 'subscriptions'
    
    id = Column(Integer, primary_key=True)
    customer_id = Column(Integer, ForeignKey('customers.id'), nullable=False)
    plan = Column(SQLEnum(SubscriptionPlan), nullable=False)
    status = Column(SQLEnum(SubscriptionStatus), default=SubscriptionStatus.ACTIVE, nullable=False)
    amount = Column(Float(precision=2), nullable=False)
    currency = Column(String(3), default='USD', nullable=False)
    billing_cycle = Column(String(20), default='monthly', nullable=False)  # monthly, yearly
    started_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    ends_at = Column(DateTime)
    cancelled_at = Column(DateTime)
    cancellation_reason = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    customer = relationship("Customer", back_populates="subscriptions")
    
    def __repr__(self):
        return f'<Subscription {self.plan.value} for {self.customer.email if self.customer else self.customer_id}>'
    
    def cancel(self, reason=None):
        """Cancel the subscription."""
        self.status = SubscriptionStatus.CANCELLED
        self.cancelled_at = datetime.utcnow()
        if reason:
            self.cancellation_reason = reason
        db.session.commit()
    
    @property
    def is_active(self):
        return self.status == SubscriptionStatus.ACTIVE
    
    @property
    def is_cancelled(self):
        return self.status == SubscriptionStatus.CANCELLED

class Payment(db.Model):
    __tablename__ = 'payments'
    
    id = Column(Integer, primary_key=True)
    customer_id = Column(Integer, ForeignKey('customers.id'), nullable=False)
    subscription_id = Column(Integer, ForeignKey('subscriptions.id'))
    payment_method = Column(String(50), nullable=False)  # card, crypto, bank_transfer
    gateway = Column(String(50), nullable=False)  # flutterwave, nowpayments
    reference = Column(String(255), unique=True, nullable=False)
    gateway_reference = Column(String(255))
    amount = Column(Float(precision=2), nullable=False)
    currency = Column(String(3), default='USD', nullable=False)
    status = Column(SQLEnum(PaymentStatus), default=PaymentStatus.PENDING, nullable=False)
    gateway_metadata = Column(Text)  # JSON metadata from gateway
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    customer = relationship("Customer", back_populates="payments")
    subscription = relationship("Subscription")
    
    def __repr__(self):
        return f'<Payment {self.reference} - {self.status.value}>'

class ContactInquiry(db.Model):
    __tablename__ = 'contact_inquiries'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False)
    company = Column(String(255))
    phone = Column(String(20))
    subject = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    ip_address = Column(String(45))
    user_agent = Column(Text)
    status = Column(String(20), default='new', nullable=False)  # new, contacted, closed
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f'<ContactInquiry from {self.email}>'

class SecurityEvent(db.Model):
    __tablename__ = 'security_events'
    
    id = Column(Integer, primary_key=True)
    customer_id = Column(Integer, ForeignKey('customers.id'), nullable=False)
    event_type = Column(String(50), nullable=False)  # malware_detected, failed_login, etc.
    severity = Column(String(20), nullable=False)  # low, medium, high, critical
    description = Column(Text, nullable=False)
    source_ip = Column(String(45))
    target_system = Column(String(255))
    event_metadata = Column(Text)  # JSON metadata
    resolved = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    customer = relationship("Customer", back_populates="security_events")
    
    def __repr__(self):
        return f'<SecurityEvent {self.event_type} - {self.severity}>'

class VulnerabilityScan(db.Model):
    __tablename__ = 'vulnerability_scans'
    
    id = Column(Integer, primary_key=True)
    customer_id = Column(Integer, ForeignKey('customers.id'), nullable=False)
    scan_type = Column(String(50), nullable=False)  # network, web_app, infrastructure
    target = Column(String(255), nullable=False)  # IP, domain, etc.
    status = Column(String(20), default='pending', nullable=False)  # pending, running, completed, failed
    vulnerabilities_found = Column(Integer, default=0)
    critical_count = Column(Integer, default=0)
    high_count = Column(Integer, default=0)
    medium_count = Column(Integer, default=0)
    low_count = Column(Integer, default=0)
    scan_results = Column(Text)  # JSON results
    started_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime)
    
    # Relationships
    customer = relationship("Customer", back_populates="vulnerability_scans")
    
    def __repr__(self):
        return f'<VulnerabilityScan {self.scan_type} for {self.target}>'

class WebhookLog(db.Model):
    __tablename__ = 'webhook_logs'
    
    id = Column(Integer, primary_key=True)
    source = Column(String(50), nullable=False)  # flutterwave, nowpayments
    event_type = Column(String(100), nullable=False)
    reference = Column(String(255))
    payload = Column(Text, nullable=False)  # Raw webhook payload
    processed = Column(Boolean, default=False, nullable=False)
    success = Column(Boolean, default=False, nullable=False)
    error_message = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    processed_at = Column(DateTime)
    
    def __repr__(self):
        return f'<WebhookLog {self.source} - {self.event_type}>'
