# CV Alarm - Remote Management System

A remote alarm management system with VPS-hosted web interface and WebSocket synchronization to your local computer.

## Overview

This system extends the CV alarm project with remote management capabilities:

- **VPS Server**: Web interface accessible from anywhere
- **Local Client**: Runs on your computer to execute alarms
- **Real-time Sync**: WebSocket connection keeps everything in sync
- **Multiple Alarms**: Create, edit, and manage multiple alarms
- **iOS-style UI**: Clean, modern interface inspired by Apple's Clock app

## Architecture

```
┌─────────────────────────────────────┐
│        VPS (Remote Server)          │
│  ┌──────────────────────────────┐  │
│  │  FastAPI Backend             │  │
│  │  - REST API                  │  │
│  │  - WebSocket Server          │  │
│  │  - SQLite Database           │  │
│  └──────────────────────────────┘  │
│  ┌──────────────────────────────┐  │
│  │  Frontend (HTML/CSS/JS)      │  │
│  │  - Login Interface           │  │
│  │  - Alarm Management          │  │
│  └──────────────────────────────┘  │
└─────────────────────────────────────┘
              │
              │ WebSocket (WSS)
              ▼
┌─────────────────────────────────────┐
│     Local Computer                 │
│  ┌──────────────────────────────┐  │
│  │  Alarm Client                │  │
│  │  - WebSocket Client          │  │
│  │  - APScheduler               │  │
│  │  - Subprocess Manager        │  │
│  └──────────────────────────────┘  │
│              │                      │
│              ▼                      │
│  ┌──────────────────────────────┐  │
│  │  run_alarm.py                │  │
│  │  (Original CV Alarm)         │  │
│  └──────────────────────────────┘  │
└─────────────────────────────────────┘
```

## Installation

### Part 1: VPS Server Setup

#### 1. Provision VPS
- Ubuntu 22.04 LTS recommended
- Minimum 2GB RAM, 1 CPU core
- Install Python 3.10+, nginx, certbot

#### 2. Deploy Backend
```bash
# On your VPS
cd /opt
git clone <your-repo> cv_alarm
cd cv_alarm/alarm_server

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
nano .env  # Edit configuration

# Generate secret key
python -c "import secrets; print(secrets.token_hex(32))"
# Add to .env as SECRET_KEY

# Set admin credentials in .env
ADMIN_USERNAME=your_username
ADMIN_PASSWORD=your_secure_password
```

#### 3. Create Systemd Service
```bash
sudo nano /etc/systemd/system/alarm-server.service
```

```ini
[Unit]
Description=CV Alarm Server
After=network.target

[Service]
Type=simple
User=your_user
WorkingDirectory=/opt/cv_alarm/alarm_server
Environment="PATH=/opt/cv_alarm/alarm_server/venv/bin"
ExecStart=/opt/cv_alarm/alarm_server/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable alarm-server
sudo systemctl start alarm-server
```

#### 4. Configure Nginx
```bash
sudo nano /etc/nginx/sites-available/alarm
```

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /ws {
        proxy_pass http://127.0.0.1:8000/ws;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }
}
```

```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/alarm /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx

# Setup SSL with Let's Encrypt
sudo certbot --nginx -d your-domain.com
```

### Part 2: Local Client Setup

**Platform Support:**
- ✅ macOS (instructions below)
- ✅ Linux (similar to macOS, use systemd)
- ✅ Windows (see `alarm_client/deployment/WINDOWS_SETUP.md`)

#### macOS/Linux Setup

##### 1. Install Dependencies
```bash
cd /path/to/cv_alarm/alarm_client

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # macOS/Linux
# OR on Windows: venv\Scripts\activate.bat

# Install dependencies
pip install -r requirements.txt
```

#### 2. Configure Client
```bash
cp .env.example .env
nano .env
```

Edit `.env`:
```env
# VPS connection
VPS_URL=wss://your-domain.com/ws
REST_API_URL=https://your-domain.com/api

