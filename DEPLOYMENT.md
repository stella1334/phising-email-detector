# Bank Phishing Guardian - Complete Deployment Guide

This guide covers deploying both the API service and browser extension for production use.

## Overview

The Bank Phishing Guardian system consists of two components:
1. **API Service**: Backend analysis engine with AI integration
2. **Browser Extension**: Frontend interface for real-time email analysis

## Prerequisites

### System Requirements
- Linux/macOS server (2+ GB RAM recommended)
- Python 3.9+ with pip
- Docker (optional but recommended)
- SSL certificate for HTTPS (production)
- Google Gemini API key

### External Services
- **Google Gemini API**: For AI-powered analysis
- **Domain/Hosting**: For production API deployment
- **Chrome Web Store Account**: For extension distribution (optional)

## Part 1: API Service Deployment

### Option A: Docker Deployment (Recommended)

#### 1. Clone and Configure
```bash
# Clone repository
git clone <repository-url>
cd bank_phishing_detector

# Create production environment file
cp .env.example .env
```

#### 2. Configure Environment
Edit `.env` file:
```bash
# API Configuration
PHISHING_DETECTOR_GEMINI_API_KEY=your_actual_api_key_here
PHISHING_DETECTOR_HOST=0.0.0.0
PHISHING_DETECTOR_PORT=8000
PHISHING_DETECTOR_DEBUG=false

# Production settings
PHISHING_DETECTOR_LOG_LEVEL=INFO
PHISHING_DETECTOR_HIGH_RISK_THRESHOLD=70.0
PHISHING_DETECTOR_MEDIUM_RISK_THRESHOLD=40.0
```

#### 3. Deploy with Docker Compose
```bash
# Start services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f
```

#### 4. Set Up Reverse Proxy (Nginx)
```bash
# Generate SSL certificates (Let's Encrypt)
sudo certbot --nginx -d your-domain.com

# Start with proxy
docker-compose --profile with-proxy up -d
```

### Option B: Manual Deployment

#### 1. Install Dependencies
```bash
# Install Python dependencies
pip install -r requirements.txt

# Install system dependencies
sudo apt update
sudo apt install nginx certbot python3-certbot-nginx
```

#### 2. Configure Service
```bash
# Create systemd service
sudo nano /etc/systemd/system/phishing-detector.service
```

Service file content:
```ini
[Unit]
Description=Bank Phishing Detector API
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/bank-phishing-detector
Environment=PATH=/opt/bank-phishing-detector/venv/bin
EnvironmentFile=/opt/bank-phishing-detector/.env
ExecStart=/opt/bank-phishing-detector/venv/bin/python app.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

#### 3. Start Service
```bash
# Enable and start service
sudo systemctl enable phishing-detector
sudo systemctl start phishing-detector

# Check status
sudo systemctl status phishing-detector
```

### Option C: Cloud Platform Deployment

#### Heroku Deployment
```bash
# Install Heroku CLI and login
heroku login

# Create app
heroku create your-app-name

# Set environment variables
heroku config:set PHISHING_DETECTOR_GEMINI_API_KEY=your_key
heroku config:set PHISHING_DETECTOR_HOST=0.0.0.0
heroku config:set PHISHING_DETECTOR_PORT=$PORT

# Deploy
git push heroku main
```

#### AWS ECS Deployment
```bash
# Build and push Docker image
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account>.dkr.ecr.us-east-1.amazonaws.com

docker build -t bank-phishing-detector .
docker tag bank-phishing-detector:latest <account>.dkr.ecr.us-east-1.amazonaws.com/bank-phishing-detector:latest
docker push <account>.dkr.ecr.us-east-1.amazonaws.com/bank-phishing-detector:latest

# Deploy using ECS task definition
aws ecs update-service --cluster your-cluster --service phishing-detector --force-new-deployment
```

## Part 2: Browser Extension Deployment

### Development Setup

#### 1. Configure Extension
```bash
cd browser_extension

# Update manifest.json for production
# Change API endpoint to your production URL
```

Update `manifest.json`:
```json
{
  "host_permissions": [
    "https://your-api-domain.com/*",
    "https://mail.google.com/*",
    "https://outlook.live.com/*"
  ]
}
```

#### 2. Create Icons
```bash
# Create proper icon files (replace placeholders)
# Use design tools or online generators
# Ensure all required sizes: 16x16, 32x32, 48x48, 128x128
```

#### 3. Build Extension
```bash
# Make build script executable
chmod +x build.sh

# Build production package
./build.sh
```

### Distribution Options

#### Option A: Chrome Web Store (Recommended)

1. **Prepare Submission**:
   - Extension zip file
   - High-quality screenshots (1280x800)
   - Promotional images (440x280, 920x680, 1400x560)
   - Store description and metadata
   - Privacy policy

2. **Developer Registration**:
   - Create Chrome Web Store developer account
   - Pay one-time $5 registration fee
   - Verify developer identity

3. **Submit Extension**:
   - Upload zip file
   - Complete store listing
   - Set pricing (free recommended)
   - Submit for review

4. **Review Process**:
   - Automated security checks
   - Manual review (1-3 days typically)
   - Possible rejection requiring fixes

#### Option B: Enterprise Distribution

```bash
# Package for enterprise
zip -r bank-phishing-guardian-enterprise.zip browser_extension/

