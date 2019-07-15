# webui.py -
#   main web ui controller for spiro
#
# - Jonas Ohlsson <jonas.ohlsson .a. slu.se>
#

from flask import Flask, render_template, Response, request, redirect, url_for, session, flash, abort
import io
import logging
import time
import os
import hashlib
import shutil
from spiro.spiroconfig import Config
from spiro.experimenter import Experimenter
from threading import Thread, Lock, Condition

logging.basicConfig(format='%(asctime)s %(message)s')
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
        self.roi = max(min(self.roi, 1.0), 0.2)
        limits = (self.roi / 2.0, 1 - self.roi / 2.0)
        self.x = max(min(self.x, limits[1]), limits[0])
        self.y = max(min(self.y, limits[1]), limits[0])
        print("applying zoom (x,y,roi):", self.x, self.y, self.roi)
        camera.zoom = (self.y - self.roi/2.0, self.x - self.roi/2.0, self.roi, self.roi)

    def zoom(self, amt):
        self.roi = round(amt, 1)
        print("new roi", self.roi)
        self.apply()
    
    def pan(self, panx = 0, pany = 0):
        print("pan x, y:", panx, pany)
        self.x = self.x + round(panx, 1)
        self.y = self.y + round(pany, 1)
        self.apply()


def public_route(decorated_function):
    decorated_function.is_public = True
    return decorated_function

def not_while_running(decorated_function):
    decorated_function.not_while_running = True
    return decorated_function

@app.before_request
def check_route_access():
    if cfg.get('password') == '':
        return redirect(url_for('newpass'))
    if any([request.endpoint.startswith('static/'),
            session.get('password').__eq__(cfg.get('password')),
            getattr(app.view_functions[request.endpoint], 'is_public', False)]):
        if experimenter.running and getattr(app.view_functions[request.endpoint], 'not_while_running', False):
            return redirect(url_for('empty'))
        return  # Access granted
    else:
        return redirect(url_for('login'))

@app.route('/')
def index():
    return render_template('index.html', live=livestream, focus=cfg.get('focus'), led=hw.led)

@app.route('/index.html')
def redir_index():
    return redirect(url_for('index'))

@app.route('/empty')
def empty():
    return render_template('unavailable.html'), 409

@public_route
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

@public_route
@app.route('/logout')
def logout():
    session['password'] = ''
    return redirect(url_for('login'))

@public_route
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

@not_while_running
@app.route('/zoom/<int:value>')
def zoom(value):
    zoomer.zoom(float(value / 100))
    return redirect(url_for('index'))

@not_while_running
@app.route('/pan/x/<value>')
def panx(value):
    zoomer.pan(panx = float(value))
    return redirect(url_for('index'))

@not_while_running
@app.route('/pan/y/<value>')
def pany(value):
    zoomer.pan(pany = float(value))
    return redirect(url_for('index'))

@not_while_running
@app.route('/live/<value>')
def switch_live(value):
    if setLive(value):
        print("change live mode")
        zoomer.set(0.5, 0.5, 1)
    return redirect(url_for('index'))

def setLive(val):
    global livestream
    prev = livestream
    if val == 'on' and livestream != True:
        print("enable live stream")
        livestream = True
        camera.resolution = "2592x1944"
        camera.start_recording(liveoutput, format='mjpeg', resize='1024x768')
    elif val == 'off' and livestream == True:
        print("disable live stream")
        livestream = False
        camera.stop_recording()
        camera.resolution = camera.MAX_RESOLUTION
    return prev != livestream

@not_while_running
@app.route('/led/<value>')
def led(value):
    if value == 'on':
        hw.LEDControl(True)
    elif value == 'off':
        hw.LEDControl(False)
    return redirect(url_for('index'))

@not_while_running
@app.route('/rotate/<value>')
def rotate(value):
    value = int(value)
    if value > 0 and value <= 400:
        rotator = Rotator(value)
        rotator.start()
    return redirect(url_for('index'))

@not_while_running
@app.route('/findstart')
def findstart():
    hw.motorOn(True)
    hw.findStart(calibration=cfg.get('calibration'))
    time.sleep(0.5)
    hw.motorOn(False)
    return redirect(url_for('index'))

def liveGen():
    while True:
        with liveoutput.condition:
            liveoutput.condition.wait()
            frame = liveoutput.frame
            yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@not_while_running
