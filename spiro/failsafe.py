# failsafe.py -
#   start debug web interface if main interface fails
#

import signal
import traceback
import subprocess

from waitress import serve
from flask import Flask, render_template, Response

from spiro.config import Config
from spiro.logger import log, debug
from spiro.webui import stream_popen

app = Flask(__name__)
app.jinja_env.trim_blocks = True
app.jinja_env.lstrip_blocks = True

err = None
cfg = Config()

@app.route('/')
def index():
    return render_template('failsafe_index.html', trace=''.join(traceback.format_tb(err.__traceback__)),
                           version=cfg.version)


@app.route('/log')
def get_log():
    p = subprocess.Popen(['/bin/journalctl', '--user-unit=spiro', '-n', '1000'], stdout=subprocess.PIPE)
    return Response(stream_popen(p), mimetype='text/plain')


@app.route('/shutdown')
def shutdown():
    subprocess.run(['sudo', 'shutdown', '-h', 'now'])
    return render_template('shutdown.html')


@app.route('/reboot')
def reboot():
    global restarting
    restarting = True
    subprocess.Popen(['sudo', 'shutdown', '-r', 'now'])
    return render_template('restarting.html', refresh=120, message="Rebooting system...")


@app.route('/exit')
def exit():
    signal.alarm(1)
    return render_template('restarting.html', refresh=10, message="Restarting web UI...")


def start(e=None):
    global err
    err = e
    serve(app, listen="*:8080", threads=2, channel_timeout=20)
