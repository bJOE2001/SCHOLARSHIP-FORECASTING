"""
Gunicorn configuration for production deployment on DigitalOcean (non-Docker).
"""

import multiprocessing

# Network binding (bind to localhost if behind Nginx on the same droplet,
# or 0.0.0.0 if accessed across a DigitalOcean VPC private network)
bind = "0.0.0.0:8001"

# Concurrency: 2 workers per CPU core is optimal for ASGI I/O + ML inference
workers = min(multiprocessing.cpu_count() * 2, 4) or 2
worker_class = "uvicorn.workers.UvicornWorker"

# Timeouts & Keepalive
timeout = 60
keepalive = 5

# Logging: Standard streams are captured cleanly by systemd (journalctl)
accesslog = "-"
errorlog = "-"
loglevel = "info"

# Process naming
proc_name = "scholarship-forecasting"
