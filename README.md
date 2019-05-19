# SPIRO
SPIRO = Smart Plate Imaging RObot. It is a Raspberry Pi -based imaging platform designed for time-lapse imaging of biological samples grown on Petri dishes: plant seedlings, fungal mycelium, bacterial colonies etc.

Currently, SPIRO supports imaging of up to four plates at the same time, using a "cube holder" for the Petri dishes. We designed it to be suitable for two most poular Petri dishes formats: round9 cm plates and square 12 cm plates. Newer blueprints, designed for 3D printing, will be uploaded soon. 

## hardware

This is the previous prototype of SPIRO placed inside a plant growth chamber. This iteration uses 3D printed parts for housing the cameras and other electronics, as well as for the dish-holding cube. 

<img src="https://raw.githubusercontent.com/jonasoh/web/master/petripi-3dprinted.jpg">

## example

<img src="https://github.com/jonasoh/web/raw/master/day-cropped-optim.gif">
(Note: the image quality has improved by a large degree since this image was captured.)

## usage

```
usage: spiro   [-h] [-l] [-d D] [--dir] [--day-shutter DS] [--night-shutter NS]
               [--day-iso DAYISO] [--night-iso NIGHTISO] [--resolution RES]
               [--dir DIR] [--prefix PREFIX] [--auto-wb] [-t]

By default, SPIRO will run an experiment for 7 days with hourly captures,
saving images to the current directory.

optional arguments:
  -h, --help            show this help message and exit
  -l, --duration        length or duration of the experiment [default: 7 ]
  -d D, --delay D       time, in minutes, to wait between shots [default: 60]
  --disable-motor       disable use of motor [default: false]
  --day-shutter DS      daytime shutter in fractions of a second, i.e. for
                        1/100 specify '100' [default: 100]
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

SPIRO is currently run on the Raspberry Pi Compute Module 3. It works with both the official camera module as well as with third-party cameras. We use the official V2 camera and Arducam.

To install, first enable dual amera interfacing using the [official instructions]

**Note:** Due to the unreliability of SD cards, we recommend that images be captured to a directory on another medium, such as a network-mounted filesystem or a USB drive (or at least to a separate partition on the SD card if this is not an option). Constantly writing to the SD cards can, in our experience, lead to irrecoverable errors on the root filesystem which may require a reinstallation of the OS. 
