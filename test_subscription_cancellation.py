# Test Suite for Subscription Cancellation
# test_subscription_cancellation.py - Tests for cancel subscription functionality

import pytest
import json
from datetime import datetime, timedelta
from flask import Flask
from models import db, Customer, Subscription, SubscriptionPlan, SubscriptionStatus
from config import TestingConfig


@pytest.fixture
def app():
    """Create test Flask application."""
    app = Flask(__name__)
    app.config.from_object(TestingConfig)
    app.secret_key = 'test-secret'
    
    db.init_app(app)
    
    # Register dashboard blueprint for testing
    from routes.dashboard import dashboard_bp
    app.register_blueprint(dashboard_bp, url_prefix='/dashboard')
    
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()


@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()


@pytest.fixture
def sample_customer_with_subscription(app):
    """Create sample customer with active subscription."""
    with app.app_context():
        customer = Customer(
            email='test@example.com',
            name='Test Customer',
            company='Test Company',
            phone='+1234567890'
        )
        db.session.add(customer)
        db.session.flush()  # Get customer ID
        
        subscription = Subscription(
            customer_id=customer.id,
            plan=SubscriptionPlan.PROFESSIONAL,
            status=SubscriptionStatus.ACTIVE,
            amount=199.00,
            currency='USD',
            billing_cycle='monthly',
            ends_at=datetime.utcnow() + timedelta(days=30)
        )
        db.session.add(subscription)
        db.session.commit()
        
        # Return IDs instead of objects to avoid detached instance issues
        return customer.id, subscription.id


class TestSubscriptionCancellation:
    """Test subscription cancellation functionality."""
    
    def test_cancel_subscription_unauthenticated(self, client):
        """Test cancellation requires authentication."""
        response = client.post('/dashboard/subscription/cancel', 
                              json={'reason': 'Test reason'})
        assert response.status_code == 401
        assert 'Not authenticated' in response.get_json()['error']
    
    def test_cancel_subscription_success(self, client, sample_customer_with_subscription):
        """Test successful subscription cancellation."""
        customer_id, subscription_id = sample_customer_with_subscription
        
        # Login the customer
        with client.session_transaction() as sess:
            sess['customer_id'] = customer_id
            sess['customer_email'] = 'test@example.com'
        
        # Cancel subscription
        response = client.post('/dashboard/subscription/cancel',
                              json={'reason': 'Too expensive for my current needs'})
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert 'cancelled successfully' in data['message']
        
        # Verify subscription is cancelled in database
        with client.application.app_context():
            updated_subscription = Subscription.query.get(subscription_id)
            assert updated_subscription.status == SubscriptionStatus.CANCELLED
            assert updated_subscription.cancelled_at is not None
            assert updated_subscription.cancellation_reason == 'Too expensive for my current needs'
    
    def test_cancel_subscription_missing_reason(self, client, sample_customer_with_subscription):
        """Test cancellation requires a reason."""
        customer_id, subscription_id = sample_customer_with_subscription
        
        with client.session_transaction() as sess:
            sess['customer_id'] = customer_id
        
        response = client.post('/dashboard/subscription/cancel', json={})
        assert response.status_code == 400
        assert 'Cancellation reason is required' in response.get_json()['error']
    
    def test_cancel_subscription_reason_too_long(self, client, sample_customer_with_subscription):
        """Test cancellation reason length validation."""
        customer_id, subscription_id = sample_customer_with_subscription
        
        with client.session_transaction() as sess:
            sess['customer_id'] = customer_id
        
        long_reason = 'x' * 501  # Over 500 character limit
        response = client.post('/dashboard/subscription/cancel',
                              json={'reason': long_reason})
        assert response.status_code == 400
        assert 'must be less than 500 characters' in response.get_json()['error']
    
    def test_cancel_no_active_subscription(self, client, app):
        """Test cancellation when customer has no active subscription."""
        with app.app_context():
            customer = Customer(
                email='nosubscription@example.com',
                name='No Subscription Customer'
            )
            db.session.add(customer)
            db.session.commit()
        
            with client.session_transaction() as sess:
                sess['customer_id'] = customer.id
        
            response = client.post('/dashboard/subscription/cancel',
                                  json={'reason': 'Test reason'})
            assert response.status_code == 404
            assert 'No active subscription found' in response.get_json()['error']
    
    def test_reactivate_subscription_success(self, client, sample_customer_with_subscription):
        """Test successful subscription reactivation."""
        customer_id, subscription_id = sample_customer_with_subscription
        
        # First cancel the subscription
        with client.application.app_context():
            subscription = Subscription.query.get(subscription_id)
            subscription.cancel('Test cancellation')
        
        with client.session_transaction() as sess:
            sess['customer_id'] = customer_id
        
        # Reactivate subscription
        response = client.post('/dashboard/subscription/reactivate')
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert 'reactivated successfully' in data['message']
        
        # Verify subscription is reactivated in database
        with client.application.app_context():
            updated_subscription = Subscription.query.get(subscription_id)
            assert updated_subscription.status == SubscriptionStatus.ACTIVE
            assert updated_subscription.cancelled_at is None
            assert updated_subscription.cancellation_reason is None
    
    def test_reactivate_no_cancelled_subscription(self, client, sample_customer_with_subscription):
        """Test reactivation when customer has no cancelled subscription."""
        customer_id, subscription_id = sample_customer_with_subscription
        
        with client.session_transaction() as sess:
            sess['customer_id'] = customer_id
        
        # Try to reactivate when subscription is still active
        response = client.post('/dashboard/subscription/reactivate')
        assert response.status_code == 404
        assert 'No cancelled subscription found' in response.get_json()['error']
    
    def test_cancel_subscription_page_loads(self, client, sample_customer_with_subscription):
        """Test that the cancellation page loads correctly."""
        customer_id, subscription_id = sample_customer_with_subscription
        
        with client.session_transaction() as sess:
            sess['customer_id'] = customer_id
        
        response = client.get('/dashboard/subscription/cancel')
        assert response.status_code == 200
        assert b'Cancel Subscription' in response.data
        assert b'AstraFabric' in response.data
        assert b'Professional' in response.data  # Plan name
    
    def test_dashboard_shows_cancel_button_for_active_subscription(self, client, sample_customer_with_subscription):
        """Test that dashboard shows cancel button for active subscriptions."""
        customer_id, subscription_id = sample_customer_with_subscription
        
        with client.session_transaction() as sess:
            sess['customer_id'] = customer_id
        
        response = client.get('/dashboard/')
        assert response.status_code == 200
        assert b'Cancel' in response.data
        assert b'btn-outline-danger' in response.data
    
    def test_dashboard_shows_reactivate_button_for_cancelled_subscription(self, client, sample_customer_with_subscription):
        """Test that dashboard shows reactivate button for cancelled subscriptions."""
        customer_id, subscription_id = sample_customer_with_subscription
        
        # Cancel the subscription first
        with client.application.app_context():
            subscription = Subscription.query.get(subscription_id)
            subscription.cancel('Test cancellation')
        
        with client.session_transaction() as sess:
            sess['customer_id'] = customer_id
        
        response = client.get('/dashboard/')
        assert response.status_code == 200
        assert b'Reactivate' in response.data
        assert b'btn-success' in response.data
        assert b'Cancelled' in response.data