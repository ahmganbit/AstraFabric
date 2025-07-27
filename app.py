# AstraFabric Enterprise Security Platform
# Complete payment-enabled platform with Contact Us page

from flask import Flask, render_template_string, request, jsonify, redirect, url_for, session
import os
import sqlite3
import hashlib
import json
import requests
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Configuration
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'astrafabric-secure-2024-enterprise')

# WhatsApp contact number
WHATSAPP_NUMBER = '+234 908 482 4238'

# Payment Gateway Configuration
FLUTTERWAVE_PUBLIC_KEY = os.environ.get('FLUTTERWAVE_PUBLIC_KEY')
FLUTTERWAVE_SECRET_KEY = os.environ.get('FLUTTERWAVE_SECRET_KEY')
NOWPAYMENTS_API_KEY = os.environ.get('NOWPAYMENTS_API_KEY')
NOWPAYMENTS_IPN_SECRET = os.environ.get('NOWPAYMENTS_IPN_SECRET')

# Admin Configuration
ADMIN_PASSWORD_HASH = hashlib.sha256("astrafabric2024!secure".encode()).hexdigest()

# Database initialization
def init_db():
    conn = sqlite3.connect('astrafabric.db')
    c = conn.cursor()
    
    # Subscriptions table
    c.execute('''CREATE TABLE IF NOT EXISTS subscriptions
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  email TEXT NOT NULL,
                  plan TEXT NOT NULL,
                  amount REAL NOT NULL,
                  currency TEXT DEFAULT 'USD',
                  payment_method TEXT,
                  payment_id TEXT,
                  status TEXT DEFAULT 'active',
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    
    # Admin logs table
    c.execute('''CREATE TABLE IF NOT EXISTS admin_logs
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  action TEXT NOT NULL,
                  details TEXT,
                  timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    
    conn.commit()
    conn.close()

# Initialize database on startup
init_db()

@app.route('/')
def home():
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <title>AstraFabric - Enterprise Security Platform</title>
        <link rel="icon" type="image/x-icon" href="/favicon.ico">
        <style>
            body { 
                font-family: Arial, sans-serif; 
                margin: 0; 
                background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
                color: white; 
                min-height: 100vh;
            }
            
            .header { 
                background: linear-gradient(45deg, #1e293b, #334155); 
                padding: 20px 0; 
                text-align: center;
                border-bottom: 1px solid rgba(59, 130, 246, 0.3);
            }
            
            .container { 
                max-width: 1200px; 
                margin: 0 auto; 
                padding: 50px 20px;
            }
            
            h1 {
                font-size: 4em;
                background: linear-gradient(45deg, #3b82f6, #8b5cf6);
                background-clip: text;
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                margin-bottom: 30px;
                text-align: center;
            }
            
            .hero-section {
                text-align: center;
                padding: 80px 20px;
                background: linear-gradient(145deg, rgba(30, 41, 59, 0.8), rgba(51, 65, 85, 0.6));
                border-radius: 20px;
                margin: 40px 0;
                border: 1px solid rgba(59, 130, 246, 0.3);
            }
            
            .features-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
                gap: 30px;
                margin: 50px 0;
            }
            
            .feature-card {
                background: linear-gradient(145deg, rgba(30, 41, 59, 0.8), rgba(51, 65, 85, 0.6));
                padding: 30px;
                border-radius: 15px;
                border: 1px solid rgba(59, 130, 246, 0.3);
                transform: perspective(1000px) rotateX(0deg);
                transition: all 0.4s ease;
            }
            
            .feature-card:hover {
                transform: perspective(1000px) rotateX(5deg) translateZ(10px);
                border-color: rgba(59, 130, 246, 0.6);
                box-shadow: 0 20px 40px rgba(59, 130, 246, 0.2);
            }
            
            .btn {
                background: linear-gradient(45deg, #3b82f6, #1e40af);
                color: white;
                padding: 15px 30px;
                border: none;
                border-radius: 10px;
                text-decoration: none;
                font-weight: bold;
                font-size: 1.1em;
                display: inline-block;
                margin: 10px;
                transition: all 0.3s ease;
            }
            
            .btn:hover {
                background: linear-gradient(45deg, #2563eb, #1d4ed8);
                transform: translateY(-2px);
                box-shadow: 0 10px 20px rgba(59, 130, 246, 0.3);
            }
            
            .nav-buttons {
                text-align: center;
                margin: 40px 0;
            }
            
            .pricing-highlight {
                background: linear-gradient(145deg, rgba(59, 130, 246, 0.2), rgba(37, 99, 235, 0.2));
                padding: 40px;
                border-radius: 20px;
                text-align: center;
                margin: 50px 0;
                border: 1px solid rgba(59, 130, 246, 0.4);
            }
        </style>
    </head>
    <body>
        <div class="header">
            <h2>🛡️ AstraFabric Enterprise Security</h2>
            <p>Autonomous Security Monitoring for Fortune 500 Companies</p>
        </div>
        
        <div class="container">
            <div class="hero-section">
                <h1>🚀 Enterprise Security Redefined</h1>
                <p style="font-size: 1.4em; margin: 30px 0;">24/7 Autonomous Security Monitoring with AI-Powered Threat Detection</p>
                <p style="font-size: 1.2em; color: #cbd5e1;">Trusted by Fortune 500 companies worldwide</p>
                
                <div class="nav-buttons">
                    <a href="/subscribe" class="btn">💳 Subscribe Now</a>
                    <a href="/client" class="btn">🔒 Client Portal</a>
                    <a href="/contact" class="btn">📞 Contact Us</a>
                    <a href="/reports" class="btn">📊 Reports</a>
                    <a href="/docs" class="btn">📖 API Docs</a>
                </div>
            </div>
            
            <div class="features-grid">
                <div class="feature-card">
                    <h3 style="color: #3b82f6;">🛡️ Autonomous Monitoring</h3>
                    <p>24/7 automated security monitoring with zero human intervention required. Our AI continuously scans for threats and vulnerabilities.</p>
                </div>
                
                <div class="feature-card">
                    <h3 style="color: #10b981;">🎯 Real-Time Alerts</h3>
                    <p>Instant notifications for critical security events. Get alerts via email, SMS, and integrated dashboards within seconds.</p>
                </div>
                
                <div class="feature-card">
                    <h3 style="color: #8b5cf6;">📊 Executive Reports</h3>
                    <p>Comprehensive security reports designed for C-level executives. Track metrics, compliance, and ROI effortlessly.</p>
                </div>
                
                <div class="feature-card">
                    <h3 style="color: #f59e0b;">🌐 Global Coverage</h3>
                    <p>Monitor assets across multiple continents with our distributed monitoring network. No blind spots in your security posture.</p>
                </div>
            </div>
            
            <div class="pricing-highlight">
                <h2 style="color: #3b82f6;">💰 Enterprise Pricing</h2>
                <p style="font-size: 1.3em;">From <strong>$199/month</strong> to <strong>$799/month</strong></p>
                <p>Competing directly with CrowdStrike and IBM QRadar at fraction of the cost</p>
                <a href="/subscribe" class="btn" style="font-size: 1.2em; padding: 20px 40px;">Start Your Enterprise Security Journey</a>
            </div>
        </div>
    </body>
    </html>
    ''')

@app.route('/contact')
def contact_us():
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Contact Us - AstraFabric Enterprise Security</title>
        <style>
            body { 
                font-family: Arial, sans-serif; 
                margin: 0; 
                background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
                color: white; 
                min-height: 100vh;
            }
            
            .header { 
                background: linear-gradient(45deg, #1e293b, #334155); 
                padding: 20px 0; 
                text-align: center;
                border-bottom: 1px solid rgba(59, 130, 246, 0.3);
            }
            
            .container { 
                max-width: 1000px; 
                margin: 0 auto; 
                padding: 50px 20px;
            }
            
            h1 {
                font-size: 3.5em;
                background: linear-gradient(45deg, #3b82f6, #8b5cf6);
                background-clip: text;
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                margin-bottom: 30px;
                text-align: center;
            }
            
            .contact-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(450px, 1fr));
                gap: 50px;
                margin: 50px 0;
            }
            
            .contact-card {
                background: linear-gradient(145deg, rgba(30, 41, 59, 0.8), rgba(51, 65, 85, 0.6));
                padding: 40px;
                border-radius: 20px;
                border: 1px solid rgba(59, 130, 246, 0.3);
            }
            
            .contact-method {
                display: flex;
                align-items: center;
                margin: 25px 0;
                padding: 20px;
                background: rgba(15, 23, 42, 0.6);
                border-radius: 15px;
                border-left: 4px solid #3b82f6;
            }
            
            .contact-icon {
                font-size: 2.5em;
                margin-right: 20px;
                min-width: 60px;
            }
            
            .contact-info h3 {
                margin: 0 0 10px 0;
                color: #3b82f6;
                font-size: 1.4em;
            }
            
            .contact-info p {
                margin: 5px 0;
                color: #cbd5e1;
                line-height: 1.6;
            }
            
            .contact-info a {
                color: #60a5fa;
                text-decoration: none;
                font-weight: bold;
            }
            
            .whatsapp-highlight {
                background: linear-gradient(45deg, #25d366, #20b358);
                border-left-color: #25d366;
            }
            
            .btn {
                background: linear-gradient(45deg, #3b82f6, #1e40af);
                color: white;
                padding: 15px 30px;
                border: none;
                border-radius: 10px;
                text-decoration: none;
                font-weight: bold;
                font-size: 1.1em;
                display: inline-block;
                margin: 10px;
                transition: all 0.3s ease;
            }
            
            .nav-links {
                text-align: center;
                margin: 40px 0;
            }
            
            .nav-links a {
                color: #60a5fa;
                text-decoration: none;
                margin: 0 20px;
                font-weight: bold;
            }
        </style>
    </head>
    <body>
        <div class="header">
            <h2>🛡️ AstraFabric Enterprise Security</h2>
            <div class="nav-links">
                <a href="/">🏠 Home</a>
                <a href="/subscribe">💳 Subscribe</a>
                <a href="/client">🔒 Client Portal</a>
            </div>
        </div>
        
        <div class="container">
            <h1>📞 Contact Us</h1>
            
            <div class="contact-grid">
                <div class="contact-card">
                    <h2 style="color: #3b82f6; text-align: center;">🚀 Get In Touch</h2>
                    
                    <div class="contact-method">
                        <div class="contact-icon">✉️</div>
                        <div class="contact-info">
                            <h3>Email Support</h3>
                            <p><a href="mailto:contact@astrafabric.com">contact@astrafabric.com</a></p>
                            <p>General inquiries and support</p>
                        </div>
                    </div>
                    
                    <div class="contact-method whatsapp-highlight">
                        <div class="contact-icon">💬</div>
                        <div class="contact-info">
                            <h3>WhatsApp Support</h3>
                            <p><a href="https://wa.me/2349084824238">''' + WHATSAPP_NUMBER + '''</a></p>
                            <p>Instant support and consultations</p>
                        </div>
                    </div>
                </div>
                
                <div class="contact-card">
                    <h2 style="color: #3b82f6; text-align: center;">🏢 Enterprise Sales</h2>
                    
                    <div class="contact-method">
                        <div class="contact-icon">💼</div>
                        <div class="contact-info">
                            <h3>Enterprise Inquiries</h3>
                            <p><a href="mailto:enterprise@astrafabric.com">enterprise@astrafabric.com</a></p>
                            <p>Fortune 500 partnerships</p>
                        </div>
                    </div>
                    
                    <div class="contact-method">
                        <div class="contact-icon">🔒</div>
                        <div class="contact-info">
                            <h3>Security Consultations</h3>
                            <p><a href="https://wa.me/2349084824238">WhatsApp: ''' + WHATSAPP_NUMBER + '''</a></p>
                            <p>Free security assessments</p>
                        </div>
                    </div>
                </div>
            </div>
            
            <div style="text-align: center; margin: 60px 0;">
                <a href="/subscribe" class="btn">💳 Subscribe Now</a>
                <a href="https://wa.me/2349084824238" class="btn" style="background: linear-gradient(45deg, #25d366, #20b358);">💬 WhatsApp Demo</a>
            </div>
        </div>
    </body>
    </html>
    ''')

@app.route('/subscribe')
def subscribe():
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Subscribe - AstraFabric Enterprise Security</title>
        <style>
            body { 
                font-family: Arial, sans-serif; 
                margin: 0; 
                background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
                color: white; 
                min-height: 100vh;
            }
            
            .container { 
                max-width: 1200px; 
                margin: 0 auto; 
                padding: 50px 20px;
            }
            
            .pricing-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
                gap: 30px;
                margin: 50px 0;
            }
            
            .pricing-card {
                background: linear-gradient(145deg, rgba(30, 41, 59, 0.8), rgba(51, 65, 85, 0.6));
                padding: 40px;
                border-radius: 20px;
                border: 1px solid rgba(59, 130, 246, 0.3);
                text-align: center;
                transition: all 0.4s ease;
            }
            
            .pricing-card:hover {
                transform: translateY(-10px);
                border-color: rgba(59, 130, 246, 0.6);
                box-shadow: 0 20px 40px rgba(59, 130, 246, 0.2);
            }
            
            .price {
                font-size: 3em;
                font-weight: bold;
                color: #3b82f6;
                margin: 20px 0;
            }
            
            .btn {
                background: linear-gradient(45deg, #3b82f6, #1e40af);
                color: white;
                padding: 15px 30px;
                border: none;
                border-radius: 10px;
                text-decoration: none;
                font-weight: bold;
                font-size: 1.1em;
                display: inline-block;
                margin: 20px 10px;
                transition: all 0.3s ease;
                cursor: pointer;
            }
            
            .btn:hover {
                background: linear-gradient(45deg, #2563eb, #1d4ed8);
                transform: translateY(-2px);
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1 style="text-align: center; font-size: 3.5em; background: linear-gradient(45deg, #3b82f6, #8b5cf6); background-clip: text; -webkit-background-clip: text; -webkit-text-fill-color: transparent;">💳 Choose Your Plan</h1>
            
            <div class="pricing-grid">
                <div class="pricing-card">
                    <h3 style="color: #10b981; font-size: 2em;">💼 Essential Autopilot</h3>
                    <div class="price">$199<span style="font-size: 0.4em;">/month</span></div>
                    <ul style="text-align: left; margin: 30px 0;">
                        <li>✅ 24/7 Autonomous Monitoring</li>
                        <li>✅ Real-time Security Alerts</li>
                        <li>✅ Basic Vulnerability Scanning</li>
                        <li>✅ Email Support</li>
                        <li>✅ Monthly Security Reports</li>
                    </ul>
                    <button class="btn" onclick="subscribe('essential', 199)">Subscribe Now</button>
                </div>
                
                <div class="pricing-card" style="border-color: #f59e0b; transform: scale(1.05);">
                    <h3 style="color: #f59e0b; font-size: 2em;">🚀 Professional Autopilot</h3>
                    <div class="price" style="color: #f59e0b;">$399<span style="font-size: 0.4em;">/month</span></div>
                    <div style="background: #f59e0b; color: #000; padding: 5px 15px; border-radius: 20px; font-weight: bold; margin: 10px 0;">MOST POPULAR</div>
                    <ul style="text-align: left; margin: 30px 0;">
                        <li>✅ Everything in Essential</li>
                        <li>✅ Advanced Threat Detection</li>
                        <li>✅ API Access</li>
                        <li>✅ WhatsApp Support</li>
                        <li>✅ Weekly Executive Reports</li>
                        <li>✅ Custom Integrations</li>
                    </ul>
                    <button class="btn" style="background: linear-gradient(45deg, #f59e0b, #d97706);" onclick="subscribe('professional', 399)">Subscribe Now</button>
                </div>
                
                <div class="pricing-card">
                    <h3 style="color: #8b5cf6; font-size: 2em;">🏆 Enterprise Autopilot</h3>
                    <div class="price" style="color: #8b5cf6;">$799<span style="font-size: 0.4em;">/month</span></div>
                    <ul style="text-align: left; margin: 30px 0;">
                        <li>✅ Everything in Professional</li>
                        <li>✅ Dedicated Account Manager</li>
                        <li>✅ Custom Security Policies</li>
                        <li>✅ Priority Support</li>
                        <li>✅ Daily Security Briefings</li>
                        <li>✅ On-site Consultations</li>
                    </ul>
                    <button class="btn" style="background: linear-gradient(45deg, #8b5cf6, #7c3aed);" onclick="subscribe('enterprise', 799)">Subscribe Now</button>
                </div>
            </div>
            
            <div style="text-align: center; margin: 50px 0;">
                <p style="font-size: 1.2em;">💬 Need a custom plan? <a href="https://wa.me/2349084824238" style="color: #3b82f6;">WhatsApp us</a> for enterprise pricing</p>
                <a href="/" style="color: #60a5fa; text-decoration: none;">← Back to Home</a>
            </div>
        </div>
        
        <script>
            function subscribe(plan, amount) {
                // Payment integration will be handled here
                window.location.href = '/payment/process?plan=' + plan + '&amount=' + amount;
            }
        </script>
    </body>
    </html>
    ''')

@app.route('/payment/process')
def payment_process():
    plan = request.args.get('plan', 'essential')
    amount = request.args.get('amount', '199')
    
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Payment Processing - AstraFabric</title>
        <style>
            body { 
                font-family: Arial, sans-serif; 
                margin: 0; 
                background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
                color: white; 
                min-height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
            }
            
            .payment-container {
                background: linear-gradient(145deg, rgba(30, 41, 59, 0.8), rgba(51, 65, 85, 0.6));
                padding: 50px;
                border-radius: 20px;
                border: 1px solid rgba(59, 130, 246, 0.3);
                text-align: center;
                max-width: 600px;
            }
            
            .btn {
                background: linear-gradient(45deg, #3b82f6, #1e40af);
                color: white;
                padding: 15px 30px;
                border: none;
                border-radius: 10px;
                text-decoration: none;
                font-weight: bold;
                font-size: 1.1em;
                display: inline-block;
                margin: 15px;
                transition: all 0.3s ease;
                cursor: pointer;
                min-width: 200px;
            }
        </style>
    </head>
    <body>
        <div class="payment-container">
            <h2 style="color: #3b82f6;">💳 Complete Your Subscription</h2>
            <p style="font-size: 1.3em;">Plan: <strong>{{ plan.title() }}</strong></p>
            <p style="font-size: 1.5em; color: #10b981;">Amount: <strong>${{ amount }}/month</strong></p>
            
            <h3>Choose Payment Method:</h3>
            
            <div style="margin: 30px 0;">
                <button class="btn" onclick="payWithFlutterwave()">💳 Pay with Card (Flutterwave)</button>
                <button class="btn" onclick="payWithCrypto()" style="background: linear-gradient(45deg, #f7931a, #f7931a);">₿ Pay with Crypto</button>
                <button class="btn" onclick="payWithBank()" style="background: linear-gradient(45deg, #10b981, #059669);">🏦 Bank Transfer</button>
            </div>
            
            <p style="margin-top: 40px;">💬 Need help? <a href="https://wa.me/2349084824238" style="color: #3b82f6;">WhatsApp Support</a></p>
        </div>
        
        <script>
            function payWithFlutterwave() {
                alert('Flutterwave payment integration - Add your API keys to activate');
            }
            
            function payWithCrypto() {
                alert('NowPayments crypto integration - Add your API keys to activate');
            }
            
            function payWithBank() {
                alert('Bank transfer integration - Contact WhatsApp for manual setup');
            }
        </script>
    </body>
    </html>
    ''', plan=plan, amount=amount)

@app.route('/client')
def client_portal():
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Client Portal - AstraFabric</title>
        <style>
            body { 
                font-family: Arial, sans-serif; 
                margin: 0; 
                background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
                color: white; 
                min-height: 100vh;
            }
            
            .container { 
                max-width: 1000px; 
                margin: 0 auto; 
                padding: 50px 20px;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1 style="text-align: center; color: #3b82f6;">🔒 Client Security Portal</h1>
            <p style="text-align: center; font-size: 1.2em;">Access your security dashboard and reports</p>
            
            <div style="text-align: center; margin: 50px 0;">
                <p>🔐 Login coming soon - Currently in development</p>
                <p>💬 <a href="https://wa.me/2349084824238" style="color: #3b82f6;">Contact WhatsApp</a> for immediate access</p>
            </div>
        </div>
    </body>
    </html>
    ''')

@app.route('/reports')
def reports():
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head><title>Security Reports - AstraFabric</title></head>
    <body style="font-family: Arial; background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%); color: white; margin: 0; min-height: 100vh;">
        <div style="max-width: 1000px; margin: 0 auto; padding: 50px 20px;">
            <h1 style="text-align: center; color: #3b82f6;">📊 Security Reports</h1>
            <p style="text-align: center;">Executive security reports and analytics</p>
            <div style="text-align: center; margin: 50px 0;">
                <p>📈 Reports portal coming soon</p>
            </div>
        </div>
    </body>
    </html>
    ''')

@app.route('/docs')
def api_docs():
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head><title>API Documentation - AstraFabric</title></head>
    <body style="font-family: Arial; background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%); color: white; margin: 0; min-height: 100vh;">
        <div style="max-width: 1000px; margin: 0 auto; padding: 50px 20px;">
            <h1 style="text-align: center; color: #3b82f6;">📖 API Documentation</h1>
            <p style="text-align: center;">Enterprise API integration guides</p>
            <div style="text-align: center; margin: 50px 0;">
                <p>📚 API docs coming soon</p>
            </div>
        </div>
    </body>
    </html>
    ''')

# Hidden admin dashboard
@app.route('/astrafabric-admin-secure-2024')
def admin_login():
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Admin Access - AstraFabric</title>
        <style>
            body { 
                font-family: Arial, sans-serif; 
                margin: 0; 
                background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
                color: white; 
                min-height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
            }
            
            .admin-container {
                background: linear-gradient(145deg, rgba(30, 41, 59, 0.8), rgba(51, 65, 85, 0.6));
                padding: 50px;
                border-radius: 20px;
                border: 1px solid rgba(239, 68, 68, 0.3);
                text-align: center;
                max-width: 400px;
            }
            
            input {
                width: 100%;
                padding: 15px;
                margin: 10px 0;
                border: 1px solid rgba(59, 130, 246, 0.3);
                border-radius: 10px;
                background: rgba(15, 23, 42, 0.8);
                color: white;
                font-size: 1.1em;
            }
            
            .btn {
                background: linear-gradient(45deg, #ef4444, #dc2626);
                color: white;
                padding: 15px 30px;
                border: none;
                border-radius: 10px;
                font-weight: bold;
                font-size: 1.1em;
                cursor: pointer;
                width: 100%;
                margin: 20px 0;
            }
        </style>
    </head>
    <body>
        <div class="admin-container">
            <h2 style="color: #ef4444;">🔐 Admin Access</h2>
            <p style="color: #fbbf24;">⚠️ Authorized Personnel Only</p>
            
            <form method="post" action="/astrafabric-admin-verify">
                <input type="password" name="password" placeholder="Enter Admin Password" required>
                <button type="submit" class="btn">🔑 Access Dashboard</button>
            </form>
        </div>
    </body>
    </html>
    ''')

@app.route('/astrafabric-admin-verify', methods=['POST'])
def admin_verify():
    password = request.form.get('password')
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    
    if password_hash == ADMIN_PASSWORD_HASH:
        session['admin_authenticated'] = True
        return redirect('/astrafabric-admin-dashboard')
    else:
        return redirect('/astrafabric-admin-secure-2024')

@app.route('/astrafabric-admin-dashboard')
def admin_dashboard():
    if not session.get('admin_authenticated'):
        return redirect('/astrafabric-admin-secure-2024')
    
    # Get subscription stats
    conn = sqlite3.connect('astrafabric.db')
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM subscriptions WHERE status='active'")
    active_subs = c.fetchone()[0]
    c.execute("SELECT SUM(amount) FROM subscriptions WHERE status='active'")
    monthly_revenue = c.fetchone()[0] or 0
    c.execute("SELECT plan, COUNT(*) FROM subscriptions WHERE status='active' GROUP BY plan")
    plan_stats = c.fetchall()
    conn.close()
    
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Admin Dashboard - AstraFabric</title>
        <style>
            body { 
                font-family: Arial, sans-serif; 
                margin: 0; 
                background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
                color: white; 
                min-height: 100vh;
            }
            
            .header {
                background: linear-gradient(45deg, #ef4444, #dc2626);
                padding: 20px;
                text-align: center;
            }
            
            .container { 
                max-width: 1200px; 
                margin: 0 auto; 
                padding: 30px;
            }
            
            .stats-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                gap: 20px;
                margin: 30px 0;
            }
            
            .stat-card {
                background: linear-gradient(145deg, rgba(30, 41, 59, 0.8), rgba(51, 65, 85, 0.6));
                padding: 30px;
                border-radius: 15px;
                border: 1px solid rgba(59, 130, 246, 0.3);
                text-align: center;
            }
            
            .stat-number {
                font-size: 2.5em;
                font-weight: bold;
                color: #10b981;
                margin: 10px 0;
            }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🔐 AstraFabric Admin Dashboard</h1>
            <p>Enterprise Security Platform Management</p>
        </div>
        
        <div class="container">
            <div class="stats-grid">
                <div class="stat-card">
                    <h3 style="color: #3b82f6;">👥 Active Subscriptions</h3>
                    <div class="stat-number">{{ active_subs }}</div>
                    <p>Current paying customers</p>
                </div>
                
                <div class="stat-card">
                    <h3 style="color: #10b981;">💰 Monthly Revenue</h3>
                    <div class="stat-number">${{ "%.2f"|format(monthly_revenue) }}</div>
                    <p>Recurring monthly income</p>
                </div>
                
                <div class="stat-card">
                    <h3 style="color: #f59e0b;">📊 Annual Projection</h3>
                    <div class="stat-number">${{ "%.0f"|format(monthly_revenue * 12) }}</div>
                    <p>Based on current subscriptions</p>
                </div>
            </div>
            
            <div style="background: linear-gradient(145deg, rgba(30, 41, 59, 0.8), rgba(51, 65, 85, 0.6)); padding: 30px; border-radius: 15px; margin: 30px 0;">
                <h3 style="color: #8b5cf6;">📈 Plan Distribution</h3>
                {% for plan, count in plan_stats %}
                <p><strong>{{ plan.title() }}</strong>: {{ count }} subscribers</p>
                {% endfor %}
            </div>
            
            <div style="text-align: center; margin: 40px 0;">
                <p style="color: #fbbf24;">⚠️ Admin Password: <strong>astrafabric2024!secure</strong></p>
                <p>💬 WhatsApp Support: <strong>''' + WHATSAPP_NUMBER + '''</strong></p>
                <a href="/astrafabric-admin-logout" style="background: #ef4444; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">🚪 Logout</a>
            </div>
        </div>
    </body>
    </html>
    ''', active_subs=active_subs, monthly_revenue=monthly_revenue, plan_stats=plan_stats)

@app.route('/astrafabric-admin-logout')
def admin_logout():
    session.pop('admin_authenticated', None)
    return redirect('/')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
