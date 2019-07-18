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
from spiro.logger import log
import spiro.webui as webui
import argparse
import textwrap
import sys
import signal
import RPi.GPIO as gpio

parser = argparse.ArgumentParser(description=textwrap.dedent("""\
                                                                SPIRO control software.
                                                                Running this command without any flags starts the web interface.
                                                                Specifying flags will perform those actions, then exit."""))
parser.add_argument('--reset-config', action="store_true", dest="reset",
                    help="reset all configuration values to defaults")
parser.add_argument('--reset-password', action="store_true", dest="resetpw",
                    help="reset web UI password")
parser.add_argument('--install-service', action="store_true", dest="install",
                    help="install systemd user service file")
options = parser.parse_args()

def initCam():
    cam = PiCamera()
    # cam.framerate dictates longest exposure (1/cam.framerate)
    cam.framerate = 5
    cam.iso = 100
    cam.resolution = cam.MAX_RESOLUTION
    cam.rotation = 90
    cam.image_denoise = False
    hw.focusCam(cfg.get('focus'))
    return cam


def installService():
    try:
        os.makedirs(os.path.expanduser('~/.config/systemd/user'), exist_ok=True)
    except OSError as e:
        print("Could not make directory (~/.config/systemd/user):", e)
    try:
        with open(os.path.expanduser('~/.config/systemd/user/spiro.service'), 'w') as f:
            f.write(textwrap.dedent("""\
                [Unit]
                Description=SPIRO control software
                [Service]
                ExecStart=/home/pi/.local/bin/spiro
                [Install]
                WantedBy=default.target
                """))
    except OSError as e:
        print("Could not write file (~/.config/systemd/user/spiro.service):", e)
    print("Systemd service file installed.")


def terminate(sig, frame):
    log("Signal caught -- shutting down.")
    webui.stop()
    hw.motorOn(False)
    cam.close()
    hw.cleanup()
    sys.exit()


cfg = Config()
cam = None
hw = HWControl(cfg)
for sig in [signal.SIGTERM, signal.SIGINT, signal.SIGQUIT, signal.SIGHUP]:
    signal.signal(sig, terminate)

# start here.
def main():
    if options.reset:
        print("Clearing all configuration values.")
        try:
            os.remove(os.path.expanduser('~/.config/spiro/spiro.conf'))
        except OSError as e:
            print("Could not remove file (~/.config/spiro/spiro.conf):", e)
            raise
    if options.install:
        print("Installing systemd service file.")
        installService()
    if options.resetpw:
        print("Resetting web UI password.")
        cfg.set('password', '')
    if any([options.reset, options.resetpw, options.install]):
        sys.exit()

    # no options given, go ahead and start web ui
    global cam
    gpio.setmode(gpio.BCM)
    hw.GPIOInit()
    cam = initCam()
    log('Starting web UI.')
    webui.start(cam, hw)
