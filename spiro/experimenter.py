import threading
import os
import time
from statistics import mean
from collections import deque
from spiro.config import Config
from spiro.logger import log

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
        self.last_captured = None
        self.nshots = 0
        threading.Thread.__init__(self)

    def stop(self):
        self.status = "Stopping"
        self.next_status = ''
        self.stop_experiment = True
        log("Stopping running experiment...")

    def isDaytime(self):
        # determine if it's day or not.
        self.cam.exposure_mode = "auto"
        self.cam.shutter_speed = 0
        self.cam.meter_mode = 'matrix'

        # to determine day/night we use a rotating list of the last 5 exposure readings
        # exposure may take a very long time to settle, so we use some heuristics to determine whether it is day or night
        itsday = 'TBD'
        exps = deque([-1,100,-1,100,-1])

        while itsday == 'TBD':
            time.sleep(1)
            exps.popleft()
            # round the exposure to nearest 1000
            exps.append(self.cam.exposure_speed // 1000)

            if exps[4] < exps[3] < exps[2] < exps[1] < exps[0]:
                if mean(exps) < 33:
                    # decreasing exposure, value below 33000
                    itsday = True
            elif exps[4] > exps[3] > exps[2] > exps[1] > exps[0]:
                if mean(exps) > 33:
                    # increasing exposure time, value above 33999
                    itsday = False
            elif exps[4] == exps[3] == exps[2] == exps[1] == exps[0]:
                if mean(exps) < 33:
                    # stable exposure, value below 33000
                    itsday = True
                elif mean(exps) > 33:
                    # stable exposure, value above 33999
                    itsday = False

        return itsday


    def setWB(self):
        log("Determining white balance.")
        self.cam.awb_mode = "auto"
        time.sleep(2)
        g = self.cam.awb_gains
        self.cam.awb_mode = "off"
        self.cam.awb_gains = g


    def takePicture(self, name):
        filename = ""
        prev_daytime = self.daytime
        self.daytime = self.isDaytime()
        
        if self.daytime:
            self.cam.shutter_speed = 1000000 // self.cfg.get('dayshutter')
            self.cam.color_effects = None
            filename = os.path.join(self.dir, name + "-day.jpg")
        else:
            # turn on led
            self.hw.LEDControl(True)
            time.sleep(0.5)

            self.cam.color_effects = (128, 128)
            self.cam.shutter_speed = 1000000 // self.cfg.get('nightshutter')
            filename = os.path.join(self.dir, name + "-night.jpg")
        
        if prev_daytime != self.daytime and self.daytime and self.cam.awb_mode != "off":
            # if there is a daytime shift, AND it is daytime, AND white balance was not previously set,
            # set the white balance to a fixed value.
            # thus, white balance will only be fixed for the first occurence of daylight.
            self.setWB()

        log("Capturing %s." % filename)
        self.cam.exposure_mode = "off"
        self.cam.capture(filename)
        self.last_captured = filename
        self.cam.color_effects = None
        self.cam.shutter_speed = 0
        # we leave the cam in auto exposure mode to improve daytime assessment performance
        self.cam.exposure_mode = "auto"
       
        if not self.daytime:
            # turn off led
            self.hw.LEDControl(False)


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
            self.status = "Initiating"
            self.starttime = time.time()
            self.endtime = time.time() + 60 * 60 * 24 * self.duration
            self.last_captured = None
            if self.delay == 0: self.delay = 0.001
            self.nshots = self.duration * 24 * 60 // self.delay
            self.cam.exposure_mode = "auto"
            self.cam.shutter_speed = 0

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
                        self.status = "Finding start position"
                        log("Finding initial position.")
                        self.hw.findStart(calibration=self.cfg.get('calibration'))
                        log("Found initial position.")
                    else:
                        self.status = "Imaging"
                        # rotate cube 90 degrees
                        log("Rotating stage.")
                        self.hw.halfStep(100, 0.03)

                    # wait for the cube to stabilize
                    time.sleep(0.5)

                    now = time.strftime("%Y%m%d-%H%M%S", time.localtime())
                    name = os.path.join("plate" + str(i + 1), "plate" + str(i + 1) + "-" + now)
                    self.takePicture(name)

                self.nshots -= 1
                self.hw.motorOn(False)

                # this part is "active waiting", rotating the cube slowly over the period of options.delay
                # this ensures consistent lighting for all plates.
                # account for the time spent capturing images.
                self.status = "Waiting"
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
            log("Experiment stopped.")
            self.cam.color_effects = None
            self.status = "Stopped"
            self.stop_experiment = False
            self.running = False
            self.cam.exposure_mode = "auto"
            self.cam.meter_mode = 'spot'
