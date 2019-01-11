#!/usr/bin/env python3
#
# petripi.py -
#   script for time-lapse imaging of Petri dishes, with a focus on plants (i.e. it is adapted to day/night cycles).
#   designed to be used with the Waveshare 5 MP OV5647-based camera with IR illumation, which is widely available. 
#
# - Jonas Ohlsson <jonas.ohlsson .a. slu.se>
#

from picamera import PiCamera
import argparse
import time
import sys
import os
import RPi.GPIO as gpio

parser = argparse.ArgumentParser(description="By default, PetriPi will run an experiment for 7 days with hourly captures, saving images to the current directory.")

parser.add_argument("-n", "--num-shots", default=168, type=int, dest="nshots", action="store", metavar="N",
                  help="number of shots to capture [default: 168]")
parser.add_argument("-d", "--delay", type=float, default=60, dest="delay", metavar="D",
                  help="time, in minutes, to wait between shots [default: 60]")
parser.add_argument("--daycam", default=1, dest="daycam", type=int, metavar='DC',
                  help="daylight camera number [default: 0]")
parser.add_argument("--nightcam", default=0, dest="nightcam", type=int, metavar='NC',
                  help="night camera number [default: 1]")
parser.add_argument("--day-shutter", default=100, dest="dayshutter", type=int, metavar="DS",
                  help="daytime shutter in fractions of a second, i.e. for 1/100 specify '100' [default: 100]")
parser.add_argument("--night-shutter", default=50, dest="nightshutter", type=int, metavar="NS",
                  help="nighttime shutter in fractions of a second [default: 50]")
parser.add_argument("--day-iso", default=100, dest="dayiso", type=int,
                  help="set daytime ISO value (0=auto) [default: 100]")
parser.add_argument("--night-iso", default=400, dest="nightiso", type=int,
                  help="set nighttime ISO value (0=auto) [default: 400]")
parser.add_argument("--resolution", default=None, dest="resolution", metavar="RES",
                  help="set camera resolution [default: use maximum supported resolution]")
parser.add_argument("--dir", default=".", dest="dir",
                  help="output pictures to directory 'DIR', creating it if needed [default: use current directory]")
parser.add_argument("--prefix", default="", dest="prefix",
                  help="prefix to use for filenames [default: none]")
parser.add_argument("--auto-wb", default=False, action="store_true", dest="awb",
                  help="adjust white balance between shots (if false, only adjust when day/night shift is detected) [default: false]")
parser.add_argument("-t", "--test", action="store_true", default=False, dest="test",
                  help="capture a test picture as 'test.jpg', then exit")

options = parser.parse_args()

# GPIO pins for electronics
hallpin = 4		# Hall sensor
LEDpin1 = 5		# IR illuminator 1
LEDpin2 = 6		# IR illuminator 2
PWMa = 11		# PWM pin a
PWMb = 12		# PWM pin b

# Motor pins
coilpin_M11 = 14	# ain2
coilpin_M12 = 15	# ain1
coilpin_M21 = 16	# bin1
coilpin_M22 = 17	# bin2
stdbypin = 18		# standby

seqNumb = 0		# State of stepper motor sequence
mdelay = 0.05		# Stepper motor movement delay

# Number of steps to rotate motor after Hall sensor is lit
calibration = 37

# Sequence for one coil rotation of stepper motor using half step
halfstep_seq = [(1,0,0,0), (1,0,1,0), (0,0,1,0), (0,1,1,0), (0,1,0,0), (0,1,0,1), (0,0,0,1), (1,0,0,1)]

# Initializes GPIO
def initGPIO():
    gpio.setmode(gpio.BCM)
    gpio.setwarnings(False)
    gpio.setup(LEDpin1,gpio.OUT)
    gpio.setup(LEDpin2,gpio.OUT)
    gpio.setup(hallpin,gpio.OUT)
    gpio.setup(hallpin,gpio.IN)
    gpio.setup(PWMa,gpio.OUT)
    gpio.setup(PWMb,gpio.OUT)
    gpio.setup(coilpin_M11,gpio.OUT)
    gpio.setup(coilpin_M12,gpio.OUT)
    gpio.setup(coilpin_M21,gpio.OUT)
    gpio.setup(coilpin_M22,gpio.OUT)
    gpio.setup(stdbypin,gpio.OUT)

    gpio.output(stdbypin,False) # turn off motor while not in use
    gpio.output(PWMa,True)
    gpio.output(PWMb,True)


