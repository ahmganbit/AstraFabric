const express = require('express');
const http = require('http');
const socketIo = require('socket.io');
const path = require('path');
const InfrastructureMonitor = require('./src/infrastructure-monitoring');
const monitoringRoutes = require('./src/routes/monitoring');
const UnifiedPaymentGateway = require('./src/unified-payment-gateway');

const app = express();
const server = http.createServer(app);
const io = socketIo(server);

// Initialize monitoring
const monitor = new InfrastructureMonitor();
monitor.io = io;

// Middleware
app.use(express.json());
app.use(express.static(path.join(__dirname, 'public')));

// Payment routes
app.post('/api/initialize-payment', async (req, res) => {
    try {
        const { email, amount, currency, paymentMethod, cryptoCurrency } = req.body;
        const result = await UnifiedPaymentGateway.initializePayment(
            email, 
            amount, 
            currency, 
            paymentMethod, 
            cryptoCurrency
        );
        res.json(result);
    } catch (error) {
        console.error('Payment initialization failed:', error);
        res.status(500).json({ success: false, error: error.message });
    }
});

// Payment callback endpoints
app.get('/payment/callback/flutterwave', async (req, res) => {
    const { transaction_id } = req.query;
    
    try {
        const result = await UnifiedPaymentGateway.verifyPayment('flutterwave', transaction_id);
        
        if (result.success && result.status === 'successful') {
            // Activate user subscription
            await activateUserSubscription(result);
            res.redirect('/payment/success');
        } else {
            res.redirect('/payment/failed');
        }
    } catch (error) {
        console.error('Flutterwave callback failed:', error);
        res.redirect('/payment/failed');
    }
});

app.post('/payment/callback/nowpayments', async (req, res) => {
    const ipnData = req.body;
    
    // Verify IPN signature
    const hmac = require('crypto').createHmac('sha512', process.env.NOWPAYMENTS_IPN_SECRET);
    hmac.update(JSON.stringify(ipnData));
    const signature = hmac.digest('hex');
    
    if (signature !== req.headers['x-nowpayments-sig']) {
        return res.status(400).send('Invalid signature');
    }
    
    try {
        if (ipnData.payment_status === 'finished') {
            // Activate user subscription
            await activateUserSubscription({
                amount: ipnData.price_amount,
                currency: ipnData.price_currency,
                email: ipnData.order_id.split('-')[1] // Extract email from order_id
            });
        }
        
        res.status(200).send('IPN received');
    } catch (error) {
        console.error('NOWPayments callback failed:', error);
        res.status(500).send('Callback processing failed');
    }
});

// Monitoring routes
app.use('/api/monitoring', monitoringRoutes);

// Serve the main application
app.get('*', (req, res) => {
    res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

// WebSocket connection for real-time metrics
io.on('connection', (socket) => {
    console.log('Client connected to monitoring dashboard');
    
    socket.on('subscribe', (resourceId) => {
        socket.join(`resource:${resourceId}`);
        console.log(`Client subscribed to resource ${resourceId}`);
    });
    
    socket.on('disconnect', () => {
        console.log('Client disconnected from monitoring dashboard');
    });
});

const PORT = process.env.PORT || 3000;
server.listen(PORT, () => {
    console.log(`AstraFabric server running on port ${PORT}`);
});

// Helper function to activate user subscription
async function activateUserSubscription(paymentData) {
    // Implement subscription activation logic
    console.log('Activating subscription for:', paymentData);
}
