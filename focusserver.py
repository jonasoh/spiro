import io
from picamera import PiCamera
import logging
import socketserver
from threading import Condition
from http import server
import RPi.GPIO as gpio
from fractions import Fraction

PAGE="""\
<html>
<head>
<title>PetriPi live view</title>
</head>
<body>
<h1>PetriPi live view</h1>
<img src="stream.mjpg" width="1024" height="768" />
<p><a href="/zoom">Zoomed in view</a></p>
<p><a href="/unzoom">Full view</a></p>
<p><a href="/led">Toggle LED</a></p>
</body>
</html>
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
        if self.path == '/':
            self.send_response(301)
            self.send_header('Location', '/index.html')
            self.end_headers()
        elif self.path == '/index.html' or self.path == '/zoom' or self.path == '/unzoom' or self.path=='/led':
            if self.path == '/zoom':
                camera.zoom = (0.4, 0.4, 0.2, 0.2)
            elif self.path == '/unzoom':
                camera.zoom = (0.0, 0.0, 1.0, 1.0)
            elif self.path == '/led':
                ledState = not ledState
                gpio.output(LEDpin, ledState)
            content = PAGE.encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.send_header('Content-Length', len(content))
            self.end_headers()
            self.wfile.write(content)
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
        else:
            self.send_error(404)
            self.end_headers()

class StreamingServer(socketserver.ThreadingMixIn, server.HTTPServer):
    allow_reuse_address = True
    daemon_threads = True


output = StreamingOutput()
camera = None
ledpin = None
ledState = False

def focusServer(cam=None, ledpin=None):
    global camera
    camera = cam
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
        cam.stop_recording()
        if (__name__ == '__main__'):
            cam.close()

if (__name__ == '__main__'):
    print("Starting focusing server, using LED pin 5.")
    camera = PiCamera(framerate_range = (Fraction(1, 10), 15), resolution = '3280x2464')
    focusServer(cam=camera, ledpin=5)