# Sets the motor pins as element in sequence
def setStepper(M_seq,i):
    gpio.output(coilpin_M11,M_seq[i][0])
    gpio.output(coilpin_M12,M_seq[i][1])
    gpio.output(coilpin_M21,M_seq[i][2])
    gpio.output(coilpin_M22,M_seq[i][3])


# Steps the stepper motor using half step, "delay" is time between coil change
# 400 steps is 360 degrees
def halfStep(steps, delay):
    for i in range(0, steps):
        global seqNumb
        setStepper(halfstep_seq, seqNumb)
        seqNumb += 1
        if (seqNumb == 8):
            seqNumb = 0
        time.sleep(delay)


def initCam(num=0):
    # XXX don't hardcode pins like this
    cam = PiCamera(camera_num = num)

    if options.resolution:
        cam.resolution = options.resolution
    else:
        cam.resolution = cam.MAX_RESOLUTION

    cam.meter_mode = "spot"
    return cam


def isDaytime(cam=None):
    # determine if it's day or not. give the camera 1 second to adjust.
    cam.shutter_speed = 0
    cam.iso = 100
    time.sleep(1)
    exp = cam.exposure_speed
    print("Exposure speed: %i" % exp)
    return exp < 24000


def setWB(cam=None):
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

    # Turn on LEDs
    gpio.output(LEDpin1, True)
    gpio.output(LEDpin2, True)

    prev_daytime = daytime
    daytime = isDaytime(cam = daycam)

    # set new wb if there's a day/night shift
    if prev_daytime != daytime and not options.awb and not options.test:
        if daytime:
            setWB(cam = daycam)
        else:
            setWB(cam = nightcam)

    cam = None
    
    if daytime:
        cam = daycam
        cam.shutter_speed = 1000000 // options.dayshutter
    else:
        cam = nightcam
        cam.shutter_speed = 1000000 // options.nightshutter

    filename = os.path.join(options.dir, options.prefix + name + ".jpg")
    sys.stdout.write("Capturing %s... " % filename)
    sys.stdout.flush()
    cam.capture(filename)

    # Turn off LEDs
    gpio.output(LEDpin1, False)
    gpio.output(LEDpin2, False)

    if daytime:
        print("daytime picture captured OK.")
    else:
        print("nighttime picture captured OK.")


# start here.
try:
    initGPIO()
    daycam = initCam(num = options.daycam)
    nightcam = initCam(num = options.nightcam)
    daycam.iso = options.dayiso
    nightcam.iso = options.nightiso
    daytime = "TBD"

    if not options.test:
        print("Welcome to PetriPi!\n\nStarting new experiment.\nWill take one picture every %i minutes, in total %i pictures (per plate)." % (options.delay, options.nshots))
        days = options.delay * options.nshots / (60 * 24)
        print("Experiment will continue for approximately %i days." % days)

    if options.dir != ".":
        if not os.path.exists(options.dir):
            os.makedirs(options.dir)

    for n in range(options.nshots):
        if options.test:
            takePicture("test")
            sys.exit()

        else:
            gpio.output(stdbypin, True) # activate motor
            time.sleep(0.005) # time for motor to activate

            for i in range(4):
                gpio.output(stdbypin, True)
                # rotate cube to starting position
                if (i == 0):
                    while gpio.input(hallpin):
                        halfStep(1, mdelay)
                        time.sleep(0.02)

                    print ("\nMagnet detected by hall effect sensor")
                    halfStep(calibration, mdelay)
                else:
                    # rotate cube 90 degrees
                    print("Cube 90 degree")
                    halfStep(100, mdelay)

                # wait for the cube to stabilize
                time.sleep(0.5)

                now = time.strftime("%Y%m%d-%H%M%S", time.localtime())
                name = "plate" + str(i) + "-" + now
                takePicture(name)

        # Deactivate motor to save energy
        gpio.output(stdbypin, False)

        # Rotate the cube during sleep to ensure consistent lighting of plates
        time.sleep(options.delay * 7.5)
        for k in range(7):
            time.sleep(options.delay * 7.5)
            gpio.output(stdbypin, True)
            halfStep(50, mdelay)
            gpio.output(stdbypin, False)

except KeyboardInterrupt:
    print("\nUser ended program by keyboard interrupt. Turning off motor and cleaning GPIO.")

finally:
    # Turn off LEDs and motor
    gpio.output(LEDpin1, False)
    gpio.output(LEDpin2, False)
    gpio.output(stdbypin, False)

    gpio.cleanup()
