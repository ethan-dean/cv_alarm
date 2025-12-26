# Windows Setup Guide for CV Alarm Client

This guide covers setting up the alarm client on Windows to run automatically at startup.

## Prerequisites

- Windows 10 or Windows 11
- Python 3.10 or later installed
- Git (optional, for cloning repository)

## Installation Steps

### 1. Install Python Dependencies

Open **Command Prompt** or **PowerShell** as Administrator:

```cmd
cd C:\Users\YourName\cv_alarm\alarm_client

REM Create virtual environment
python -m venv venv

REM Activate virtual environment
venv\Scripts\activate.bat

REM Install dependencies
pip install -r requirements.txt
```

### 2. Configure the Client

```cmd
REM Copy example config
copy .env.example .env

REM Edit the config file
notepad .env
```

Edit `.env` with your settings:
```env
# VPS connection
VPS_URL=wss://your-domain.com/ws
REST_API_URL=https://your-domain.com/api

# Authentication
USERNAME=admin
PASSWORD=your-secure-password

# Timezone (use Windows timezone names)
# Common options: America/New_York, America/Los_Angeles, America/Chicago
TIMEZONE=America/New_York

# Paths (use Windows paths with backslashes or forward slashes)
CV_ALARM_ROOT=C:\Users\YourName\cv_alarm
RUN_ALARM_SCRIPT=run_alarm.py
```

### 3. Test Manual Run

```cmd
cd C:\Users\YourName\cv_alarm\alarm_client
venv\Scripts\activate.bat
python main.py
```

You should see output like:
```
CV Alarm Client Starting...
VPS URL: wss://your-domain.com/ws
Timezone: America/New_York
Prerequisites check passed
Scheduler started
WebSocket client started
Alarm client running. Press Ctrl+C to stop.
```

Press `Ctrl+C` to stop the test.

## Auto-Start Options

You have three options for running the client automatically:

### Option A: Task Scheduler (Recommended)

This method runs the client at startup without a visible window.

#### Step 1: Edit the VBScript

Edit `deployment\start_alarm_client_hidden.vbs` and update the path:
```vbscript
installPath = "C:\Users\YourName\cv_alarm\alarm_client"
```

#### Step 2: Create Scheduled Task

1. Press `Win + R`, type `taskschd.msc`, press Enter
2. Click **"Create Task..."** (not "Create Basic Task")
3. **General Tab:**
   - Name: `CV Alarm Client`
   - Description: `Runs CV alarm client with WebSocket sync`
   - Select: **"Run whether user is logged on or not"**
   - Check: **"Run with highest privileges"**
   - Configure for: **Windows 10** (or your version)

4. **Triggers Tab:**
   - Click **"New..."**
   - Begin the task: **"At startup"**
   - Advanced settings:
     - Delay task for: **30 seconds** (gives network time to connect)
   - Click **OK**

5. **Actions Tab:**
   - Click **"New..."**
   - Action: **"Start a program"**
   - Program/script: `wscript.exe`
   - Add arguments: `"C:\Users\YourName\cv_alarm\alarm_client\deployment\start_alarm_client_hidden.vbs"`
   - Click **OK**

6. **Conditions Tab:**
   - Check: **"Start only if the following network connection is available: Any connection"**
   - Uncheck: **"Stop if the computer switches to battery power"**

7. **Settings Tab:**
   - Check: **"Allow task to be run on demand"**
   - Check: **"Run task as soon as possible after a scheduled start is missed"**
   - Check: **"If the task fails, restart every: 1 minute"**
   - Attempt to restart up to: **3 times**
   - If the running task does not end when requested: **"Do not stop"**

8. Click **OK**, enter your Windows password if prompted

#### Step 3: Test the Task

Right-click the task → **"Run"**

Check if it's running:
```cmd
tasklist | findstr python
```

View logs:
```cmd
type C:\Users\YourName\cv_alarm\alarm_client\logs\alarm_client.log
```

### Option B: Startup Folder (Simple, but shows console window)

1. Press `Win + R`, type `shell:startup`, press Enter
2. Create a shortcut to `deployment\start_alarm_client.bat`
3. The client will start in a console window on login

### Option C: Windows Service (Advanced)

For running as a background service, use NSSM (Non-Sucking Service Manager):

#### Step 1: Download NSSM
- Download from: https://nssm.cc/download
- Extract to a folder (e.g., `C:\nssm`)

