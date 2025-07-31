const express = require('express');
const http = require('http');
const socketIo = require('socket.io');
const path = require('path');
require('dotenv').config();

const app = express();
const server = http.createServer(app);
const io = socketIo(server);

// Error handling for uncaught exceptions
process.on('uncaughtException', (error) => {
    console.error('Uncaught Exception:', error);
});

process.on('unhandledRejection', (reason, promise) => {
    console.error('Unhandled Rejection at:', promise, 'reason:', reason);
});

// Middleware
app.use(express.json());
app.use(express.static(path.join(__dirname, 'static')));

// Health check endpoint - responds immediately
app.get('/health', (req, res) => {
    res.status(200).json({
        status: 'OK',
        timestamp: new Date().toISOString(),
        service: 'AstraFabric',
        uptime: process.uptime()
    });
});

// Root endpoint
app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname, 'static', 'index.html'));
});

// Simple test endpoint
app.get('/test', (req, res) => {
    res.json({ message: 'AstraFabric is running!' });
});

// Payment routes with error handling
app.post('/api/initialize-payment', async (req, res) => {
    try {
        const { email, amount, currency, paymentMethod, cryptoCurrency } = req.body;
        const UnifiedPaymentGateway = require('./src/unified-payment-gateway');
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

// Monitoring routes - only initialize if Redis is available
let monitoringRoutes;
try {
    if (process.env.REDIS_URL) {
        monitoringRoutes = require('./src/routes/monitoring');
        app.use('/api/monitoring', monitoringRoutes);
        console.log('Monitoring routes initialized');
    } else {
        console.warn('REDIS_URL not set, monitoring routes disabled');
    }
} catch (error) {
    console.error('Failed to initialize monitoring routes:', error);
}

// Catch-all route for SPA
app.get('*', (req, res) => {
    res.sendFile(path.join(__dirname, 'static', 'index.html'));
});

// Initialize monitoring only if Redis is available
let monitor;
if (process.env.REDIS_URL) {
    try {
        const InfrastructureMonitor = require('./src/infrastructure-monitoring');
        monitor = new InfrastructureMonitor();
        monitor.io = io;
        console.log('Infrastructure monitoring initialized successfully');
    } catch (error) {
        console.error('Failed to initialize infrastructure monitoring:', error);
    }
}

// WebSocket connection
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

// Start server with error handling
const PORT = process.env.PORT || 3000;

try {
    server.listen(PORT, () => {
        console.log(`🚀 AstraFabric server running on port ${PORT}`);
        console.log(`📊 Environment: ${process.env.NODE_ENV || 'development'}`);
        console.log(`🔗 Health check: http://localhost:${PORT}/health`);
        console.log(`🌐 Test endpoint: http://localhost:${PORT}/test`);
        
        // Log environment variables (without sensitive data)
        console.log('📋 Environment variables:');
        console.log(`  NODE_ENV: ${process.env.NODE_ENV || 'not set'}`);
        console.log(`  PORT: ${PORT}`);
        console.log(`  REDIS_URL: ${process.env.REDIS_URL ? 'set' : 'not set'}`);
        console.log(`  FLW_PUBLIC_KEY: ${process.env.FLW_PUBLIC_KEY ? 'set' : 'not set'}`);
        console.log(`  NOWPAYMENTS_API_KEY: ${process.env.NOWPAYMENTS_API_KEY ? 'set' : 'not set'}`);
    });
} catch (error) {
    console.error('Failed to start server:', error);
    process.exit(1);
}

// Helper function to activate user subscription
async function activateUserSubscription(paymentData) {
    console.log('Activating subscription for:', paymentData);
}