@app.route('/stream.mjpg')
def liveStream():
    return Response(liveGen(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/nightstill.jpg')
def nightStill():
    if nightstill.seek(0, io.SEEK_END) == 0:
        return redirect(url_for('static', filename='empty.jpg'))
    nightstill.seek(0)
    return Response(nightstill.read(), mimetype="image/jpeg")

@app.route('/daystill.jpg')
def dayStill():
    if daystill.seek(0, io.SEEK_END) == 0:
        return redirect(url_for('static', filename='empty.jpg'))
    daystill.seek(0)
    return Response(daystill.read(), mimetype="image/jpeg")

@app.route('/lastcapture.jpg')
def lastCapture():
    if not experimenter.last_captured:
        return redirect(url_for('static', filename='empty.jpg'))
    else:
        try:
            with open(experimenter.last_captured, 'rb') as f:
                return Response(f.read(), mimetype="image/jpeg")
        except:
            return redirect(url_for('static', filename='empty.jpg'))

def takePicture(obj):
    obj.truncate()
    obj.seek(0)
    camera.capture(obj, format="jpeg", quality=90)
    obj.seek(0)

def grabExposure(time):
    global dayshutter, nightshutter
    if time in ['day', 'night']:
        setLive('off')
        if time == 'day':
            takePicture(daystill)
            dayshutter = camera.shutter_speed
        else:
            camera.color_effects = (128, 128)
            takePicture(nightstill)
            camera.color_effects = None
            nightshutter = camera.shutter_speed
        setLive('on')
        return redirect(url_for('exposure', time=time))
    else:
        abort(404)

@not_while_running
@app.route('/focus/<int:value>')
def focus(value):
    value = int(value)
    value = min(1000, max(10, value))
    print("new focus:", value)
    hw.focusCam(value)
    cfg.set('focus', value)
    return redirect(url_for('index'))


@app.route('/experiment', methods=['GET', 'POST'])
def experiment():
    if request.method == 'POST':
        if request.form['action'] == 'start':
            if experimenter.running:
                flash("Experiment is already running.")
            else:
                if request.form.get('duration'): experimenter.duration = int(request.form['duration'])
                else: experimenter.duration = 7
                if request.form.get('delay'): experimenter.delay = int(request.form['delay'])
                else: experimenter.delay = 60
                if request.form.get('directory'): experimenter.dir = os.path.expanduser(os.path.join('~', request.form['directory']))
                else: experimenter.dir = os.path.expanduser('~')
                setLive('off')
                experimenter.next_status = 'run'
                experimenter.status_change.set()
                # give thread time to start before presenting template
                time.sleep(1)
        elif request.form['action'] == 'stop':
            experimenter.stop()
            time.sleep(1)
    df = shutil.disk_usage(experimenter.dir)
    diskspace = round(df.free / 1024 ** 3, 1)
    diskreq = round(experimenter.nshots * 4 * 4 / 1024, 1)
    return render_template('experiment.html', running=experimenter.running, directory=experimenter.dir, 
                           starttime=time.ctime(experimenter.starttime), delay=experimenter.delay,
                           endtime=time.ctime(experimenter.endtime), diskspace=diskspace, duration=experimenter.duration,
                           status=experimenter.status, nshots=experimenter.nshots, diskreq=diskreq)

@not_while_running
@app.route('/setexposure/<time>')
def exposureMode(time):
    if time == 'day':
        camera.shutter_speed = 1000000 // cfg.get('dayshutter')
        hw.LEDControl(False)
        return redirect(url_for('exposure', time='day'))
    elif time == 'night':
        camera.shutter_speed = 1000000 // cfg.get('nightshutter')
        hw.LEDControl(True)
        return redirect(url_for('exposure', time='night'))
    elif time == 'auto':
        camera.shutter_speed = 0
        return redirect(url_for('index'))
    abort(404)

@not_while_running
@app.route('/shutter/<time>/<int:value>')
def shutter(time, value):
    if time in ['day', 'night', 'live']:
        value = max(10, min(value, 1000))
        camera.shutter_speed = 1000000 // value
        return redirect(url_for('index'))
    else:
        abort(404)

@not_while_running
@app.route('/exposure/<time>', methods=['GET', 'POST'])
def exposure(time):
    if not time in ['day', 'night']: abort(404)
    ns=None
    ds=None

    if request.method == 'POST':
        shutter = request.form.get('shutter')
        if shutter:
            shutter = int(shutter)
            shutter = max(10, min(shutter, 1000))
            print("setting new shutter", shutter)
            cfg.set(time + 'shutter', shutter)
        exposureMode(time)
        grabExposure(time)
    else:
        exposureMode(time)
        setLive('on')
        camera.exposure_mode = "off"
    if nightshutter:
        ns = 1000000 // nightshutter
    if dayshutter:
        ds = 1000000 // dayshutter
    return render_template('exposure.html', shutter=cfg.get(time+'shutter'), time=time, 
                           nightshutter=ns, dayshutter=ds)

livestream = False
liveoutput = StreamingOutput()
daystill = io.BytesIO()
nightstill = io.BytesIO()
dayshutter = None
nightshutter = None
zoomer = ZoomObject()
lock = Lock()
cfg = Config()
camera = None
hw = None
experimenter = None

def start(cam, myhw):
    global camera, hw, experimenter
    camera = cam
    hw = myhw
    experimenter = Experimenter(hw=hw, cam=cam)
    experimenter.start()
    if cfg.get('secret') == '':
        secret = hashlib.sha1(os.urandom(16))
        cfg.set('secret', secret.hexdigest())
    app.secret_key = cfg.get('secret')
    try:
        camera.meter_mode = 'spot'
        camera.rotation = 90
        app.run(host='0.0.0.0', port=8080, debug=False, threaded=True)
    finally:
        experimenter.stop()
        experimenter.quit = True
        experimenter.status_change.set()
        if livestream:
            camera.stop_recording()
