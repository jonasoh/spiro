#!/usr/bin/env python3
#
# spiro.py -
#   script for time-lapse imaging of Petri dishes, with a focus on plants
#   (i.e. it is adapted to day/night cycles).
#
# - Jonas Ohlsson <jonas.ohlsson .a. slu.se>
#

from picamera import PiCamera
import argparse
import time
import sys
import os
import shutil
import RPi.GPIO as gpio
from fractions import Fraction
from spiro.hwcontrol import HWControl
from spiro.spiroconfig import Config
import spiro.webui as webui
import logging, logging.handlers

parser = argparse.ArgumentParser(description="By default, SPIRO will run an experiment for 7 days with hourly captures, saving images to the current directory.")

parser.add_argument("-l", "--duration", type=float, default=7, dest="duration", metavar="L",
                  help="duration, in days, of the experiment [default: 7]")
parser.add_argument("-d", "--delay", type=float, default=60, dest="delay", metavar="D",
                  help="time, in minutes, to wait between shots [default: 60]")
parser.add_argument("--day-shutter", default=100, dest="dayshutter", type=int, metavar="DS",
                  help="daytime shutter in fractions of a second, i.e. for 1/100 specify '100' [default: 100]")
parser.add_argument("--night-shutter", default=10, dest="nightshutter", type=int, metavar="NS",
                  help="nighttime shutter in fractions of a second [default: 5]")
parser.add_argument("--day-iso", default=100, dest="dayiso", type=int,
                  help="set daytime ISO value (0=auto) [default: 100]")
parser.add_argument("--night-iso", default=100, dest="nightiso", type=int,
                  help="set nighttime ISO value (0=auto) [default: 100]")
parser.add_argument("--resolution", dest="resolution", metavar="RES",
                  help="set camera resolution [default: use maximum supported resolution]")
parser.add_argument("--rotation", dest="rotation", metavar="DEG", default=90, type=int,
                  help="set image rotation in degrees [default: 90]")
parser.add_argument("--dir", default=".", dest="dir",
                  help="output pictures to directory 'DIR', creating it if needed [default: use current directory]")
parser.add_argument("--prefix", default="", dest="prefix",
                  help="prefix to use for filenames [default: none]")
parser.add_argument("--auto-wb", action="store_true", dest="awb",
                  help="adjust white balance between shots (if false, only adjust when day/night shift is detected) [default: false]")
parser.add_argument("--live", action="store_true", help="start live view web server")
options = parser.parse_args()

def initCam():
    cam = PiCamera()
    cam.framerate = 15  
    if options.resolution:
        cam.resolution = options.resolution
    else:
        cam.resolution = cam.MAX_RESOLUTION
    cam.rotation = options.rotation
    cam.image_denoise = False
    hw.focusCam(cfg.get('focus'))
    return cam


def isDaytime(cam=None):
    # determine if it's day or not.
    # XXX determine how long we need to wait, probably less than 6 seconds.
    cam.shutter_speed = 0
    oldiso = cam.iso
    cam.iso = 100
    cam.exposure_mode = "auto"
    time.sleep(6)
    exp = cam.exposure_speed
    cam.iso = oldiso
    cam.exposure_mode = "off"
    return exp < threshold


def setWB(cam=None):
    print("Determining white balance... ", end='', flush=True)
    cam.awb_mode = "auto"
    time.sleep(2)
    print("done.")
    g = cam.awb_gains
    cam.awb_mode = "off"
    cam.awb_gains = g


def takePicture(name, cam=None):
    global daytime
    filename = ""
    prev_daytime = daytime
    daytime = isDaytime(cam = cam)
    
    if daytime:
        cam.iso = options.dayiso
        cam.shutter_speed = 1000000 // options.dayshutter
        cam.color_effects = None
        filename = os.path.join(options.dir, options.prefix + name + "-day.jpg")
    else:
        # turn on led
        hw.LEDControl(True)
        cam.iso = options.nightiso
        cam.color_effects = (128, 128)
        cam.shutter_speed = 1000000 // options.nightshutter
        time.sleep(2)
        filename = os.path.join(options.dir, options.prefix + name + "-night.jpg")
    
    if not options.awb and prev_daytime != daytime and daytime and cam.awb_mode != "off":
        # if there is a daytime shift, AND it is daytime, AND white balance was not previously set,
        # set the white balance to a fixed value.
        # thus, white balance will only be fixed for the first occurence of daylight.
        setWB(cam)

    print("Capturing %s... " % filename, end='', flush=True)
    cam.capture(filename) 
   
    if daytime:
        print("daytime picture captured OK.")
    else:
        # turn off led
        hw.LEDControl(False)
        print("nighttime picture captured OK.")


cfg = Config()
threshold = cfg.get('threshold')
calibration = cfg.get('calibration')
daytime = "TBD"
hw = HWControl(cfg)
logging.basicConfig(format='%(asctime)s %(message)s')
logger = logging.getLogger()
handler = logging.handlers.RotatingFileHandler(os.path.expanduser('~/spiro.log'), maxBytes=10*1024**2, backupCount=4)
logger.addHandler(handler)

# start here.
def main():
    hw.GPIOInit()
    hw.motorOn(False) # turn off motor while not in use

    try:
        if options.live:
            cam = initCam()
            cam.framerate = 10
            logger.debug('Starting web UI.')
            webui.start(cam, hw)
            sys.exit()

    except KeyboardInterrupt:
        print("\nProgram ended by keyboard interrupt. Turning off motor and cleaning up GPIO.")

    finally:
        hw.motorOn(False)
        cam.close()
        gpio.cleanup()
