"""
Entry point used by Gunicorn in production.
SocketIO requires eventlet worker:
  gunicorn --worker-class eventlet -w 1 wsgi:app
"""
from app import app, socketio

if __name__ == '__main__':
    socketio.run(app)
