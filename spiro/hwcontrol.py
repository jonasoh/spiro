import RPi.GPIO as gpio
import time
import os

class HWControl:
    def __init__(self, cfg):
        self.pins = {
            'LED' : cfg.get('LED'),
            'sensor' : cfg.get('sensor'),
            'PWMa' : cfg.get('PWMa'),
            'PWMb' : cfg.get('PWMb'),
            'coilpin_M11' : cfg.get('coilpin_M11'),
            'coilpin_M12' : cfg.get('coilpin_M12'),
            'coilpin_M21' : cfg.get('coilpin_M21'),
            'coilpin_M22' : cfg.get('coilpin_M22'),
            'stdby' : cfg.get('stdby')
        }


    def GPIOInit(self):
        gpio.setmode(gpio.BCM)
        gpio.setwarnings(False)
        gpio.setup(self.pins['LED'], gpio.OUT)
        gpio.setup(self.pins['sensor'], gpio.IN, pull_up_down=gpio.PUD_DOWN)
        gpio.setup(self.pins['PWMa'], gpio.OUT)
        gpio.setup(self.pins['PWMb'], gpio.OUT)
        gpio.setup(self.pins['coilpin_M11'], gpio.OUT)
        gpio.setup(self.pins['coilpin_M12'], gpio.OUT)
        gpio.setup(self.pins['coilpin_M21'], gpio.OUT)
        gpio.setup(self.pins['coilpin_M22'], gpio.OUT)
        gpio.setup(self.pins['stdby'], gpio.OUT)
        gpio.output(self.pins['PWMa'], True)
        gpio.output(self.pins['PWMb'], True)
        self.LEDControl(False)


    def findStart(self):
        """rotates the imaging stage until the positional switch is activated"""
        while not gpio.input(self.pins['sensor']):
            self.halfStep(1, 0.03)


    # sets the motor pins as element in sequence
    def setStepper(self, M_seq, i):
        gpio.output(self.pins['coilpin_M11'], M_seq[i][0])
        gpio.output(self.pins['coilpin_M12'], M_seq[i][1])
        gpio.output(self.pins['coilpin_M21'], M_seq[i][2])
        gpio.output(self.pins['coilpin_M22'], M_seq[i][3])


    # steps the stepper motor using half steps, "delay" is time between coil change
    # 400 steps is 360 degrees
    def halfStep(self, steps, delay):
        self.motorOn(True)
        time.sleep(0.005) # time for motor to activate
        for i in range(0, steps):
            self.setStepper(self.halfstep_seq, self.seqNumb)
            self.seqNumb += 1
            if(self.seqNumb == 8):
                self.seqNumb = 0
            time.sleep(delay)
        self.motorOn(False)


    # sets motor standby status
    def motorOn(self, value):
        gpio.output(self.pins['stdby'], value)

    # turns on and off led
    def LEDControl(self, value):
        gpio.output(self.pins['LED'], value)

    # focuses the ArduCam motorized focus camera
    # code is from ArduCam GitHub repo
    def focusCam(self, val):
        value = (val << 4) & 0x3ff0
        data1 = (value >> 8) & 0x3f
        data2 = value & 0xf0
        os.system("i2cset -y 1 0x0c %d %d" % (data1,data2))

    # my copy of the pinout
    pins = {}
    
    # state of stepper motor sequence
    seqNumb = 0
    
    # sequence for one coil rotation of stepper motor using half step
    halfstep_seq = [(1,0,0,0), (1,0,1,0), (0,0,1,0), (0,1,1,0),
                    (0,1,0,0), (0,1,0,1), (0,0,0,1), (1,0,0,1)]
