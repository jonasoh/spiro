import RPi.GPIO as gpio
import time

# my copy of the pinout
pins = {}

# state of stepper motor sequence
seqNumb = 0

# sequence for one coil rotation of stepper motor using half step
halfstep_seq = [(1,0,0,0), (1,0,1,0), (0,0,1,0), (0,1,1,0),
                (0,1,0,0), (0,1,0,1), (0,0,0,1), (1,0,0,1)]

def setPins(mypins):
    global pins
    pins = mypins


def GPIOInit():
    gpio.setmode(gpio.BCM)
    gpio.setwarnings(False)
    gpio.setup(pins['LED'], gpio.OUT)
    gpio.setup(pins['sensor'], gpio.IN)
    gpio.setup(pins['PWMa'], gpio.OUT)
    gpio.setup(pins['PWMb'], gpio.OUT)
    gpio.setup(pins['coilpin_M11'], gpio.OUT)
    gpio.setup(pins['coilpin_M12'], gpio.OUT)
    gpio.setup(pins['coilpin_M21'], gpio.OUT)
    gpio.setup(pins['coilpin_M22'], gpio.OUT)
    gpio.setup(pins['stdby'], gpio.OUT)
    gpio.output(pins['PWMa'], True)
    gpio.output(pins['PWMb'], True)


def findStart():
    """rotates the imaging stage until the positional switch is activated"""
    while gpio.input(pins['sensor']):
        halfStep(1, 0.03)


# sets the motor pins as element in sequence
def setStepper(M_seq, i):
    gpio.output(pins['coilpin_M11'], M_seq[i][0])
    gpio.output(pins['coilpin_M12'], M_seq[i][1])
    gpio.output(pins['coilpin_M21'], M_seq[i][2])
    gpio.output(pins['coilpin_M22'], M_seq[i][3])


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


# sets motor standby status
def motorOn(value):
    gpio.output(pins['stdby'], value)


# turns on and off led
def LEDControl(pins, value):
    gpio.output(pins['LED'], value)
