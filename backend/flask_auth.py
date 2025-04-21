import os

from flask import Flask, request
import threading
from werkzeug.serving import make_server

server = None

class FlaskAuth(threading.Thread):
    port = None
    redirect_uri = None
    token = None

    app_thread = None

    def __init__(self, port):
        threading.Thread.__init__(self)

        self.port = port
        self.redirect_uri = "http://127.0.0.1:" + str(port)

        self.app = Flask(__name__)
        self.app.config['SECRET_KEY'] = os.urandom(64)
        self.app.config['SESSION_TYPE'] = 'filesystem'
        self.app.config['SESSION_FILE_DIR'] = './.flask_session/'
        self.app.config['SESSION_PERMANENT'] = True
        self.app.route('/')(self.index)

        self.server = make_server("127.0.0.1", port, self.app)
        self.ctx = self.app.app_context()
        self.ctx.push()

    def run(self):
        self.server.serve_forever()

    def stop(self):
        self.server.shutdown()

    def get_token(self):
        return self.token

    # POST / PUT request handlers
    def index(self):
        if request.args.get("code"):
            # Being redirected from Spotify auth page
            self.token = request.args.get("code")
        return f'<h2>You can now close this browser tab and continue in Stream Controller</h2>'

def start_server(port):
    global server
    # App routes defined here
    print("Setup Server on port: ", port)
    server = FlaskAuth(port)
    server.token = None
    print("Starting Server...")
    server.start()

def stop_server():
    global server
    server.stop()
