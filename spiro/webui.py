# webui.py -
#   main web ui controller for spiro
#
# - Jonas Ohlsson <jonas.ohlsson .a. slu.se>
#

from flask import Flask, render_template, Response, request, redirect, url_for, session, flash
import io
from picamera import PiCamera
import logging
from threading import Condition
from fractions import Fraction
import time
import os
import hashlib
import shutil
from spiro.spiroconfig import Config
from threading import Thread, Lock

app = Flask(__name__)

class Rotator(Thread):
    def __init__(self, value):
        Thread.__init__(self)
        self.value = value
    
    def run(self):
        lock.acquire()
        try:
            hw.motorOn(True)
            time.sleep(0.5)
            hw.halfStep(self.value, 0.03)
            time.sleep(0.5)
        finally:
            hw.motorOn(False)
            lock.release()


class StreamingOutput(object):
    def __init__(self):
        self.frame = None
        self.buffer = io.BytesIO()
        self.condition = Condition()

    def write(self, buf):
        if buf.startswith(b'\xff\xd8'):
            # New frame, copy the existing buffer's content and notify all
            # clients it's available
            self.buffer.truncate()
            with self.condition:
                self.frame = self.buffer.getvalue()
                self.condition.notify_all()
            self.buffer.seek(0)
        return self.buffer.write(buf)


class StillOutput(object):
    def __init__(self):
        self.frame = None
        self.buffer = io.BytesIO()

    def write(self, buf):
        if buf.startswith(b'\xff\xd8'):
            self.buffer.truncate()
            self.frame = self.buffer.getvalue()
            self.buffer.seek(0)
        return self.buffer.write(buf)


class ZoomObject(object):
    def __init__(self):
        self.roi = 1
        self.x = 0.5
        self.y = 0.5
    
    def set(self, x, y, roi):
        self.x = x
        self.y = y
        self.roi = roi
        self.apply()

    def apply(self):
        print("applying zoom (x,y,roi):", self.x, self.y, self.roi)
        camera.zoom = (self.y - self.roi/2.0, self.x - self.roi/2.0, self.roi, self.roi)

    def zoom(self, amt):
        print("zoom with amt", amt)
        amt = round(amt, 1)
        if amt < 0:
            # zoom out
            self.roi = min(1.0, self.roi - amt)
        else:
            # zoom in
            self.roi = max(0.2, self.roi - amt)
        print("new roi", self.roi)
        self.apply()
    
    def pan(self, panx = 0, pany = 0):
        xlimits = self.x - self.roi / 2.0, 1 - (self.x + self.roi / 2.0)
        ylimits = self.y - self.roi / 2.0, 1 - (self.y + self.roi / 2.0)

        if panx > 0:
            # pan right
            panx = min(panx, xlimits[1])
        elif panx < 0:
            # pan left
            panx = max(panx, -xlimits[0])
        if pany > 0:
            # pan down
            pany = min(pany, ylimits[1])
        elif pany < 0:
            # pan up
            pany = max(pany, -ylimits[0])
        
        print("pan x, y:", panx, pany)
        self.x = self.x + panx
        self.y = self.y + pany
        self.apply()


@app.route('/')
def index():
    if cfg.get('password') == '':
        return redirect(url_for('newpass'))
    if not 'password' in session:
        return redirect(url_for('login'))
    if not session['password'] == cfg.get('password'):
        return redirect(url_for('login'))
    return render_template('index.html', live=livestream)

