#!/usr/bin/env python3
#
# focusserver.py -
#   live view web stream viewer for SPIRO.
#   useful for making focus adjustments.
#   start using ``spiro --focus''.
#
#   heavily copied from the picamera docs.
#
# - Jonas Ohlsson <jonas.ohlsson .a. slu.se>
#

import io
from picamera import PiCamera
import logging
import socketserver
from threading import Condition
from http import server
from fractions import Fraction

PAGE="""\
<html>
<head>
<title>SPIRO live view</title>
</head>
<body>
<h1>SPIRO live view</h1>
<div style="position:relative;">
<img src="stream.mjpg" width="1024" height="768" />
<img src="grid.svg" style="position:absolute; left:0px; top: 0px; width: 1024px; height: 768px;" />
</div>
<p>Zoom <a href="/zoom?-0.1">in</a> / <a href="/zoom?0.1">out</a></p>
<p>Pan <a href="/panx?-0.1">left</a> / <a href="/panx?0.1">right</a> / <a href="/pany?-0.1">up</a> / <a href="/pany?0.1">down</a></p>
<p><a href="/start">Find start position</a> <a href="/90">Rotate 90 degrees</a></p>
<p><a href="/led">Toggle LED</a></p>
</body>
</html>
"""

GRID="""\
<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.1//EN" "http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd">
<svg width="100%" height="100%" viewBox="0 0 3280 2464" version="1.1" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" xml:space="preserve" xmlns:serif="http://www.serif.com/" style="fill-rule:evenodd;clip-rule:evenodd;stroke-linecap:round;stroke-linejoin:round;stroke-miterlimit:1.5;">
    <g id="Layer1">
        <g transform="matrix(0.834385,0,0,0.906683,503.74,219.769)">
            <rect x="204.506" y="-30.735" width="2559.38" height="2385.81" style="fill:none;stroke:rgb(221,52,52);stroke-width:10.33px;"/>
        </g>
        <g transform="matrix(0.969955,0,0,0.969955,78.409,84.5988)">
            <circle cx="1715.26" cy="1649.07" r="833.816" style="fill:none;stroke:rgb(221,52,52);stroke-width:9.28px;"/>
        </g>
    </g>
</svg>
"""

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

class StreamingHandler(server.BaseHTTPRequestHandler):
    def do_GET(self):
        global ledState, roi, panx, pany
        if '?' in self.path:
            (p, arg) = self.path.split('?', maxsplit=1)
        else:
            p = self.path
            arg = ''
        if p == '/':
            self.send_response(301)
            self.send_header('Location', '/index.html')
            self.end_headers()
        elif p == '/index.html' or p == '/zoom' or p == '/led' or p == '/panx' or p == '/pany' or p == '/start' or p == '/90':
            content = PAGE.encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.send_header('Content-Length', len(content))
            self.end_headers()
            self.wfile.write(content)
            if p == '/zoom':
                amt = float(arg)
                roi = roi + amt
                print("ROI increase by %f" % amt)
                if roi > 1:
                    roi = 1.0
                elif roi < 0.1:
                    roi = 0.1
                zoom = (max(0, panx - roi / 2.0), max(0, pany - roi / 2.0), roi, roi)
                print("new zoom:")
                print(zoom)
                camera.zoom = zoom
            elif p == '/panx':
                amt = float(arg)
                panx = panx + amt
                if panx < 0:
                    panx = 0.0
                elif panx > 1:
                    panx = 1.0
                x = panx - roi / 2.0
                y = pany - roi / 2.0
                if x + roi > 1:
                    x = x - (x + roi - 1)
                if y + roi > 1:
                    y = y - (y + roi - 1)
                zoom = (max(0, x), max(0, y), roi, roi)
                print("new zoom:")
                print(zoom)
                camera.zoom = zoom
            elif p == '/pany':
                amt = float(arg)
                pany = pany + amt
                if pany < 0:
                    pany = 0.0
                elif pany > 1:
                    pany = 1.0
                x = panx - roi / 2.0
                y = pany - roi / 2.0
                if x + roi > 1:
                    x = x - (x + roi - 1)
                if y + roi > 1:
                    y = y - (y + roi - 1)
                zoom = (max(0, x), max(0, y), roi, roi)
                print("new zoom:")
                print(zoom)
                camera.zoom = zoom
            elif p == '/led':
                ledState = not ledState
                hw.LEDControl(ledState)
            elif p == '/start':
                hw.findStart()
            elif p == '/90':
                hw.halfStep(100, 0.03)
        elif self.path == '/stream.mjpg':
            self.send_response(200)
            self.send_header('Age', 0)
            self.send_header('Cache-Control', 'no-cache, private')
            self.send_header('Pragma', 'no-cache')
            self.send_header('Content-Type', 'multipart/x-mixed-replace; boundary=FRAME')
            self.end_headers()
            try:
                while True:
                    with output.condition:
                        output.condition.wait()
                        frame = output.frame
                    self.wfile.write(b'--FRAME\r\n')
                    self.send_header('Content-Type', 'image/jpeg')
                    self.send_header('Content-Length', len(frame))
                    self.end_headers()
                    self.wfile.write(frame)
                    self.wfile.write(b'\r\n')
            except Exception as e:
                logging.warning(
                    'Removed streaming client %s: %s',
                    self.client_address, str(e))
        elif self.path == '/grid.svg':
            content = GRID.encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'image/svg+xml')
            self.send_header('Content-Length', len(content))
            self.end_headers()
            self.wfile.write(content)
        else:
            self.send_error(404)
            self.end_headers()

class StreamingServer(socketserver.ThreadingMixIn, server.HTTPServer):
    allow_reuse_address = True
    daemon_threads = True

output = StreamingOutput()
ledState = False
camera = None
hw = None
# region of interest for zooming; 1 means full view
roi = 1
panx = 0.5
pany = 0.5

def focusServer(cam=None, myhw=hw):
    global camera, hw
    camera = cam
    hw = myhw
    camera.meter_mode = 'spot'
    camera.iso = 0
    camera.start_recording(output, format='mjpeg', resize='1024x768')
    try:
        address = ('', 8080)
        print("Web server started on port 8080. Press Ctrl+C to exit.")
        server = StreamingServer(address, StreamingHandler)
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nProgram ended by keyboard interrupt.")
    finally:
        camera.stop_recording()