#### Step 2: Install Service
Open **Command Prompt as Administrator**:
```cmd
cd C:\nssm\win64

REM Install service
nssm install CVAlarmClient "C:\Users\YourName\cv_alarm\alarm_client\venv\Scripts\python.exe" "C:\Users\YourName\cv_alarm\alarm_client\main.py"

REM Set working directory
nssm set CVAlarmClient AppDirectory "C:\Users\YourName\cv_alarm\alarm_client"

REM Set to auto-start
nssm set CVAlarmClient Start SERVICE_AUTO_START

REM Start the service
nssm start CVAlarmClient
```

#### Check Service Status:
```cmd
nssm status CVAlarmClient
```

#### View Logs:
```cmd
type C:\Users\YourName\cv_alarm\alarm_client\logs\alarm_client.log
```

#### Stop/Remove Service:
```cmd
nssm stop CVAlarmClient
nssm remove CVAlarmClient confirm
```

## Firewall Configuration

If Windows Firewall blocks the connection:

1. Open **Windows Defender Firewall** → **Advanced Settings**
2. Click **Outbound Rules** → **New Rule...**
3. Rule Type: **Program**
4. Program path: `C:\Users\YourName\cv_alarm\alarm_client\venv\Scripts\python.exe`
5. Action: **Allow the connection**
6. Profile: Check all (Domain, Private, Public)
7. Name: `CV Alarm Client`

## Troubleshooting

### Client won't connect

**Check if Python is running:**
```cmd
tasklist | findstr python
```

**Check logs:**
```cmd
type C:\Users\YourName\cv_alarm\alarm_client\logs\alarm_client.log
```

**Common issues:**
- **Antivirus blocking**: Add exception for `python.exe` in your antivirus
- **Firewall**: Allow Python through Windows Firewall (see above)
- **Wrong path in .env**: Check `CV_ALARM_ROOT` uses Windows paths
- **VPS URL wrong**: Verify `wss://` (not `ws://`) and domain is correct

### Webcam not working when alarm fires

**Check if another program is using webcam:**
- Close Zoom, Skype, Teams, etc.
- Check Windows Camera app isn't running

**Check lock file:**
```cmd
dir %TEMP%\cv_alarm.lock
```

**Remove stale lock:**
```cmd
del %TEMP%\cv_alarm.lock
```

### Task Scheduler task won't run

**Check task history:**
1. Open Task Scheduler
2. Right-click **CV Alarm Client** → **Properties**
3. Go to **History** tab
4. Look for errors

**Common fixes:**
- Ensure path in VBScript is correct (no typos)
- Run task manually first to test
- Check "Run with highest privileges" is enabled
- Verify Windows password is correct

### View real-time logs

Use PowerShell:
```powershell
Get-Content -Path "C:\Users\YourName\cv_alarm\alarm_client\logs\alarm_client.log" -Wait -Tail 50
```

Or use a log viewer like **Notepad++** or **BareTail**.

## Uninstallation

### Remove Task Scheduler Task:
1. Open Task Scheduler
2. Find **CV Alarm Client**
3. Right-click → **Delete**

### Remove Windows Service (if using NSSM):
```cmd
nssm stop CVAlarmClient
nssm remove CVAlarmClient confirm
```

### Remove Files:
```cmd
rmdir /s /q C:\Users\YourName\cv_alarm\alarm_client
```

## Additional Notes

### Timezone Configuration

Windows uses IANA timezone names. Common values:
- Eastern: `America/New_York`
- Central: `America/Chicago`
- Mountain: `America/Denver`
- Pacific: `America/Los_Angeles`

Full list: https://en.wikipedia.org/wiki/List_of_tz_database_time_zones

### Python Path Issues

If `python` command not found, use full path:
```cmd
C:\Users\YourName\AppData\Local\Programs\Python\Python311\python.exe
```

Or add Python to PATH:
1. Search for "Environment Variables"
2. Edit "Path" variable
3. Add Python installation directory

### Running Multiple Alarms

The process lock ensures only one alarm runs at a time. If multiple alarms are scheduled at the same time:
1. First alarm runs immediately
2. Second alarm waits 5 minutes, then retries
3. Maximum 3 retry attempts

## Support

For issues:
1. Check logs in `logs\alarm_client.log`
2. Verify configuration in `.env`
3. Test WebSocket connection in browser: `https://your-domain.com`
4. Check Task Scheduler history for task errors
5. Ensure Python and all dependencies installed correctly
