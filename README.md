# plantlapse
Raspberry Pi timelapse imaging of seed growth. For now, this is mainly for internal use and the script contains constants which need to be modified for proper function (e.g. exposure speed cutoffs for day/night determination). 

## example

<img src="examples/day-cropped-optim.gif">

## usage

```
usage: plantlapse [-h] [-n N] [-d D] [--disable-motor] [--day-shutter DS]
                  [--night-shutter NS] [--day-iso DAYISO]
                  [--night-iso NIGHTISO] [--resolution RES] [--dir DIR]
                  [--prefix PREFIX] [--auto-wb] [--led] [--preview [P]] [-t]

By default, plantlapse will run an experiment for 7 days with hourly captures,
saving images to the current directory.

optional arguments:
  -h, --help            show this help message and exit
  -n N, --num-shots N   number of shots to capture [default: 168]
  -d D, --delay D       time, in minutes, to wait between shots [default: 60]
  --disable-motor       disable use of motor [default: false]
  --day-shutter DS      daytime shutter in fractions of a second, i.e. for
                        1/100 specify '100' [default: 100]
  --night-shutter NS    nighttime shutter in fractions of a second [default:
                        50]
  --day-iso DAYISO      set daytime ISO value (0=auto) [default: 100]
  --night-iso NIGHTISO  set nighttime ISO value (0=auto) [default: 100]
  --resolution RES      set camera resolution [default: use maximum supported
                        resolution]
  --dir DIR             output pictures to directory 'DIR', creating it if
                        needed [default: use current directory]
  --prefix PREFIX       prefix to use for filenames [default: none]
  --auto-wb             adjust white balance between shots (if false, only
                        adjust when day/night shift is detected) [default:
                        false]
  --led                 do not disable camera led; useful for running without
                        GPIO privileges
  --preview [P]         show a live preview of the current settings for P
                        seconds, then exit [default: 60]
  -t, --test            capture a test picture as 'test.jpg', then exit
```

## requirements and installation

Plantlapse should run under Raspbian on any Raspberry Pi model with a camera interface (only tested on the Zero W). It works with both the official camera module as well as with third-party cameras. The one we use is [this 5 MP OV5647-based camera with near-IR illumation](https://www.modmypi.com/raspberry-pi/camera/camera-boards/raspberry-pi-night-vision-camera). 

To install, first enable the camera module using raspi-config, and reboot. 

```
sudo raspi-config
```

Then, install the dependencies: 

```
# python3-rpi.gpio is required for turning off camera led
sudo apt-get install python3-picamera python3-rpi.gpio
```

We recommend setting up a softlink to plantlapse.py somewhere in the default $PATH to facilitate its usage: 

```
sudo ln -s ~pi/plantlapse/plantlapse.py /usr/local/bin/plantlapse
```

In order to use the stepper motor functionality, you should also install [Adafruit's MotorHAT library](https://github.com/adafruit/Adafruit-Motor-HAT-Python-Library).

You should now be all set to start using plantlapse!

**Note:** Due to the unreliability of SD cards, we recommend that images be captured to a directory on another medium, such as a network-mounted filesystem or a USB drive (or at least to a separate partition on the SD card if this is not an option). Constantly writing to the SD cards can, in our experience, lead to irrecoverable errors on the root filesystem which may require a reinstallation of the OS. 
