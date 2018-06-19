# plantlapse
Raspberry Pi timelapse imaging of seed growth. For now, this is mainly for internal use and the script contains constants which need to be modified for proper function (e.g. exposure speed cutoffs for day/night determination). 

## example

<img src="examples/day-cropped-optim.gif">

## usage

```
usage: plantlapse [-h] [-n N] [-d D] [--day-shutter DS] [--night-shutter NS]
                  [--day-iso DAYISO] [--night-iso NIGHTISO] [--resolution RES]
                  [--dir DIR] [--prefix PREFIX] [--auto-wb] [--led]
                  [--preview [P]] [-t]

By default, plantlapse will run an experiment for 7 days with hourly captures,
saving images to the current directory.

optional arguments:
  -h, --help            show this help message and exit
  -n N, --num-shots N   number of shots to capture [default: 168]
  -d D, --delay D       time, in minutes, to wait between shots [default: 60]
  --day-shutter DS      daytime shutter in fractions of a second, i.e. for
                        1/100 specify '100' [default: 50]
  --night-shutter NS    nighttime shutter in fractions of a second [default:
                        200]
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
