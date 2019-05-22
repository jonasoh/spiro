import json
import os

class Config(object):
    defaults = {
        'calibration' : 8,   # number of steps taken after positional sensor is lit
        'threshold' : 20000, # threshold for day/night determination
        'sensor': 4,         # mini microswitch positional sensor
        'LED': 17,           # pin for turning on/off led
        'PWMa': 8,           # first pwm pin
        'PWMb': 14,          # second pwm pin
        'coilpin_M11': 25,   # ain2
        'coilpin_M12': 24,   # ain1
        'coilpin_M21': 18,   # bin1
        'coilpin_M22': 15,   # bin2
        'stdby': 23,         # stby
    }

    config = {}

    def __init__(self):
        self.cfgdir = os.path.expanduser("~/.config/spiro")
        self.cfgfile = os.path.join(self.cfgdir, "spiro.conf")
        self.read()


    def read(self):
        os.makedirs(self.cfgdir, exist_ok=True)
        if os.path.exists(self.cfgfile):
            with open(self.cfgfile, 'r') as f:
                self.config = json.load(f)


    def write(self):
        with open(self.cfgfile, 'w') as f:
            json.dump(self.config, f, indent=4)


    def get(self, key):
        if key in self.config:
            return self.config[key]
        elif key in self.defaults:
            return self.defaults[key]
        else:
            return None


    def set(self, key, value):
        self.config[key] = value
        self.write()


    def unset(self, key):
        if key in self.config:
            del self.config[key]
            self.write()