# Authentication
ALARM_USERNAME=your_username
ALARM_PASSWORD=your_secure_password

# Timezone
TIMEZONE=America/New_York

# Paths
CV_ALARM_ROOT=/Users/ethan/Downloads/Web/cv_alarm
RUN_ALARM_SCRIPT=run_alarm.py
```

#### 3. Test Manual Run
```bash
source venv/bin/activate
python main.py
```

You should see:
```
CV Alarm Client Starting...
VPS URL: wss://your-domain.com/ws
Timezone: America/New_York
Prerequisites check passed
Scheduler started
WebSocket client started
Alarm client running. Press Ctrl+C to stop.
```

#### 4. Setup LaunchAgent (Auto-start on Boot)
```bash
# Edit the plist file
cd deployment
nano com.user.alarm-client.plist

# Replace %INSTALL_PATH% with actual path
# Example: /Users/ethan/Downloads/Web/cv_alarm

# Copy to LaunchAgents
cp com.user.alarm-client.plist ~/Library/LaunchAgents/

# Load the agent
launchctl load ~/Library/LaunchAgents/com.user.alarm-client.plist

# Check status
launchctl list | grep alarm-client
```

#### 5. View Logs
```bash
# Real-time logs
tail -f /path/to/cv_alarm/alarm_client/logs/alarm_client.log

# Or use macOS Console app
# Filter for "alarm_client"
```

#### Windows Setup

**For detailed Windows instructions, see:** `alarm_client/deployment/WINDOWS_SETUP.md`

**Quick Start:**
1. Install Python 3.10+
2. Open Command Prompt in `alarm_client` folder
3. Run:
   ```cmd
   python -m venv venv
   venv\Scripts\activate.bat
   pip install -r requirements.txt
   copy .env.example .env
   notepad .env
   ```
4. Edit `.env` with Windows paths (e.g., `C:\Users\YourName\cv_alarm`)
5. Test: `python main.py`
6. Setup auto-start using **Task Scheduler** (see WINDOWS_SETUP.md)

**Auto-start methods:**
- **Task Scheduler** (Recommended) - Runs hidden at startup
- **Startup Folder** - Shows console window
- **Windows Service** - Uses NSSM for background service

## Usage

### 1. Access Web Interface
Open https://your-domain.com in your browser

### 2. Login
- Username: (set in VPS .env)
- Password: (set in VPS .env)

### 3. Create Alarm
1. Click "+ Add Alarm"
2. Set time (24-hour format)
3. Choose repeat days (M T W T F S S)
4. Add label (optional)
5. Click "Save"

### 4. Manage Alarms
- **Enable/Disable**: Toggle switch on the right
- **Edit**: Click on alarm card
- **Delete**: Edit alarm, then delete button

### 5. Connection Status
- Green dot: Local client connected
- Red dot: Local client offline

## Features

### Web Interface
- Clean, iOS-style design
- Real-time synchronization
- Multiple alarm support
- Day-of-week selection (Mon-Sun)
- Enable/disable toggle
- Custom labels

### Local Client
- Automatic reconnection
- Timezone-aware scheduling
- Process locking (one alarm at a time)
- Error handling and retry logic
- Comprehensive logging

### Security
- JWT authentication with 31-day expiration
- Automatic logout on token expiration
- TLS/SSL encryption (WSS)
- Password hashing (bcrypt)
- Input validation

## Troubleshooting

### VPS Server Issues

**Server won't start:**
```bash
# Check service status
sudo systemctl status alarm-server

# Check logs
sudo journalctl -u alarm-server -f

# Common issues:
# - Missing dependencies: pip install -r requirements.txt
# - Port in use: sudo lsof -i :8000
# - Database permissions: chmod 755 database/
```

**Can't access web interface:**
```bash
# Check nginx
sudo nginx -t
sudo systemctl status nginx

# Check firewall
sudo ufw status
sudo ufw allow 80
sudo ufw allow 443

