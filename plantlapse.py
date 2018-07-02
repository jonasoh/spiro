#!/usr/bin/env python3
#
# plantlapse.py -
#   script for time-lapse imaging of petri dishes, with a focus on plants (i.e. it is adapted to day/night cycles).
#   designed to be used with the 5 MP OV5647-based camera with IR illumation, which is widely available. 
#
# - Jonas Ohlsson <jonas.ohlsson .a. slu.se>
#

from picamera import PiCamera
import argparse
import time
import sys
import os

parser = argparse.ArgumentParser(description="By default, plantlapse will run an experiment for 7 days with hourly captures, saving images to the current directory.")

parser.add_argument("-n", "--num-shots", default=168, type=int, dest="nshots", action="store", metavar="N",
                  help="number of shots to capture [default: 168]")
parser.add_argument("-d", "--delay", type=float, default=60, dest="delay", metavar="D",
                  help="time, in minutes, to wait between shots [default: 60]")
parser.add_argument("--disable-motor", default=True, action="store_false", dest="motor",
                  help="disable use of motor [default: false]")
parser.add_argument("--day-shutter", default=100, dest="dayshutter", type=int, metavar="DS",
                  help="daytime shutter in fractions of a second, i.e. for 1/100 specify '100' [default: 100]")
parser.add_argument("--night-shutter", default=50, dest="nightshutter", type=int, metavar="NS",
                  help="nighttime shutter in fractions of a second [default: 50]")
parser.add_argument("--day-iso", default=100, dest="dayiso", type=int,
                  help="set daytime ISO value (0=auto) [default: 100]")
parser.add_argument("--night-iso", default=100, dest="nightiso", type=int,
                  help="set nighttime ISO value (0=auto) [default: 100]")
parser.add_argument("--resolution", default=None, dest="resolution", metavar="RES",
                  help="set camera resolution [default: use maximum supported resolution]")
parser.add_argument("--dir", default=".", dest="dir",
                  help="output pictures to directory 'DIR', creating it if needed [default: use current directory]")
parser.add_argument("--prefix", default="", dest="prefix",
                  help="prefix to use for filenames [default: none]")
parser.add_argument("--auto-wb", default=False, action="store_true", dest="awb",
                  help="adjust white balance between shots (if false, only adjust when day/night shift is detected) [default: false]")
parser.add_argument("--led", default=False, action="store_true", dest="led",
                  help="do not disable camera led; useful for running without GPIO privileges")
parser.add_argument("--preview", nargs="?", default=False, const=60, dest="preview", metavar="P",
                  help="show a live preview of the current settings for P seconds, then exit [default: 60]")
parser.add_argument("-t", "--test", action="store_true", default=False, dest="test",
                  help="capture a test picture as 'test.jpg', then exit")
options = parser.parse_args()

def initCam():
    cam = PiCamera()
    if options.resolution:
        cam.resolution = options.resolution
    else:
        cam.resolution = cam.MAX_RESOLUTION
    cam.meter_mode = "spot"
    if not options.led:
        cam.led = False
    return cam


def isDaytime():
    # determine if it's day or not. give the camera 1 second to adjust.
    cam.shutter_speed = 0
    cam.iso = 100
    time.sleep(1)
    exp = cam.exposure_speed
    print("Exposure speed: %i" % exp)
    return exp < 20000


def setWB():
    sys.stdout.write("Determining white balance... ")
    cam.awb_mode = "auto"
    sys.stdout.flush()
    time.sleep(1)
    print("done.")
    (one, two) = cam.awb_gains
    cam.awb_mode = "off"
    cam.awb_gains = (one, two)


def takePicture(name):
    global daytime
    prev_daytime = daytime
    daytime = isDaytime()

    # set new wb if there's a day/night shift
    if prev_daytime != daytime and not options.awb and not options.test:
        setWB()

    if daytime:
        cam.shutter_speed = 1000000 // options.dayshutter
        cam.iso=options.dayiso
    else:
        cam.shutter_speed = 1000000 // options.nightshutter
        cam.iso=options.nightiso

    filename = os.path.join(options.dir, options.prefix + name + ".jpg")
    sys.stdout.write("Capturing %s... " % filename)
    sys.stdout.flush()
    cam.capture(filename)

    if daytime:
        print("daytime picture captured OK.")
    else:
        print("nighttime picture captured OK.")


# intialize motor before camera to make sure that atexit hook is registered.
if options.motor:
    from Adafruit_MotorHAT import Adafruit_MotorHAT, Adafruit_DCMotor, Adafruit_StepperMotor
    import atexit
  
    mh = Adafruit_MotorHAT()
    def turnOffMotors():
        mh.getMotor(1).run(Adafruit_MotorHAT.RELEASE)

    atexit.register(turnOffMotors)
    motor = mh.getStepper(200, 1)
    motor.setSpeed(10)

# start here.
cam = initCam()
daytime = "TBD"

if options.preview:
    cam.start_preview()
    time.sleep(60)
    cam.stop_preview()
    sys.exit()

if not options.test:
    print("Starting new experiment.\nWill take one picture every %i minutes, in total %i pictures (per plate)." % (options.delay, options.nshots))
    days = options.delay * options.nshots / (60 * 24)
    print("Experiment will continue for approximately %i days." % days)
    if options.motor:
        print("Motor is ENABLED.")
    else:
        print("Motor is DISABLED.")

if options.dir != ".":
    if not os.path.exists(options.dir):
        os.makedirs(options.dir)

for n in range(options.nshots):
    if options.test:
        takePicture("test")
        sys.exit()

    if not options.motor:
        name = time.strftime("%Y%m%d-%H%M%S", time.localtime())
        takePicture(name)
    else:
        for i in range(4):
            now = time.strftime("%Y%m%d-%H%M%S", time.localtime())
            name = "plate" + str(i) + "-" + now
            takePicture(name)

            # rotate cube 90 degrees
            motor.step(49, Adafruit_MotorHAT.FORWARD, Adafruit_MotorHAT.MICROSTEP)
            
            # wait for the cube to stabilize
            time.sleep(0.5)

    time.sleep(options.delay * 60)
