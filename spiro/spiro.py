#!/usr/bin/env python3
#
# spiro.py -
#   script for time-lapse imaging of Petri dishes, with a focus on plants
#   (i.e. it is adapted to day/night cycles).
#
# - Jonas Ohlsson <jonas.ohlsson .a. slu.se>
#

import os
from picamera import PiCamera
from spiro.hwcontrol import HWControl
from spiro.spiroconfig import Config
import spiro.webui as webui
import logging, logging.handlers

def initCam():
    cam = PiCamera()
    cam.framerate = 15  
    cam.resolution = cam.MAX_RESOLUTION
    cam.rotation = 90
    cam.image_denoise = False
    hw.focusCam(cfg.get('focus'))
    return cam

cfg = Config()
daytime = "TBD"
hw = HWControl(cfg)
logging.basicConfig(format='%(asctime)s %(message)s')
logger = logging.getLogger()
handler = logging.handlers.RotatingFileHandler(os.path.expanduser('~/spiro.log'), maxBytes=10*1024**2, backupCount=4)
logger.addHandler(handler)

# start here.
def main():
    hw.GPIOInit()

    try:
        cam = initCam()
        cam.framerate = 10
        logger.debug('Starting web UI.')
        webui.start(cam, hw)

    except KeyboardInterrupt:
        print("\nProgram ended by keyboard interrupt. Turning off motor and cleaning up GPIO.")

    finally:
        hw.motorOn(False)
        cam.close()
        hw.cleanup()
