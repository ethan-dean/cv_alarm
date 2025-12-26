module.exports = {
  apps: [{
    name: 'alarms_prod',
    script: 'main.py',
    interpreter: 'venv/bin/python3',
    cwd: '/root/deployments/alarm_server',
    instances: 1,
    exec_mode: 'fork',
    autorestart: true,
    watch: false,
    max_memory_restart: '100M',
    env: {
      PYTHONUNBUFFERED: '1'
    },
    error_file: './logs/pm2-error.log',
    out_file: './logs/pm2-out.log',
    log_date_format: 'YYYY-MM-DD HH:mm:ss Z',
    merge_logs: true,
    time: true
  }]
};