# Check SSL certificate
sudo certbot certificates
```

### Local Client Issues

**Client won't connect:**
```bash
# Check if client is running
ps aux | grep "python main.py"

# Check logs
tail -f logs/alarm_client.log

# Common issues:
# - Wrong VPS_URL in .env
# - Invalid credentials
# - Network/firewall blocking WebSocket
```

**Alarm doesn't fire:**
```bash
# Check if alarm is enabled in web UI
# Check client logs for scheduling errors
# Verify timezone is correct in .env
# Check that run_alarm.py exists and model file is present
```

**Webcam error when alarm fires:**
```bash
# Check if another process is using webcam
lsof | grep "Camera"

# Check lock file
ls -la /tmp/cv_alarm.lock

# Remove stale lock if needed
rm /tmp/cv_alarm.lock
```

### Connection Status Always Red

**If web UI shows red dot but client is running:**
```bash
# Check WebSocket connection in browser console (F12)
# Look for WebSocket errors

# Check that client authenticated successfully
grep "Authentication successful" logs/alarm_client.log

# Verify token hasn't expired (31 days)
# Restart client to get new token
launchctl unload ~/Library/LaunchAgents/com.user.alarm-client.plist
launchctl load ~/Library/LaunchAgents/com.user.alarm-client.plist
```

### Session Expired / Automatic Logout

**Web UI automatically logs out after 31 days:**
- JWT tokens expire after 31 days for security
- When token expires, you'll see "Session expired. Please log in again." toast message
- Both WebSocket and REST API calls are protected
- Simply log in again to continue using the application
- The alarm_client will continue running with its own token

## Advanced Configuration

### Change Timezone
Edit `alarm_client/.env`:
```env
TIMEZONE=America/Los_Angeles
```

Restart client:
```bash
launchctl unload ~/Library/LaunchAgents/com.user.alarm-client.plist
launchctl load ~/Library/LaunchAgents/com.user.alarm-client.plist
```

### Change Alarm Duration
Edit `alarm_client/.env`:
```env
MAX_ALARM_DURATION=2400  # 40 minutes
```

### Multiple Users (Future)
Currently single-user only. To add multi-user support:
1. Add user registration endpoint
2. Update database schema
3. Modify WebSocket to support multiple connections per user
4. Update frontend with user management

## Maintenance

### Backup Database
```bash
# On VPS
cd /opt/cv_alarm/alarm_server/database
cp alarms.db alarms.db.backup.$(date +%Y%m%d)

# Or setup automated backup
echo "0 2 * * * cp /opt/cv_alarm/alarm_server/database/alarms.db /backup/alarms.db.$(date +\%Y\%m\%d)" | crontab -
```

### Update System
```bash
# On VPS
cd /opt/cv_alarm
git pull
cd alarm_server
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart alarm-server

# On local computer
cd /Users/ethan/Downloads/Web/cv_alarm
git pull
cd alarm_client
source venv/bin/activate
pip install -r requirements.txt
launchctl unload ~/Library/LaunchAgents/com.user.alarm-client.plist
launchctl load ~/Library/LaunchAgents/com.user.alarm-client.plist
```

### View Logs
```bash
# VPS server logs
sudo journalctl -u alarm-server -f

# Local client logs
tail -f /Users/ethan/Downloads/Web/cv_alarm/alarm_client/logs/alarm_client.log

# Nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

## Development

### Run VPS Server Locally
```bash
cd alarm_server
source venv/bin/activate
python main.py
# Access at http://localhost:8000
```

### Run Client with Local Server
Edit `alarm_client/.env`:
```env
VPS_URL=ws://localhost:8000/ws
REST_API_URL=http://localhost:8000/api
```

### API Documentation
Access Swagger UI at: https://your-domain.com/docs

## Support

For issues or questions:
1. Check logs first
2. Review troubleshooting section
3. Verify configuration files
4. Test connectivity (ping, curl, telnet)
5. Check GitHub issues

## License

Same as original CV Alarm project.
