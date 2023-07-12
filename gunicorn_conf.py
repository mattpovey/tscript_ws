bind = "0.0.0.0:8008"
workers = 2
accesslog = "-"

# Long timeout currently required for the transcription tasks. Migration to Celery 
# will enable shorter timeout
timeout = 9000
keepalive = 2

# The app
wsgi_app = "tscript_ws:ts_flask_app" 