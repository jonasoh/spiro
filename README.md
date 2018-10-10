# PetriPi
Raspberry Pi timelapse imaging of seed growth. For now, this is mainly for internal use and the script contains constants which need to be modified for proper function (e.g. exposure speed cutoffs for day/night determination). 

PetriPi supports imaging of up to four plates at the same time, using a "cube holder" for the Petri dishes. A blueprint for an old version of the cube can be found [here](blueprints/aluminium-cube.pdf). Newer blueprints, designed for 3D printing, will be uploaded soon. 

## hardware

This is the current state of the PetriPi hardware, housed inside a growth chamber. This iteration uses 3D printed parts for housing the cameras and other electronics, as well as for the dish-holding cube. 

<img src="https://raw.githubusercontent.com/jonasoh/web/master/petripi-3dprinted.jpg">

## example

<img src="https://github.com/jonasoh/web/raw/master/day-cropped-optim.gif">
(Note: the image quality has improved by a large degree since this image was captured.)

## usage

```
usage: petripi [-h] [-n N] [-d D] [--disable-motor] [--i2c I2C] [--daycam DC]
               [--nightcam NC] [--day-shutter DS] [--night-shutter NS]
               [--day-iso DAYISO] [--night-iso NIGHTISO] [--resolution RES]
               [--dir DIR] [--prefix PREFIX] [--auto-wb] [-t]

By default, PetriPi will run an experiment for 7 days with hourly captures,
saving images to the current directory.

optional arguments:
  -h, --help            show this help message and exit
  -n N, --num-shots N   number of shots to capture [default: 168]
  -d D, --delay D       time, in minutes, to wait between shots [default: 60]
  --disable-motor       disable use of motor [default: false]
  --i2c I2C             I2C bus of the MotorHAT [default: 3]
  --daycam DC           daylight camera number [default: 0]
  --nightcam NC         night camera number [default: 1]
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
  -t, --test            capture a test picture as 'test.jpg', then exit
```

## requirements and installation

PetriPi is currently known to run only on the Raspberry Pi Compute Module 3. It works with both the official camera module as well as with third-party cameras. We use the official V2 camera for daylight imaging and [this 5 MP OV5647-based camera with near-IR illumation](https://www.modmypi.com/raspberry-pi/camera/camera-boards/raspberry-pi-night-vision-camera) for night time images. 

To install, first enable dual camera interfacing using the [official instructions](https://www.raspberrypi.org/documentation/hardware/computemodule/cmio-camera.md).   

Then, install the dependencies: 

```
sudo apt-get install python3-picamera
```

We recommend setting up a softlink to petripi.py somewhere in the default $PATH to facilitate its usage: 

```
sudo ln -s ~pi/petripi/petripi.py /usr/local/bin/petripi
```

Add the following line to /boot/config.txt to disable the camera's LED (reduces reflections):

```
disable_camera_led=1
```

In order to use the stepper motor functionality, you should also install [Adafruit's MotorHAT library](https://github.com/adafruit/Adafruit-Motor-HAT-Python-Library).

You should now be all set to start using PetriPi! To start a new experiment, simply create a folder to contain your images, and type `petripi`. By default, this will start an experiment that takes one image per hour for 7 days, utilizing the stepper motor functionality for imaging of multiple plates. 

**Note:** Due to the unreliability of SD cards, we recommend that images be captured to a directory on another medium, such as a network-mounted filesystem or a USB drive (or at least to a separate partition on the SD card if this is not an option). Constantly writing to the SD cards can, in our experience, lead to irrecoverable errors on the root filesystem which may require a reinstallation of the OS. 
