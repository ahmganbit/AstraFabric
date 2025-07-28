# AstraFabric Deployment Guide for Render.com

## 🚀 Quick Deployment Steps

### 1. **Push Updated Code to GitHub**
```bash
git add .
git commit -m "Updated to production-ready architecture with security improvements"
git push origin main
```

### 2. **Deploy to Render.com**

#### Option A: Using render.yaml (Recommended)
1. Go to your Render.com dashboard
2. Click "New" → "Blueprint"
3. Connect your GitHub repository
4. Render will automatically read the `render.yaml` file

#### Option B: Manual Setup
1. Go to Render.com dashboard
2. Click "New" → "Web Service"
3. Connect your GitHub repository
4. Use these settings:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn --config gunicorn.conf.py app_factory:create_app()`

### 3. **Configure Environment Variables**

**In your Render.com dashboard, set these environment variables:**

#### 🔐 **Security (REQUIRED)**
```
SECRET_KEY=your-super-secret-key-here-minimum-32-chars
ADMIN_PASSWORD=YourSecureAdminPassword123!
```

#### 💳 **Payment Gateways (Optional)**
```
NOWPAYMENTS_API_KEY=your-nowpayments-api-key
NOWPAYMENTS_HMAC_KEY=your-nowpayments-hmac-key
FLW_PUBLIC_KEY=your-flutterwave-public-key
FLW_SECRET_KEY=your-flutterwave-secret-key
FLW_SECRET_HASH=your-flutterwave-webhook-hash
```

#### 🌐 **Application Settings**
```
FLASK_ENV=production
BASE_URL=https://your-app-name.onrender.com
```

### 4. **Generate Secure Keys**

Use these commands to generate secure keys:

```python
# Generate SECRET_KEY
import secrets
print(secrets.token_urlsafe(32))

# Or use this online: https://djecrety.ir/
```

### 5. **Database Setup**

If using the `render.yaml` blueprint:
- PostgreSQL database will be created automatically
- Redis instance will be created for rate limiting

If setting up manually:
1. Create a PostgreSQL database in Render
2. Add the `DATABASE_URL` environment variable

### 6. **Health Check**

After deployment, verify your app is working:
- Visit: `https://your-app-name.onrender.com/health`
- Should return: `{"status": "healthy", "timestamp": "...", "version": "2.0.0"}`

## 🔧 **Troubleshooting**

### Common Issues:

#### **Build Fails**
```bash
# Check requirements.txt is properly formatted
# Ensure all dependencies are compatible
```

#### **App Won't Start**
- Check environment variables are set
- Verify `SECRET_KEY` and `ADMIN_PASSWORD` are configured
- Check Render logs for specific errors

#### **Database Connection Issues**
- Ensure `DATABASE_URL` is set
- Check PostgreSQL service is running
- Verify database credentials

#### **Missing Routes**
- The new structure uses blueprints
- Make sure all route files are present in `/routes/` folder

### **Accessing Logs**
1. Go to Render dashboard
2. Click on your service
3. Click "Logs" tab to see real-time logs

## 📋 **Post-Deployment Checklist**

- [ ] App starts successfully
- [ ] Health check endpoint works (`/health`)
- [ ] Homepage loads (`/`)
- [ ] Contact form works (`/contact`)
- [ ] Admin login works (once implemented)
- [ ] Payment integration tested
- [ ] SSL certificate is active
- [ ] Custom domain configured (if applicable)

## 🔒 **Security Checklist**

- [ ] `SECRET_KEY` is set and secure (32+ random characters)
- [ ] `ADMIN_PASSWORD` is strong and unique
- [ ] All payment API keys are configured
- [ ] HTTPS is enforced (automatic on Render)
- [ ] Environment variables are not in source code
- [ ] Database backups are enabled

## 🛠 **Advanced Configuration**

### Custom Domain Setup
1. In Render dashboard → Settings → Custom Domains
2. Add your domain (e.g., astrafabric.com)
3. Update DNS records as shown
4. SSL certificate will be generated automatically

### Scaling
- **Starter Plan**: Good for development and small traffic
- **Standard Plan**: Recommended for production
- **Pro Plan**: For high-traffic applications

### Monitoring
- Enable Render's built-in monitoring
- Set up email alerts for failures
- Monitor database performance

## 📞 **Need Help?**

If you encounter issues:

1. **Check Render Logs**: Most issues show up in the deployment logs
2. **Verify Environment Variables**: Ensure all required variables are set
3. **Test Locally**: Run `python app_factory.py` locally first
4. **Database Issues**: Check PostgreSQL connection and migrations

**Common Commands for Local Testing:**
```bash
# Test the app locally
python app_factory.py

# Run tests
pytest test_app.py -v

# Check for missing dependencies
pip freeze > requirements.txt
```

---

**Your AstraFabric platform is now production-ready with enterprise-grade security! 🎉**
