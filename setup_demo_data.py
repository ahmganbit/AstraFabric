# Demo Data Setup Script
# setup_demo_data.py - Creates demo subscription data for testing cancellation functionality

from app_factory import create_app
from models import db, Customer, Subscription, SubscriptionPlan, SubscriptionStatus
from datetime import datetime, timedelta

def setup_demo_data():
    """Set up demo data for testing subscription cancellation."""
    app = create_app('development')
    
    with app.app_context():
        # Check if demo customer already exists
        demo_customer = Customer.query.filter_by(email='demo@astrafabric.com').first()
        if demo_customer:
            print(f"Demo customer already exists: {demo_customer.email}")
            return demo_customer
        
        # Create demo customer
        demo_customer = Customer(
            email='demo@astrafabric.com',
            name='Demo Customer',
            company='Demo Security Company',
            phone='+1-234-567-8900'
        )
        db.session.add(demo_customer)
        db.session.flush()  # Get the ID
        
        # Create active subscription
        subscription = Subscription(
            customer_id=demo_customer.id,
            plan=SubscriptionPlan.PROFESSIONAL,
            status=SubscriptionStatus.ACTIVE,
            amount=199.00,
            currency='USD',
            billing_cycle='monthly',
            ends_at=datetime.utcnow() + timedelta(days=30)  # Valid for 30 more days
        )
        db.session.add(subscription)
        
        db.session.commit()
        
        print(f"Created demo customer: {demo_customer.email}")
        print(f"Created active subscription: {subscription.plan.value} - ${subscription.amount}/{subscription.billing_cycle}")
        print(f"Customer ID: {demo_customer.id}")
        print(f"Subscription ID: {subscription.id}")
        
        return demo_customer

if __name__ == '__main__':
    setup_demo_data()