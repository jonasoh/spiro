#!/usr/bin/env python3
#
# petripi.py -
#   script for time-lapse imaging of Petri dishes, with a focus on plants
#   (i.e. it is adapted to day/night cycles).
#
# - Jonas Ohlsson <jonas.ohlsson .a. slu.se>
#

########################################################################
# tunables; general settings
calibration = 4     # number of steps taken after hall sensor is lit
threshold = 60000   # threshold for day/night determination
                    # shutter times longer than this, at iso 100, are
                    # considered to be indicative of nighttime.
########################################################################
# tunables; GPIO pins
hallpin = 4		    # hall sensor
LEDpin = 5		    # pin for turning on/off led
PWMa = 11           # first pwm pin
PWMb = 12           # second pwm pin
coilpin_M11 = 14	# ain2
coilpin_M12 = 15	# ain1
coilpin_M21 = 16	# bin1
coilpin_M22 = 17	# bin2
stdbypin = 18		# stby
########################################################################
# end tunables

from picamera import PiCamera
import argparse
import time
import sys
import os
import RPi.GPIO as gpio
from fractions import Fraction

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

# state of stepper motor sequence -- do not touch
seqNumb = 0

# sequence for one coil rotation of stepper motor using half step
halfstep_seq = [(1,0,0,0), (1,0,1,0), (0,0,1,0), (0,1,1,0),
                (0,1,0,0), (0,1,0,1), (0,0,0,1), (1,0,0,1)]

gpio.setmode(gpio.BCM)
gpio.setwarnings(False)
gpio.setup(LEDpin, gpio.OUT)
gpio.setup(hallpin, gpio.IN)
gpio.setup(PWMa, gpio.OUT)
gpio.setup(PWMb, gpio.OUT)
gpio.setup(coilpin_M11, gpio.OUT)
gpio.setup(coilpin_M12, gpio.OUT)
gpio.setup(coilpin_M21, gpio.OUT)
gpio.setup(coilpin_M22, gpio.OUT)
gpio.setup(stdbypin, gpio.OUT)

gpio.output(stdbypin, False) # turn off motor while not in use
gpio.output(PWMa, True)
gpio.output(PWMb, True)

# sets the motor pins as element in sequence
def setStepper(M_seq, i):
    gpio.output(coilpin_M11, M_seq[i][0])
    gpio.output(coilpin_M12, M_seq[i][1])
    gpio.output(coilpin_M21, M_seq[i][2])
    gpio.output(coilpin_M22, M_seq[i][3])


# steps the stepper motor using half steps, "delay" is time between coil change
# 400 steps is 360 degrees
def halfStep(steps, delay):
    for i in range(0, steps):
            global seqNumb
            setStepper(halfstep_seq, seqNumb)
            seqNumb = seqNumb + 1
            if(seqNumb == 8):
                seqNumb = 0
            time.sleep(delay)


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
    # the number below is the threshold
    return exp < 60000


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
        gpio.output(LEDpin, True)
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
        gpio.output(LEDpin, False)
        print("nighttime picture captured OK.")


# start here.
try:
    if options.focus:
        options.resolution="1024x768"
        cam = initCam()
        import focusserver
        focusserver.focusServer(cam = cam, ledpin = LEDpin)
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
        gpio.output(stdbypin, True) # activate motor
        time.sleep(0.005) # time for motor to activate
        for i in range(4):
            gpio.output(stdbypin, True)
            # rotate stage to starting position
            if(i == 0):
                print("Finding initial position... ", end='', flush=True)
                while gpio.input(hallpin):
                    halfStep(1, 0.03)
                print ("found.")
                halfStep(calibration, 0.03)
            else:
                # rotate cube 90 degrees
                print("Rotating stage...")
                halfStep(100, 0.03)

            # wait for the cube to stabilize
            time.sleep(0.5)

            now = time.strftime("%Y%m%d-%H%M%S", time.localtime())
            name = "plate" + str(i) + "-" + now
            takePicture(name, cam)

        gpio.output(stdbypin, False) # deactivate motor to save energy

        time.sleep(options.delay * 7.5)
        for k in range(7):
            gpio.output(stdbypin, True)
            halfStep(50, 0.03)
            gpio.output(stdbypin, False)
            time.sleep(options.delay * 7.5)

except KeyboardInterrupt:
    print("\nProgram ended by keyboard interrupt. Turning off motor and cleaning up GPIO.")

finally:
    gpio.output(stdbypin,False)
    gpio.cleanup()
    cam.close()
