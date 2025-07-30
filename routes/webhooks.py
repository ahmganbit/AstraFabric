# Webhook Routes Blueprint
# routes/webhooks.py - Automated payment processing webhooks

from flask import Blueprint, request, jsonify, current_app
from models import db, Customer, Subscription, Payment, PaymentStatus, SubscriptionPlan, WebhookLog
from datetime import datetime, timedelta
import hashlib
import hmac
import json
import structlog

logger = structlog.get_logger()
webhook_bp = Blueprint('webhooks', __name__)


@webhook_bp.route('/nowpayments', methods=['POST'])
def nowpayments_webhook():
    """Handle NowPayments webhook for automatic subscription activation."""
    try:
        # Log webhook for debugging
        webhook_log = WebhookLog(
            source='nowpayments',
            event_type='payment_update',
            headers=dict(request.headers),
            payload=request.get_json(),
            ip_address=request.remote_addr
        )
        
        # Verify webhook signature
        signature = request.headers.get('x-nowpayments-sig')
        if signature:
            webhook_log.signature = signature
            webhook_log.signature_valid = verify_nowpayments_signature(
                request.data, signature
            )
        
        db.session.add(webhook_log)
        
        data = request.get_json()
        if not data:
            webhook_log.error_message = 'No JSON data received'
            db.session.commit()
            return jsonify({'error': 'No data'}), 400
        
        # Extract payment information
        payment_status = data.get('payment_status')
        order_id = data.get('order_id')
        payment_id = data.get('payment_id')
        
        webhook_log.payment_reference = order_id
        webhook_log.event_type = f"payment_{payment_status}"
        
        if not order_id:
            webhook_log.error_message = 'Missing order_id'
            db.session.commit()
            return jsonify({'error': 'Missing order_id'}), 400
        
        # Find payment record
        payment = Payment.query.filter_by(reference=order_id).first()
        if not payment:
            webhook_log.error_message = f'Payment not found: {order_id}'
            db.session.commit()
            return jsonify({'error': 'Payment not found'}), 404
        
        # Update payment status
        old_status = payment.status
        if payment_status == 'finished':
            payment.status = PaymentStatus.COMPLETED
            payment.completed_at = datetime.utcnow()
            payment.webhook_verified = True
            
            # Activate subscription
            activate_subscription(payment)
            webhook_log.processing_status = 'completed'
            
        elif payment_status == 'failed':
            payment.status = PaymentStatus.FAILED
            webhook_log.processing_status = 'failed'
            
        elif payment_status == 'refunded':
            payment.status = PaymentStatus.REFUNDED
            # Deactivate subscription if exists
            deactivate_subscription(payment)
            webhook_log.processing_status = 'refunded'
        
        db.session.commit()
        
        logger.info('NowPayments webhook processed', extra={
            'order_id': order_id,
            'old_status': old_status.value if old_status else None,
            'new_status': payment.status.value,
            'payment_status': payment_status
        })
        
        return jsonify({'status': 'success'})
        
    except Exception as e:
        logger.error('NowPayments webhook error', extra={'error': str(e)})
        if 'webhook_log' in locals():
            webhook_log.error_message = str(e)
            webhook_log.processing_status = 'error'
            db.session.commit()
        return jsonify({'error': 'Webhook processing failed'}), 500


@webhook_bp.route('/flutterwave', methods=['POST'])
def flutterwave_webhook():
    """Handle Flutterwave webhook for automatic subscription activation."""
    try:
        # Log webhook for debugging
        webhook_log = WebhookLog(
            source='flutterwave',
            event_type='payment_update',
            headers=dict(request.headers),
            payload=request.get_json(),
            ip_address=request.remote_addr
        )
        
        # Verify webhook signature
        signature = request.headers.get('verif-hash')
        if signature:
            webhook_log.signature = signature
            webhook_log.signature_valid = verify_flutterwave_signature(signature)
        
        db.session.add(webhook_log)
        
        data = request.get_json()
        if not data:
            webhook_log.error_message = 'No JSON data received'
            db.session.commit()
            return jsonify({'error': 'No data'}), 400
        
        # Extract payment information
        event_type = data.get('event')
        if event_type != 'charge.completed':
            webhook_log.processing_status = 'ignored'
            db.session.commit()
            return jsonify({'status': 'ignored'})
        
        charge_data = data.get('data', {})
        tx_ref = charge_data.get('tx_ref')
        status = charge_data.get('status')
        
        webhook_log.payment_reference = tx_ref
        webhook_log.event_type = f"charge_{status}"
        
        if not tx_ref:
            webhook_log.error_message = 'Missing tx_ref'
            db.session.commit()
            return jsonify({'error': 'Missing tx_ref'}), 400
        
        # Find payment record
        payment = Payment.query.filter_by(reference=tx_ref).first()
        if not payment:
            webhook_log.error_message = f'Payment not found: {tx_ref}'
            db.session.commit()
            return jsonify({'error': 'Payment not found'}), 404
        
        # Update payment status
        old_status = payment.status
        if status == 'successful':
            payment.status = PaymentStatus.COMPLETED
            payment.completed_at = datetime.utcnow()
            payment.webhook_verified = True
            
            # Activate subscription
            activate_subscription(payment)
            webhook_log.processing_status = 'completed'
            
        elif status == 'failed':
            payment.status = PaymentStatus.FAILED
            webhook_log.processing_status = 'failed'
        
        db.session.commit()
        
        logger.info('Flutterwave webhook processed', extra={
            'tx_ref': tx_ref,
            'old_status': old_status.value if old_status else None,
            'new_status': payment.status.value,
            'status': status
        })
        
        return jsonify({'status': 'success'})
        
    except Exception as e:
        logger.error('Flutterwave webhook error', extra={'error': str(e)})
        if 'webhook_log' in locals():
            webhook_log.error_message = str(e)
            webhook_log.processing_status = 'error'
            db.session.commit()
        return jsonify({'error': 'Webhook processing failed'}), 500


