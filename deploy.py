# Deployment Helper Script
# deploy.py - Handles database initialization and migrations for Render

import os
import sys
from app_factory import create_app, create_tables, init_sample_data
from config import config


def deploy():
    """Initialize application for production deployment."""
    
    print("🚀 Starting AstraFabric deployment...")
    
    # Create app with production config
    app = create_app('production')
    
    with app.app_context():
        try:
            # Create database tables
            print("📊 Creating database tables...")
            create_tables(app)
            
            # Initialize sample data if needed
            print("🔧 Initializing application data...")
            init_sample_data(app)
            
            print("✅ Deployment completed successfully!")
            return True
            
        except Exception as e:
            print(f"❌ Deployment failed: {e}")
            return False


if __name__ == '__main__':
    if deploy():
        sys.exit(0)
    else:
        sys.exit(1)
