# Gunicorn configuration file for Render deployment
import os
import multiprocessing

# Server socket
bind = "0.0.0.0:{}".format(int(os.environ.get('PORT', 5000)))
backlog = 2048

# Worker processes
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "sync"
worker_connections = 1000
timeout = 120
keepalive = 5

# Logging
accesslog = "-"
errorlog = "-"
loglevel = "info"

# Process naming
proc_name = "pdf-buddy"

# Server mechanics
daemon = False
pidfile = None
umask = 0
user = None
group = None
tmp_upload_dir = None