@app.route('/index.html')
def redir_index():
    return redirect(url_for('index'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        pwd = request.form['password']
        if pwd == cfg.get('password'):
            session['password'] = pwd
            return redirect(url_for('index'))
        else:
            flash("Incorrect password.")
            return redirect(url_for('login'))
    else:
        return render_template('login.html')

@app.route('/logout')
def logout():
    session['password'] = ''
    return redirect(url_for('login'))

@app.route('/newpass', methods=['GET', 'POST'])
def newpass():
    if request.method == 'POST':
        currpass = request.form['currpass']
        pwd1 = request.form['pwd1']
        pwd2 = request.form['pwd2']

        if currpass != cfg.get('password'):
            flash("Current password incorrect.")
            return render_template('newpass.html')

        if pwd1 == pwd2:
            cfg.set('password', pwd1)
            session['password'] = pwd1
            flash("Password was changed.")
            return redirect(url_for('index'))
        else:
            flash("Passwords do not match.")
            return redirect(url_for('newpass'))
    else:
        return render_template('newpass.html')

@app.route('/zoom/<value>')
def zoom(value):
    zoomer.zoom(float(value))
    return redirect(url_for('index'))

@app.route('/pan/x/<value>')
def panx(value):
    zoomer.pan(panx = float(value))
    return redirect(url_for('index'))

@app.route('/pan/y/<value>')
def pany(value):
    zoomer.pan(pany = float(value))
    return redirect(url_for('index'))

@app.route('/live/<value>')
def switch_live(value):
    if setLive(value):
        print("change live mode")
        zoomer.set(0.5, 0.5, 1)
    return redirect(url_for('index'))

@app.route('/led/<value>')
def led(value):
    if value == 'on':
        hw.LEDControl(True)
    elif value == 'off':
        hw.LEDControl(False)
    return redirect(url_for('index'))

@app.route('/rotate/<value>')
def rotate(value):
    value = int(value)
    if value > 0 and value <= 400:
        rotator = Rotator(value)
        rotator.start()
    return redirect(url_for('index'))

@app.route('/findstart')
def findstart():
    hw.findStart(calibration=cfg.get('calibration'))
    return redirect(url_for('index'))

def liveGen():
    while True:
        with liveoutput.condition:
            liveoutput.condition.wait()
            frame = liveoutput.frame
            yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/stream.mjpg')
def liveStream():
    return Response(liveGen(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/capture.jpg')
def stillImage():
    if stilloutput.seek(0, io.SEEK_END) == 0:
        return redirect(url_for('static', filename='empty.jpg'))
    stilloutput.seek(0)
    return Response(stilloutput.read(), mimetype="image/jpeg")

@app.route('/grab')
def grab():
    stilloutput.truncate()
    stilloutput.seek(0)
    camera.capture(stilloutput, format="jpeg", quality=90)
    stilloutput.seek(0)
    return redirect(url_for('index'))

@app.route('/focus/<value>')
def focus(value):
    value = int(value)
    focus = cfg.get('focus')
    newfocus = 0
    if value < 0:
        newfocus = max(10, focus + value)
    else:
        newfocus = min(1000, focus + value)
    print("new focus:", newfocus)
    hw.focusCam(newfocus)
    cfg.set('focus', newfocus)
    return redirect(url_for('index'))


def setLive(val):
    global livestream
    prev = livestream
    if val == 'on' and livestream != True:
        print("enable live stream")
        livestream = True
        camera.start_recording(liveoutput, format='mjpeg', resize='1024x768')
    elif val == 'off' and livestream == True:
        print("disable live stream")
        livestream = False
        camera.stop_recording()
    return prev != livestream

@app.route('/experiment', methods=['GET', 'POST'])
def experiment():
    if request.method == 'GET':
        runtime = time.time() - exp['start'] / 60 / 24
        df = shutil.disk_usage(os.path.expanduser(os.path.join('~', exp['dir'])))
        diskspace = round(df.free / 1024 ** 3, 1)
        return render_template('experiment.html', running=exp['running'], directory=exp['dir'], delay=exp['delay'], runtime=runtime, diskspace=diskspace)

exp = {
    'running': False,
    'dir': '',
    'duration': 0,
    'start': 0,
    'delay': 0,
}
    
livestream = True
liveoutput = StreamingOutput()
stilloutput = io.BytesIO()
zoomer = ZoomObject()
lock = Lock()
cfg = Config()
camera = None
hw = None

#if __name__ == '__main__':
def start(cam, myhw):
    global camera, hw
    camera = cam
    hw = myhw
    if cfg.get('secret') == '':
        secret = hashlib.sha1(os.urandom(16))
        cfg.set('secret', secret.hexdigest())
    app.secret_key = cfg.get('secret')
    try:
        camera.meter_mode = 'spot'
        camera.iso = 0
        camera.rotation = 90
        camera.start_recording(liveoutput, format='mjpeg', resize='1024x768')
        app.run(host='0.0.0.0', port=8080, debug=False, threaded=True)
    finally:
        if livestream:
            camera.stop_recording()