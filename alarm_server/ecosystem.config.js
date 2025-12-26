module.exports = {
  apps: [{
    name: 'alarms_prod',
    script: 'venv/bin/uvicorn',
    args: 'main:app --host 127.0.0.1 --port 5002',
    cwd: '/deployments/alarm_server',
    instances: 1,
    exec_mode: 'fork',
    autorestart: true,
    watch: false,
    max_memory_restart: '100M',
    env: {
      NODE_ENV: 'production',
      PYTHONUNBUFFERED: '1'
    },
    error_file: './logs/pm2-error.log',
    out_file: './logs/pm2-out.log',
    log_date_format: 'YYYY-MM-DD HH:mm:ss Z',
    merge_logs: true,
    time: true
  }]
};
