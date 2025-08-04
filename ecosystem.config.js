module.exports = {
  apps: [
    {
      name: "gmail-monitor",
      script: "notif.py",
      interpreter: "python",
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: "1G",
      env: {
        NODE_ENV: "production"
      },
      error_file: "./logs/gmail-monitor-error.log",
      out_file: "./logs/gmail-monitor-out.log",
      log_file: "./logs/gmail-monitor-combined.log",
      time: true,
      // Restart jika crash
      max_restarts: 10,
      min_uptime: "10s",
      // Restart setiap 24 jam untuk menghindari memory leak
      cron_restart: "0 0 * * *"
    }
  ]
}; 
