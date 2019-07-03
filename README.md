# SPIRO
SPIRO = Smart Plate Imaging RObot. It is a Raspberry Pi based imaging platform designed for time-lapse imaging of biological samples grown on Petri dishes: plant seedlings, fungal mycelium, bacterial colonies etc.

Currently, SPIRO supports imaging of up to four plates at the same time, using a "cube holder" for the Petri dishes. We designed it to be suitable for the two most poular Petri dish formats: round 9 cm plates and square 12 cm plates. Newer blueprints, designed for 3D printing, will be uploaded soon.

## hardware

SPIRO is based around Raspberry Pi 3B+, using 3D printed parts to hold everything together. The image below is a link to a YouTube video showing some of its design and features. 

[![SPIRO intro](https://user-images.githubusercontent.com/6480370/60589568-1e46ed80-9d9a-11e9-96ae-08fe85d8b415.png)](http://www.youtube.com/watch?v=fh5NMvDNjNc "SPIRO intro")

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
  -l, --duration        length or duration of the experiment [default: 7]
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

SPIRO is currently run on the Raspberry Pi 3 Model B+. It works with both the official camera module as well as with third-party cameras. We use the [Arducam Motorized Focus camera](http://www.arducam.com/programmable-motorized-focus-camera-raspberry-pi/).