def verify_nowpayments_signature(payload, signature):
    """Verify NowPayments webhook signature."""
    try:
        hmac_key = current_app.config.get('NOWPAYMENTS_HMAC_KEY')
        if not hmac_key:
            return False
        
        expected_signature = hmac.new(
            hmac_key.encode('utf-8'),
            payload,
            hashlib.sha512
        ).hexdigest()
        
        return hmac.compare_digest(signature, expected_signature)
    except Exception:
        return False


def verify_flutterwave_signature(signature):
    """Verify Flutterwave webhook signature."""
    try:
        secret_hash = current_app.config.get('FLW_SECRET_HASH')
        if not secret_hash:
            return False
        
        return hmac.compare_digest(signature, secret_hash)
    except Exception:
        return False


def activate_subscription(payment):
    """Activate subscription after successful payment."""
    try:
        # Determine plan from payment amount
        plan_mapping = {
            99: ('essential', 'monthly'),
            990: ('essential', 'yearly'),
            199: ('professional', 'monthly'),
            1990: ('professional', 'yearly'),
            299: ('enterprise', 'monthly'),
            2990: ('enterprise', 'yearly')
        }
        
        amount = float(payment.amount)
        plan_info = plan_mapping.get(amount)
        
        if not plan_info:
            logger.error('Unknown payment amount for subscription', extra={
                'payment_id': payment.id,
                'amount': amount
            })
            return
        
        plan_name, billing_cycle = plan_info
        
        # Calculate subscription dates
        start_date = datetime.utcnow()
        if billing_cycle == 'monthly':
            end_date = start_date + timedelta(days=30)
        else:  # yearly
            end_date = start_date + timedelta(days=365)
        
        # Create subscription
        subscription = Subscription(
            customer_id=payment.customer_id,
            plan=SubscriptionPlan(plan_name.upper()),
            status='active',
            start_date=start_date,
            end_date=end_date,
            billing_cycle=billing_cycle,
            amount=payment.amount,
            currency=payment.currency
        )
        
        # Link payment to subscription
        payment.subscription_id = subscription.id
        
        db.session.add(subscription)
        db.session.commit()
        
        logger.info('Subscription activated', extra={
            'customer_id': payment.customer_id,
            'plan': plan_name,
            'billing_cycle': billing_cycle,
            'subscription_id': subscription.id
        })
        
        # Send welcome email (implement later)
        # send_welcome_email(payment.customer, subscription)
        
    except Exception as e:
        logger.error('Subscription activation failed', extra={
            'payment_id': payment.id,
            'error': str(e)
        })


def deactivate_subscription(payment):
    """Deactivate subscription after refund."""
    try:
        if payment.subscription_id:
            subscription = Subscription.query.get(payment.subscription_id)
            if subscription:
                subscription.status = 'cancelled'
                subscription.end_date = datetime.utcnow()
                db.session.commit()
                
                logger.info('Subscription deactivated', extra={
                    'subscription_id': subscription.id,
                    'customer_id': payment.customer_id
                })
    except Exception as e:
        logger.error('Subscription deactivation failed', extra={
            'payment_id': payment.id,
            'error': str(e)
        })


@webhook_bp.route('/flutterwave/callback')
def flutterwave_callback():
    """Handle Flutterwave payment callback."""
    try:
        transaction_id = request.args.get('transaction_id')
        tx_ref = request.args.get('tx_ref')
        status = request.args.get('status')
        
        if status == 'successful' and transaction_id:
            # Verify transaction with Flutterwave API
            verification_result = verify_flutterwave_transaction(transaction_id)
            
            if verification_result['success']:
                # Find and update payment
                payment = Payment.query.filter_by(reference=tx_ref).first()
                if payment and payment.status == PaymentStatus.PENDING:
                    payment.status = PaymentStatus.COMPLETED
                    payment.completed_at = datetime.utcnow()
                    payment.gateway_transaction_id = transaction_id
                    
                    # Activate subscription
                    activate_subscription(payment)
                    db.session.commit()
                
                return redirect('/payment/success')
            else:
                return redirect('/payment/cancel')
        else:
            return redirect('/payment/cancel')
            
    except Exception as e:
        logger.error('Flutterwave callback error', extra={'error': str(e)})
        return redirect('/payment/cancel')


def verify_flutterwave_transaction(transaction_id):
    """Verify transaction with Flutterwave API."""
    try:
        import requests
        
        secret_key = current_app.config.get('FLW_SECRET_KEY')
        if not secret_key:
            return {'success': False, 'error': 'Flutterwave not configured'}
        
        url = f"https://api.flutterwave.com/v3/transactions/{transaction_id}/verify"
        headers = {
            'Authorization': f'Bearer {secret_key}',
            'Content-Type': 'application/json'
        }
        
        response = requests.get(url, headers=headers, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            if data['status'] == 'success' and data['data']['status'] == 'successful':
                return {'success': True, 'data': data['data']}
        
        return {'success': False, 'error': 'Transaction verification failed'}
        
    except Exception as e:
        logger.error('Transaction verification error', extra={'error': str(e)})
        return {'success': False, 'error': 'Verification service unavailable'}