# Distribute via:
# - Internal app store
# - Group Policy (Windows)
# - Mobile Device Management
# - Direct download with instructions
```

#### Option C: Developer Mode (Testing)

```bash
# Users can install manually:
# 1. Enable Developer mode in Chrome
# 2. Use "Load unpacked" with extension folder
# 3. Suitable for internal testing only
```

## Part 3: Production Configuration

### Security Hardening

#### API Service Security
```bash
# Configure firewall
sudo ufw enable
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Set up fail2ban
sudo apt install fail2ban
sudo systemctl enable fail2ban
```

#### SSL/TLS Configuration
```nginx
# nginx.conf - Strong SSL configuration
ssl_protocols TLSv1.2 TLSv1.3;
ssl_ciphers ECDHE-RSA-AES128-GCM-SHA256:ECDHE-RSA-AES256-GCM-SHA384;
ssl_prefer_server_ciphers off;
add_header Strict-Transport-Security "max-age=63072000" always;
```

#### Rate Limiting
```nginx
# nginx.conf - Rate limiting
limit_req_zone $binary_remote_addr zone=api:10m rate=100r/m;
limit_req_zone $binary_remote_addr zone=bulk:10m rate=10r/m;

location /analyze {
    limit_req zone=api burst=20 nodelay;
    proxy_pass http://backend;
}
```

### Monitoring and Logging

#### Application Monitoring
```bash
# Set up log rotation
sudo nano /etc/logrotate.d/phishing-detector
```

Logrotate configuration:
```
/opt/bank-phishing-detector/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 0644 www-data www-data
    postrotate
        systemctl reload phishing-detector
    endscript
}
```

#### Health Monitoring
```bash
# Create health check script
#!/bin/bash
HEALTH_URL="https://your-domain.com/health"
RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" $HEALTH_URL)

if [ $RESPONSE -ne 200 ]; then
    echo "API health check failed: $RESPONSE"
    # Send alert (email, Slack, etc.)
fi

# Run via cron every 5 minutes
*/5 * * * * /opt/scripts/health-check.sh
```

### Performance Optimization

#### API Optimization
```python
# In config.py - Production settings
class ProductionSettings(Settings):
    debug: bool = False
    log_level: str = "WARNING"
    gemini_temperature: float = 0.1  # More deterministic
    max_request_size: int = 5 * 1024 * 1024  # 5MB limit
```

#### Database Optimization (if added)
```bash
# Redis for caching (optional enhancement)
sudo apt install redis-server
sudo systemctl enable redis-server

# Configure Redis in application
pip install redis
```

### Backup and Recovery

#### Configuration Backup
```bash
# Backup script
#!/bin/bash
BACKUP_DIR="/opt/backups/$(date +%Y%m%d)"
mkdir -p $BACKUP_DIR

# Backup configuration
cp -r /opt/bank-phishing-detector/.env $BACKUP_DIR/
cp -r /etc/nginx/sites-available/phishing-detector $BACKUP_DIR/
cp -r /etc/systemd/system/phishing-detector.service $BACKUP_DIR/

# Upload to cloud storage (optional)
aws s3 sync $BACKUP_DIR s3://your-backup-bucket/$(date +%Y%m%d)/
```

## Part 4: User Onboarding

### Installation Guide for End Users

#### For Chrome Web Store Installation
1. Visit Chrome Web Store
2. Search "Bank Phishing Guardian"
3. Click "Add to Chrome"
4. Accept permissions
5. Configure API endpoint if needed

#### For Manual Installation
1. Download extension package
2. Extract to folder
3. Open Chrome → Extensions
4. Enable Developer mode
5. Click "Load unpacked"
6. Select extension folder
7. Configure settings

### User Training Materials

#### Quick Start Guide
```markdown
# Bank Phishing Guardian - Quick Start

## What You'll See
- ✅ Green check: Email is safe
- ⚠️ Yellow warning: Be cautious
- 🚨 Red alert: Likely phishing

## What to Do
- **Green**: Proceed normally
- **Yellow**: Verify sender independently
- **Red**: Do not click links or download attachments

## Getting Help
- Click extension icon for details
- Report false positives
- Contact IT support for questions
```

## Part 5: Maintenance and Updates

### Regular Maintenance Tasks

#### Weekly Tasks
- Review application logs
- Check API response times
- Monitor error rates
- Verify SSL certificate status

#### Monthly Tasks
- Update dependencies
- Review security patches
- Analyze usage statistics
- Backup configuration

#### Quarterly Tasks
- Security audit
- Performance optimization
- User feedback review
- Disaster recovery test

### Update Procedures

#### API Service Updates
```bash
# Zero-downtime update
git pull origin main
docker-compose build
docker-compose up -d --no-deps api

# Or for manual deployment
sudo systemctl stop phishing-detector
git pull origin main
pip install -r requirements.txt
sudo systemctl start phishing-detector
```

#### Extension Updates
```bash
# Update version in manifest.json
# Build new package
./build.sh

# Upload to Chrome Web Store
# Users receive automatic updates
```

## Troubleshooting

### Common Issues

#### API Service Issues
```bash
# Check service status
sudo systemctl status phishing-detector

# View logs
sudo journalctl -u phishing-detector -f

# Test API directly
curl https://your-domain.com/health
```

#### Extension Issues
- Check browser console for errors
- Verify API endpoint configuration
- Test on different email providers
- Clear extension data and reconfigure

### Support Resources

- **Documentation**: Complete setup guides
- **Issue Tracker**: GitHub issues for bug reports
- **Community**: Discord/Slack for user support
- **Professional**: Paid support options for enterprises

## Conclusion

This deployment guide provides comprehensive instructions for setting up both components of the Bank Phishing Guardian system. Follow the security best practices and monitoring recommendations for a robust production deployment.

For additional support or custom deployment assistance, please refer to the project documentation or contact the development team.
