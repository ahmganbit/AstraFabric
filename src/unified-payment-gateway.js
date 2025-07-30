const axios = require('axios');
const crypto = require('crypto');

// Configuration
const config = {
    flutterwave: {
        publicKey: process.env.FLW_PUBLIC_KEY,
        secretKey: process.env.FLW_SECRET_KEY,
        encryptionKey: process.env.FLW_ENCRYPTION_KEY
    },
    nowpayments: {
        apiKey: process.env.NOWPAYMENTS_API_KEY,
        ipnSecret: process.env.NOWPAYMENTS_IPN_SECRET
    },
    currencyApi: process.env.CURRENCY_API_KEY
};

// Currency Conversion Service
class CurrencyConverter {
    static async convertToUSD(amount, currency) {
        try {
            if (currency.toUpperCase() === 'USD') return amount;
            
            const response = await axios.get(
                `https://api.exchangerate-api.com/v4/latest/USD`,
                { headers: { 'apikey': config.currencyApi } }
            );
            
            const rate = response.data.rates[currency.toUpperCase()];
            return amount / rate;
        } catch (error) {
            console.error('Currency conversion failed:', error);
            return amount; // Fallback to original amount
        }
    }
    
    static async getSupportedCurrencies() {
        try {
            const response = await axios.get(
                'https://api.exchangerate-api.com/v4/latest/USD',
                { headers: { 'apikey': config.currencyApi } }
            );
            return Object.keys(response.data.rates);
        } catch (error) {
            console.error('Failed to get currencies:', error);
            return ['USD', 'EUR', 'GBP', 'NGN', 'CAD', 'AUD']; // Fallback
        }
    }
}

// Flutterwave Integration
class FlutterwaveGateway {
    static async initializePayment(email, amount, currency) {
        try {
            const usdAmount = await CurrencyConverter.convertToUSD(amount, currency);
            
            const response = await axios.post(
                'https://api.flutterwave.com/v3/payments',
                {
                    tx_ref: `AF-${Date.now()}`,
                    amount: usdAmount,
                    currency: 'USD',
                    redirect_url: 'https://astrafabric.com/payment/callback/flutterwave',
                    customer: {
                        email
                    },
                    customizations: {
                        title: 'AstraFabric Security',
                        description: 'Premium Security Subscription',
                        logo: 'https://astrafabric.com/ASTRAFRABRIC-LOGO.png'
                    },
                    payment_options: 'card, banktransfer, ussd, mpesa, mobilemoney'
                },
                {
                    headers: {
                        Authorization: `Bearer ${config.flutterwave.secretKey}`,
                        'Content-Type': 'application/json'
                    }
                }
            );
            
            return {
                success: true,
                gateway: 'flutterwave',
                data: response.data.data
            };
        } catch (error) {
            console.error('Flutterwave payment failed:', error);
            return { success: false, error: error.message };
        }
    }
    
    static async verifyPayment(transactionId) {
        try {
            const response = await axios.get(
                `https://api.flutterwave.com/v3/transactions/${transactionId}/verify`,
                {
                    headers: {
                        Authorization: `Bearer ${config.flutterwave.secretKey}`
                    }
                }
            );
            
            return {
                success: true,
                status: response.data.data.status,
                amount: response.data.data.amount,
                currency: response.data.data.currency
            };
        } catch (error) {
            console.error('Flutterwave verification failed:', error);
            return { success: false, error: error.message };
        }
    }
}

// NOWPayments Integration
class NOWPaymentsGateway {
    static async initializePayment(amount, currency, cryptoCurrency) {
        try {
            const usdAmount = await CurrencyConverter.convertToUSD(amount, currency);
            
            const response = await axios.post(
                'https://api.nowpayments.io/v1/payment',
                {
                    price_amount: usdAmount,
                    price_currency: 'USD',
                    pay_currency: cryptoCurrency,
                    order_id: `AF-${Date.now()}`,
                    order_description: 'AstraFabric Security Subscription',
                    ipn_callback_url: 'https://astrafabric.com/payment/callback/nowpayments',
                    success_url: 'https://astrafabric.com/payment/success',
                    cancel_url: 'https://astrafabric.com/payment/cancel'
                },
                {
                    headers: {
                        'x-api-key': config.nowpayments.apiKey,
                        'Content-Type': 'application/json'
                    }
                }
            );
            
            return {
                success: true,
                gateway: 'nowpayments',
                data: response.data
            };
        } catch (error) {
            console.error('NOWPayments payment failed:', error);
            return { success: false, error: error.message };
        }
    }
    
    static async getPaymentStatus(paymentId) {
        try {
            const response = await axios.get(
                `https://api.nowpayments.io/v1/payment/${paymentId}`,
                {
                    headers: {
                        'x-api-key': config.nowpayments.apiKey
                    }
                }
            );
            
            return {
                success: true,
                status: response.data.payment_status,
                amount: response.data.price_amount,
                currency: response.data.price_currency
            };
        } catch (error) {
            console.error('NOWPayments status failed:', error);
            return { success: false, error: error.message };
        }
    }
    
    static async getSupportedCryptocurrencies() {
        try {
            const response = await axios.get(
                'https://api.nowpayments.io/v1/currencies',
                {
                    headers: {
                        'x-api-key': config.nowpayments.apiKey
                    }
                }
            );
            
            return response.data.currencies
                .filter(currency => currency.payin_enabled)
                .map(currency => currency.code);
        } catch (error) {
            console.error('Failed to get cryptocurrencies:', error);
            return ['BTC', 'ETH', 'USDT', 'BNB', 'LTC', 'BCH']; // Fallback
        }
    }
}

// Unified Payment Gateway
class UnifiedPaymentGateway {
    static async initializePayment(email, amount, currency, paymentMethod, cryptoCurrency = 'USDT') {
        switch (paymentMethod) {
            case 'flutterwave':
                return await FlutterwaveGateway.initializePayment(email, amount, currency);
            case 'crypto':
                return await NOWPaymentsGateway.initializePayment(amount, currency, cryptoCurrency);
            default:
                return { success: false, error: 'Invalid payment method' };
        }
    }
    
    static async verifyPayment(gateway, transactionId) {
        switch (gateway) {
            case 'flutterwave':
                return await FlutterwaveGateway.verifyPayment(transactionId);
            case 'nowpayments':
                return await NOWPaymentsGateway.getPaymentStatus(transactionId);
            default:
                return { success: false, error: 'Invalid payment gateway' };
        }
    }
    
    static async getSupportedOptions() {
        try {
            const currencies = await CurrencyConverter.getSupportedCurrencies();
            const cryptocurrencies = await NOWPaymentsGateway.getSupportedCryptocurrencies();
            
            return {
                currencies,
                cryptocurrencies,
                paymentMethods: ['flutterwave', 'crypto']
            };
        } catch (error) {
            console.error('Failed to get payment options:', error);
            return {
                currencies: ['USD', 'EUR', 'GBP', 'NGN'],
                cryptocurrencies: ['BTC', 'ETH', 'USDT'],
                paymentMethods: ['flutterwave', 'crypto']
            };
        }
    }
}

module.exports = UnifiedPaymentGateway;
