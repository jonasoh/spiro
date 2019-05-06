#!/usr/bin/env python3
#
# petripi.py -
#   script for time-lapse imaging of Petri dishes, with a focus on plants
#   (i.e. it is adapted to day/night cycles).
#
# - Jonas Ohlsson <jonas.ohlsson .a. slu.se>
#

#########################################################################
# tunables; general settings
calibration = 4    # number of steps taken after positional sensor is lit
threshold = 32000  # threshold for day/night determination
                   # shutter times longer than this, at iso 100, are
                   # considered to be indicative of nighttime.
#########################################################################
# tunables; GPIO pins
pins = {
'sensor': 23,      # positional sensor
'LED': 25,         # pin for turning on/off led
'PWMa': 17,        # first pwm pin
'PWMb': 16,        # second pwm pin
'coilpin_M11': 27, # ain2
'coilpin_M12': 22, # ain1
'coilpin_M21': 6,  # bin1
'coilpin_M22': 26, # bin2
'stdby': 5,        # stby
}
#########################################################################
# end tunables

from picamera import PiCamera
import argparse
import time
import sys
import os
import RPi.GPIO as gpio
from fractions import Fraction
from hwcontrol import HWControl

parser = argparse.ArgumentParser(description="By default, PetriPi will run an experiment for 7 days with hourly captures, saving images to the current directory.")

parser.add_argument("-n", "--num-shots", default=168, type=int, dest="nshots", action="store", metavar="N",
                  help="number of shots to capture [default: 168]")
parser.add_argument("-d", "--delay", type=float, default=60, dest="delay", metavar="D",
                  help="time, in minutes, to wait between shots [default: 60]")
parser.add_argument("--day-shutter", default=100, dest="dayshutter", type=int, metavar="DS",
                  help="daytime shutter in fractions of a second, i.e. for 1/100 specify '100' [default: 100]")
parser.add_argument("--night-shutter", default=1, dest="nightshutter", type=int, metavar="NS",
                  help="nighttime shutter in fractions of a second [default: 5]")
parser.add_argument("--day-iso", default=100, dest="dayiso", type=int,
                  help="set daytime ISO value (0=auto) [default: 100]")
parser.add_argument("--night-iso", default=800, dest="nightiso", type=int,
                  help="set nighttime ISO value (0=auto) [default: 800]")
parser.add_argument("--resolution", dest="resolution", metavar="RES",
                  help="set camera resolution [default: use maximum supported resolution]")
parser.add_argument("--dir", default=".", dest="dir",
                  help="output pictures to directory 'DIR', creating it if needed [default: use current directory]")
parser.add_argument("--prefix", default="", dest="prefix",
                  help="prefix to use for filenames [default: none]")
parser.add_argument("--auto-wb", action="store_true", dest="awb",
                  help="adjust white balance between shots (if false, only adjust when day/night shift is detected) [default: false]")
parser.add_argument("--focus", action="store_true", help="start web server for focus assessment")
options = parser.parse_args()

def initCam():
    cam = PiCamera(framerate_range = (Fraction(1, 6), 30))
    if options.resolution:
        cam.resolution = options.resolution
    else:
        cam.resolution = cam.MAX_RESOLUTION
    cam.meter_mode = "spot"
    return cam


def isDaytime(cam=None):
    # determine if it's day or not. give the camera 1 second to adjust.
    cam.shutter_speed = 0
    oldiso = cam.iso
    oldmode = cam.exposure_mode
    cam.iso = 100
    cam.exposure_mode = "auto"
    time.sleep(1)
    exp = cam.exposure_speed
    cam.iso = oldiso
    cam.exposure_mode = oldmode
    return exp < threshold


def setWB(cam=None):
    sys.stdout.write("Determining white balance... ")
    cam.awb_mode = "auto"
    sys.stdout.flush()
    time.sleep(1)
    print("done.")
    (one, two) = cam.awb_gains
    cam.awb_mode = "off"
    cam.awb_gains = (one, two)


def takePicture(name, cam=None):
    global daytime
    filename = ""
    prev_daytime = daytime
    daytime = isDaytime(cam = cam)
    
    if daytime:
        cam.iso = options.dayiso
        cam.shutter_speed = 1000000 // options.dayshutter
        cam.exposure_mode = "auto"
        filename = os.path.join(options.dir, options.prefix + name + "-day.jpg")
    else:
        # turn on led
        hw.LEDControl(pins, True)
        cam.exposure_mode = "off"
        cam.iso = options.nightiso
        cam.framerate = Fraction(1, 6)
        cam.shutter_speed = 1000000 // options.nightshutter
        time.sleep(2)
        filename = os.path.join(options.dir, options.prefix + name + "-night.jpg")

    sys.stdout.write("Capturing %s... " % filename)
    sys.stdout.flush()
    cam.capture(filename)

    if daytime:
        print("daytime picture captured OK.")
    else:
        # turn off led
        hw.LEDControl(pins, False)
        print("nighttime picture captured OK.")


# start here.
if (__name__) == '__main__':
    hw = HWControl(pins)
    hw.GPIOInit()
    hw.motorOn(False) # turn off motor while not in use

    try:
        if options.focus:
            # set lower resolution to reduce risk of PiCamera crashing :\
            options.resolution="1640x1232"
            cam = initCam()
            import focusserver
            focusserver.focusServer(cam, hw)
            sys.exit()

        cam = initCam()
        daytime = "TBD"

        print("Welcome to PetriPi!\n\nStarting new experiment.\nWill take one picture every %i minutes, in total %i pictures (per plate)." % (options.delay, options.nshots))
        days = options.delay * options.nshots / (60 * 24)
        print("Experiment will continue for approximately %i days." % days)

        if options.dir != ".":
            if not os.path.exists(options.dir):
                os.makedirs(options.dir)

        for n in range(options.nshots):
            for i in range(4):
                # rotate stage to starting position
                if(i == 0):
                    print("Finding initial position... ", end='', flush=True)
                    hw.findStart()
                    print ("found.")
                    hw.halfStep(calibration, 0.03)
                else:
                    # rotate cube 90 degrees
                    print("Rotating stage...")
                    hw.halfStep(100, 0.03)

                # wait for the cube to stabilize
                time.sleep(0.5)

                now = time.strftime("%Y%m%d-%H%M%S", time.localtime())
                name = "plate" + str(i) + "-" + now
                takePicture(name, cam)

            time.sleep(options.delay * 7.5)
            for k in range(7):
                hw.halfStep(50, 0.03)
                time.sleep(options.delay * 7.5)

    except KeyboardInterrupt:
        print("\nProgram ended by keyboard interrupt. Turning off motor and cleaning up GPIO.")

    finally:
        hw.motorOn(False)
        gpio.cleanup()
        cam.close()
