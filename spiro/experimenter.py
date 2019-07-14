import threading
import os
import time
from spiro.spiroconfig import Config

class Experimenter(threading.Thread):
    def __init__(self, hw=None, cam=None):
        self.hw = hw
        self.cam = cam
        self.cfg = Config()
        self.delay = 60
        self.duration = 7
        self.dir = os.path.expanduser('~')
        self.starttime = 0
        self.endtime = 0
        self.running = False
        self.status = "Stopped"
        self.daytime = "TBD"
        self.quit = False
        self.stop_experiment = False
        self.status_change = threading.Event()
        self.next_status = ''
        threading.Thread.__init__(self)

    def stop(self):
        self.status = "Stopping"
        self.stop_experiment = True

    def isDaytime(self):
        # determine if it's day or not.
        # XXX determine how long we need to wait, probably less than 6 seconds.
        self.cam.shutter_speed = 0
        oldiso = self.cam.iso
        self.cam.iso = 100
        self.cam.exposure_mode = "auto"
        time.sleep(6)
        exp = self.cam.exposure_speed
        self.cam.iso = oldiso
        self.cam.exposure_mode = "off"
        return exp < self.cfg.get('threshold')


    def setWB(self):
        print("Determining white balance... ", end='', flush=True)
        self.cam.awb_mode = "auto"
        time.sleep(2)
        print("done.")
        g = self.cam.awb_gains
        self.cam.awb_mode = "off"
        self.cam.awb_gains = g


    def takePicture(self, name):
        filename = ""
        prev_daytime = self.daytime
        self.daytime = self.isDaytime()
        
        if self.daytime:
            self.cam.iso = cfg.get('dayiso')
            self.cam.shutter_speed = 1000000 // cfg.get('dayshutter')
            self.cam.color_effects = None
            filename = os.path.join(self.dir, name + "-day.jpg")
        else:
            # turn on led
            self.hw.LEDControl(True)
            self.cam.iso = self.cfg.get('nightiso')
            self.cam.color_effects = (128, 128)
            self.cam.shutter_speed = 1000000 // self.cfg.get('nightshutter')
            time.sleep(2)
            filename = os.path.join(self.dir, name + "-night.jpg")
        
        if prev_daytime != self.daytime and self.daytime and self.cam.awb_mode != "off":
            # if there is a daytime shift, AND it is daytime, AND white balance was not previously set,
            # set the white balance to a fixed value.
            # thus, white balance will only be fixed for the first occurence of daylight.
            self.setWB()

        print("Capturing %s... " % filename, end='', flush=True)
        self.cam.capture(filename) 
       
        if self.daytime:
            print("daytime picture captured OK.")
        else:
            # turn off led
            self.hw.LEDControl(False)
            print("nighttime picture captured OK.")


    def set(self, delay=None, duration=None, dir=None):
        if delay:
            self.delay = delay
        if duration:
            self.duration = duration
        if dir:
            self.dir = os.path.expanduser(os.path.join('~', dir))


    def run(self):
        while not self.quit:
            self.status_change.wait()
            if self.next_status == 'run':
                self.next_status = ''
                self.status_change.clear()
                self.runExperiment()


    def go(self):
        self.next_status = 'run'
        self.status_change.set()                


    def runExperiment(self):
        if self.running:
            raise RuntimeError('An experiment is already running.')

        try:
            self.running = True
            self.status = "Running"
            self.starttime = time.time()
            self.endtime = time.time() + 60 * 60 * 24 * self.duration
            for i in range(4):
                platedir = "plate" + str(i + 1)
                os.makedirs(os.path.join(self.dir, platedir), exist_ok=True)

            while time.time() < self.endtime and not self.stop_experiment:
                loopstart = time.time()
                nextloop = time.time() + 60 * self.delay
                if nextloop > self.endtime:
                    nextloop = self.endtime
                
                for i in range(4):
                    # rotate stage to starting position
                    if(i == 0):
                        self.hw.motorOn(True)
                        print("Finding initial position... ", end='', flush=True)
                        self.hw.findStart(calibration=self.cfg.get('calibration'))
                        print ("done.")
                    else:
                        # rotate cube 90 degrees
                        print("Rotating stage...")
                        self.hw.halfStep(100, 0.03)

                    # wait for the cube to stabilize
                    time.sleep(0.5)

                    now = time.strftime("%Y%m%d-%H%M%S", time.localtime())
                    name = os.path.join("plate" + str(i + 1), "plate" + str(i + 1) + "-" + now)
                    self.takePicture(name)

                self.hw.motorOn(False)

                # this part is "active waiting", rotating the cube slowly over the period of options.delay
                # this ensures consistent lighting for all plates.
                # account for the time spent capturing images.
                secs = 0
                while time.time() < nextloop and not self.stop_experiment:
                    time.sleep(1)
                    secs += 1
                    if self.delay > 900 and secs == int(self.delay / 7.5):
                        # don't bother if delay is very short
                        secs = 0
                        self.hw.motorOn(True)
                        self.hw.halfStep(50, 0.03)
                        self.hw.motorOn(False)

        finally:
            self.cam.framerate = 10
            self.status = "Stopped"
            self.stop_experiment = False
            self.running = False
