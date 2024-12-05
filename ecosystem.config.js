module.exports = {
  apps: [{
    name: 'science-quotes-bot',
    script: 'start.sh',
    autorestart: true,
    watch: false,
    max_memory_restart: '1G',
    env: {
      NODE_ENV: 'production'
    },
    // Restart on errors
    max_restarts: 10,
    min_uptime: '5m',
    // Logging
    out_file: './logs/pm2_out.log',
    error_file: './logs/pm2_error.log',
    merge_logs: true,
    time: true,
  }]
};
