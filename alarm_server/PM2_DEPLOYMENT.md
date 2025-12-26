# PM2 Deployment Guide for Ubuntu VPS

## Quick Deployment Steps

### 1. Copy Files to VPS

**Option A: Using scp (if files are on your local machine)**
```bash
# From your local machine
cd /Users/ethan/Downloads/Web/cv_alarm
scp -r alarm_server your_user@your-vps-ip:/tmp/

# SSH into VPS
ssh your_user@your-vps-ip

# Move to final location
sudo mkdir -p /opt/cv_alarm
sudo mv /tmp/alarm_server /opt/cv_alarm/
sudo chown -R $USER:$USER /opt/cv_alarm
```

**Option B: Using git (if code is in a repository)**
```bash
# SSH into VPS
ssh your_user@your-vps-ip

# Clone repository
cd /opt
sudo git clone <your-repo-url> cv_alarm
sudo chown -R $USER:$USER /opt/cv_alarm
```

### 2. Install Dependencies on VPS

```bash
cd /opt/cv_alarm/alarm_server

# Check Python version (need 3.10 or later)
python3 --version

# If Python 3.10+ is already installed, skip to creating venv
# If you need to install Python (Ubuntu 22.04+):
# sudo apt update
# sudo apt install python3 python3-venv python3-pip -y

# Create virtual environment
python3 -m venv venv

# Activate and install dependencies
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Configure Environment

```bash
# Copy example config
cp .env.example .env

# Edit configuration
nano .env
```

Set your configuration:
```env
# Server settings
SECRET_KEY=your-secret-key-here-generate-with-openssl-rand-hex-32
DATABASE_URL=sqlite:///./database/alarms.db
ALLOWED_ORIGINS=https://your-domain.com

# Port (already defaults to 5002, but you can override)
PORT=5002
HOST=127.0.0.1

# Admin credentials
ADMIN_USERNAME=your_username
ADMIN_PASSWORD=your_secure_password

# WebSocket settings
WS_HEARTBEAT_INTERVAL=30
WS_TIMEOUT=90
```

**Generate secret key:**
```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

### 4. Create Logs Directory

```bash
mkdir -p logs
```

### 5. Test Run

```bash
# Make sure venv is activated
source venv/bin/activate

# Test the server
python main.py
```

You should see:
```
Starting CV Alarm Server...
Database initialized
Created default admin user: your_username
CV Alarm Server started successfully
INFO:     Uvicorn running on http://127.0.0.1:5002
```

Press `Ctrl+C` to stop the test.

### 6. Start with PM2

```bash
# Install pm2 if not already installed
npm install -g pm2

# Start the application
cd /opt/cv_alarm/alarm_server
pm2 start ecosystem.config.js

# Check status
pm2 status

# View logs
pm2 logs alarms_prod

# Save pm2 configuration
pm2 save

# Setup pm2 to start on boot
pm2 startup
# Follow the instructions printed (will give you a sudo command to run)
```

### 7. PM2 Management Commands

```bash
# View status
pm2 status

# View logs
pm2 logs alarms_prod

# Restart
pm2 restart alarms_prod

# Stop
pm2 stop alarms_prod

# Delete from pm2
pm2 delete alarms_prod

# Monitor
pm2 monit

# Show detailed info
pm2 show alarms_prod
```

## Configure Nginx

Add this to your nginx configuration:

```bash
sudo nano /etc/nginx/sites-available/your-site
```

Add this location block:

```nginx
server {
    server_name your-domain.com;

    # Your existing configuration...

    # Alarm API (REST endpoints)
    location /api {
        proxy_pass http://127.0.0.1:5002;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Alarm WebSocket
    location /ws {
        proxy_pass http://127.0.0.1:5002/ws;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 86400;
    }

    # Serve frontend static files
    location / {
        proxy_pass http://127.0.0.1:5002;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # SSL configuration (if using certbot)
    # listen 443 ssl;
    # ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    # ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;
}
```

Test and reload nginx:
```bash
sudo nginx -t
sudo systemctl reload nginx
```

## Verify Deployment

### Check if server is running:
```bash
# Check pm2
pm2 status

# Check if port is listening
sudo netstat -tlnp | grep 5002
# Or
sudo ss -tlnp | grep 5002
```

### Test locally on VPS:
```bash
curl http://127.0.0.1:5002/api/health
# Should return: {"status":"healthy","version":"1.0.0"}
```

### Test from browser:
- Visit: `https://your-domain.com`
- Should see login page
- Login with your admin credentials

### Check logs:
```bash
# PM2 logs
pm2 logs alarms_prod

# Application logs
tail -f /opt/cv_alarm/alarm_server/logs/alarm_server.log

# PM2 specific logs
tail -f /opt/cv_alarm/alarm_server/logs/pm2-out.log
tail -f /opt/cv_alarm/alarm_server/logs/pm2-error.log
```

## Troubleshooting

### Port 5002 already in use:
```bash
# Check what's using the port
sudo lsof -i :5002

# Kill the process (if needed)
sudo kill -9 <PID>
```

### Database permissions:
```bash
cd /opt/cv_alarm/alarm_server
chmod 755 database/
chmod 644 database/alarms.db  # After first run
```

### PM2 won't start:
```bash
# Check pm2 logs
pm2 logs alarms_prod --lines 100

# Make sure venv path is correct
ls -la venv/bin/uvicorn

# Try running manually first
source venv/bin/activate
python main.py
```

### CORS errors in browser:
Update `ALLOWED_ORIGINS` in `.env`:
```env
ALLOWED_ORIGINS=https://your-domain.com,http://localhost:3000
```

Then restart:
```bash
pm2 restart alarms_prod
```

### WebSocket connection fails:
1. Check nginx WebSocket proxy configuration
2. Verify `/ws` location block exists
3. Check firewall allows port 443/80
4. Test WebSocket endpoint:
   ```bash
   wscat -c ws://127.0.0.1:5002/ws?token=test
   ```

## Update Deployment

When you update code:

```bash
cd /opt/cv_alarm/alarm_server

# Pull latest code (if using git)
git pull

# Or copy new files via scp
# scp ...

# Update dependencies if needed
source venv/bin/activate
pip install -r requirements.txt

# Restart pm2
pm2 restart alarms_prod

# Watch logs
pm2 logs alarms_prod
```

## Backup Database

```bash
# Create backup directory
mkdir -p /opt/cv_alarm/backups

# Backup database
cp /opt/cv_alarm/alarm_server/database/alarms.db \
   /opt/cv_alarm/backups/alarms.db.$(date +%Y%m%d_%H%M%S)

# Setup daily backup cron
crontab -e
# Add this line:
# 0 2 * * * cp /opt/cv_alarm/alarm_server/database/alarms.db /opt/cv_alarm/backups/alarms.db.$(date +\%Y\%m\%d)
```

## Summary

Your alarm server is now:
- ✅ Running on port 5002 (localhost only)
- ✅ Managed by pm2 as "alarms_prod"
- ✅ Auto-restarts on crash
- ✅ Starts on boot (after `pm2 startup` + `pm2 save`)
- ✅ Accessible via nginx reverse proxy
- ✅ Logs to pm2 and application logs

Access your alarm interface at: `https://your-domain.com`
