# Database Migration Script
# migrate_db.py - Migrate from SQLite to PostgreSQL with SQLAlchemy

import os
import sqlite3
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from models import db, Customer, Subscription, Payment, SecurityEvent, VulnerabilityScan, ContactInquiry, WebhookLog
from config import config
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DatabaseMigrator:
    """Handle database migration from SQLite to PostgreSQL."""
    
    def __init__(self, sqlite_path='astrafabric_secure.db'):
        self.sqlite_path = sqlite_path
        self.sqlite_conn = None
        self.pg_engine = None
        self.pg_session = None
    
    def connect_sqlite(self):
        """Connect to SQLite database."""
        if os.path.exists(self.sqlite_path):
            self.sqlite_conn = sqlite3.connect(self.sqlite_path)
            self.sqlite_conn.row_factory = sqlite3.Row
            logger.info(f"Connected to SQLite database: {self.sqlite_path}")
            return True
        else:
            logger.error(f"SQLite database not found: {self.sqlite_path}")
            return False
    
    def connect_postgresql(self, database_url):
        """Connect to PostgreSQL database."""
        try:
            self.pg_engine = create_engine(database_url)
            Session = sessionmaker(bind=self.pg_engine)
            self.pg_session = Session()
            logger.info("Connected to PostgreSQL database")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to PostgreSQL: {e}")
            return False
    
    def create_tables(self):
        """Create all tables in PostgreSQL."""
        try:
            db.metadata.create_all(self.pg_engine)
            logger.info("Created all tables in PostgreSQL")
            return True
        except Exception as e:
            logger.error(f"Failed to create tables: {e}")
            return False
    
    def migrate_customers(self):
        """Migrate customers data."""
        try:
            cursor = self.sqlite_conn.cursor()
            cursor.execute("SELECT * FROM customers")
            customers = cursor.fetchall()
            
            for row in customers:
                customer = Customer(
                    email=row['email'],
                    name=row['name'],
                    company=row.get('company'),
                    phone=row.get('phone'),
                    created_at=row.get('created_at'),
                    is_active=bool(row.get('is_active', True))
                )
                self.pg_session.add(customer)
            
            self.pg_session.commit()
            logger.info(f"Migrated {len(customers)} customers")
            return True
        except Exception as e:
            logger.error(f"Failed to migrate customers: {e}")
            self.pg_session.rollback()
            return False
    
    def migrate_subscriptions(self):
        """Migrate subscriptions data."""
        try:
            cursor = self.sqlite_conn.cursor()
            cursor.execute("""
                SELECT s.*, c.email as customer_email 
                FROM subscriptions s 
                LEFT JOIN customers c ON s.customer_id = c.id
            """)
            subscriptions = cursor.fetchall()
            
            for row in subscriptions:
                # Find customer by email
                customer = self.pg_session.query(Customer).filter_by(email=row['customer_email']).first()
                if customer:
                    subscription = Subscription(
                        customer_id=customer.id,
                        plan=row['plan'],
                        status=row.get('status', 'active'),
                        start_date=row.get('start_date'),
                        end_date=row.get('end_date'),
                        billing_cycle=row.get('billing_cycle', 'monthly'),
                        amount=row.get('amount', 0),
                        currency=row.get('currency', 'USD')
                    )
                    self.pg_session.add(subscription)
            
            self.pg_session.commit()
            logger.info(f"Migrated {len(subscriptions)} subscriptions")
            return True
        except Exception as e:
            logger.error(f"Failed to migrate subscriptions: {e}")
            self.pg_session.rollback()
            return False
    
    def migrate_payments(self):
        """Migrate payments data."""
        try:
            cursor = self.sqlite_conn.cursor()
            cursor.execute("""
                SELECT p.*, c.email as customer_email 
                FROM transactions p 
                LEFT JOIN customers c ON p.customer_id = c.id
            """)
            payments = cursor.fetchall()
            
            for row in payments:
                # Find customer by email
                customer = self.pg_session.query(Customer).filter_by(email=row['customer_email']).first()
                if customer:
                    payment = Payment(
                        customer_id=customer.id,
                        payment_method=row.get('payment_method', 'unknown'),
                        gateway=row.get('gateway', 'unknown'),
                        gateway_transaction_id=row.get('gateway_transaction_id'),
                        reference=row.get('reference', f"legacy_{row['id']}"),
                        amount=row.get('amount', 0),
                        currency=row.get('currency', 'USD'),
                        status=row.get('status', 'pending'),
                        created_at=row.get('created_at'),
                        completed_at=row.get('completed_at'),
                        ip_address=row.get('ip_address'),
                        webhook_verified=bool(row.get('webhook_verified', False))
                    )
                    self.pg_session.add(payment)
            
            self.pg_session.commit()
            logger.info(f"Migrated {len(payments)} payments")
            return True
        except Exception as e:
            logger.error(f"Failed to migrate payments: {e}")
            self.pg_session.rollback()
            return False
    
    def migrate_contact_inquiries(self):
        """Migrate contact inquiries."""
        try:
            cursor = self.sqlite_conn.cursor()
            cursor.execute("SELECT * FROM contact_inquiries")
            inquiries = cursor.fetchall()
            
            for row in inquiries:
                inquiry = ContactInquiry(
                    name=row['name'],
                    email=row['email'],
                    company=row.get('company'),
                    phone=row.get('phone'),
                    subject=row.get('subject', 'Legacy Inquiry'),
                    message=row['message'],
                    ip_address=row.get('ip_address'),
                    status=row.get('status', 'new'),
                    created_at=row.get('created_at')
                )
                self.pg_session.add(inquiry)
            
            self.pg_session.commit()
            logger.info(f"Migrated {len(inquiries)} contact inquiries")
            return True
        except Exception as e:
            logger.error(f"Failed to migrate contact inquiries: {e}")
            self.pg_session.rollback()
            return False
    
    def run_migration(self, database_url):
        """Run complete migration process."""
        logger.info("Starting database migration...")
        
        # Connect to databases
        if not self.connect_sqlite():
            return False
        
        if not self.connect_postgresql(database_url):
            return False
        
        # Create tables
        if not self.create_tables():
            return False
        
        # Migrate data
        success = True
        success &= self.migrate_customers()
        success &= self.migrate_subscriptions() 
        success &= self.migrate_payments()
        success &= self.migrate_contact_inquiries()
        
        # Close connections
        if self.sqlite_conn:
            self.sqlite_conn.close()
        if self.pg_session:
            self.pg_session.close()
        
        if success:
            logger.info("Database migration completed successfully!")
        else:
            logger.error("Database migration failed!")
        
        return success


def main():
    """Main migration function."""
    # Get database URL from environment or use default
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        logger.error("DATABASE_URL environment variable is required")
        return False
    
    migrator = DatabaseMigrator()
    return migrator.run_migration(database_url)


if __name__ == '__main__':
    main()
