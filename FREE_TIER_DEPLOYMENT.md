# 🆓 AstraFabric FREE TIER Deployment Guide

## 🎯 **Render.com Free Tier Setup**

### **Free Tier Benefits:**
✅ **Web Service**: FREE with limitations  
✅ **PostgreSQL**: FREE with 1GB storage  
✅ **SSL Certificate**: FREE and automatic  
✅ **Custom Domain**: NOT available (use .onrender.com)  
✅ **24/7 Uptime**: ❌ Apps sleep after 15 mins of inactivity  

### **Free Tier Limitations:**
⚠️ **Sleeps after 15 minutes** of no requests  
⚠️ **512MB RAM** limit  
⚠️ **PostgreSQL**: 1GB storage, expires after 90 days  
⚠️ **No custom domains** (use yourapp.onrender.com)  

## 🚀 **Deployment Steps**

### **1. Deploy Using Blueprint**
1. Go to [Render Dashboard](https://dashboard.render.com)
2. Click **"New"** → **"Blueprint"**
3. Connect to: `https://github.com/ahmganbit/AstraFabric`
4. Render will create:
   - Web Service (FREE)
   - PostgreSQL Database (FREE)

### **2. Environment Variables (Required)**

Add these in **Render Dashboard → Environment**:

```bash
# Security (REQUIRED)
SECRET_KEY=uhL_D3m2zo5YXc-v2GkAOjiYHKS2qJYjNgcts_SvyC0
ADMIN_PASSWORD=AstraFabric2024!SecureAdmin

# Application (REQUIRED)
FLASK_ENV=production
BASE_URL=https://astrafabric-platform.onrender.com

# Payment Gateways (Your Keys)
NOWPAYMENTS_API_KEY=your-nowpayments-api-key
NOWPAYMENTS_HMAC_KEY=your-nowpayments-hmac-key
FLW_PUBLIC_KEY=your-flutterwave-public-key
FLW_SECRET_KEY=your-flutterwave-secret-key
FLW_SECRET_HASH=your-flutterwave-webhook-hash

# Free Tier Optimizations
GUNICORN_WORKERS=1
RATELIMIT_STORAGE_URL=memory://
```

### **3. Replace BASE_URL**
Update `BASE_URL` with your actual Render app URL:
```bash
BASE_URL=https://your-actual-app-name.onrender.com
```

## 🔧 **Free Tier Optimizations Made**

### **Performance Adjustments:**
- **Workers**: Reduced to 1 (from 2) for memory limits
- **Connections**: Reduced to 500 (from 1000)
- **Rate Limiting**: Uses memory instead of Redis
- **Database**: Falls back to SQLite if PostgreSQL unavailable

### **Removed Features for Free Tier:**
- ❌ **Redis**: Not available on free tier
- ❌ **Custom Domains**: Use .onrender.com domain
- ❌ **Multiple Workers**: Single worker for memory limits

## ⚡ **Handling Sleep Mode**

### **App Sleep Issue:**
Free tier apps sleep after 15 minutes of inactivity.

### **Solutions:**
1. **Ping Service**: Use UptimeRobot (free) to ping every 5 minutes
2. **Cold Start**: First request after sleep takes 10-30 seconds
3. **Upgrade**: Consider paid plan ($7/month) for 24/7 uptime

### **UptimeRobot Setup (FREE):**
1. Go to [uptimerobot.com](https://uptimerobot.com)
2. Add monitor: `https://your-app.onrender.com/health`
3. Check every 5 minutes
4. Keeps your app awake during business hours

## 💾 **Database Considerations**

### **PostgreSQL Free Tier:**
- **Storage**: 1GB limit
- **Connections**: Limited
- **Expires**: After 90 days of inactivity
- **Backup**: Manual export recommended

### **SQLite Fallback:**
If PostgreSQL issues occur, app falls back to SQLite automatically.

## 🧪 **Testing Your Deployment**

### **Check These Endpoints:**
```bash
# Health check
https://your-app.onrender.com/health

# Homepage
https://your-app.onrender.com/

# Contact form
https://your-app.onrender.com/contact

# Subscribe page
https://your-app.onrender.com/subscribe
```

### **Expected Behavior:**
- First load after sleep: 10-30 seconds
- Subsequent loads: Fast
- Payment forms: Should work with your keys

## 🔄 **Upgrading from Free Tier**

### **When to Upgrade ($7/month Starter):**
- ✅ **No Sleep**: 24/7 uptime
- ✅ **More RAM**: Better performance
- ✅ **Custom Domains**: Use astrafabric.com
- ✅ **Redis**: Better rate limiting
- ✅ **Support**: Priority support

### **Upgrade Process:**
1. Render Dashboard → Service Settings
2. Change plan to "Starter"
3. Add custom domain settings
4. Enable Redis service

## 📊 **Free Tier Monitoring**

### **Watch These Metrics:**
- **Response Time**: Should be <5s after warmup
- **Memory Usage**: Stay under 512MB
- **Database Size**: Monitor 1GB limit
- **Uptime**: Track with UptimeRobot

### **Logs Location:**
Render Dashboard → Your Service → Logs

## 🎯 **Deployment Checklist**

- [ ] Blueprint deployed successfully
- [ ] Environment variables set
- [ ] Health endpoint returns 200
- [ ] Homepage loads properly
- [ ] Contact form works
- [ ] Payment keys configured
- [ ] UptimeRobot monitoring setup
- [ ] Database connection working

## 🆙 **Next Steps After Deployment**

1. **Test all functionality** on free tier
2. **Monitor performance** for a few days
3. **Set up UptimeRobot** to prevent sleeping
4. **Consider upgrading** when ready for production traffic
5. **Add custom domain** after upgrading to paid plan

**Your AstraFabric is now ready for FREE deployment! 🎉**

*Free tier is perfect for testing and development. Upgrade when you're ready for production traffic.*
