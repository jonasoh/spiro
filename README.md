# plantlapse
Raspberry Pi timelapse imaging of seed growth. For now, this is mainly for internal use and the script contains constants which need to be modified for proper function (e.g. exposure speed cutoffs for day/night determination). 

```
Usage: plantlapse.py [options]

Options:
  --version             show program's version number and exit
  -h, --help            show this help message and exit
  -n NSHOTS, --num-shots=NSHOTS
                        number of shots to capture [default: 168]
  -d DELAY, --delay=DELAY
                        time, in minutes, to wait between shots [default: 60]
  --day-shutter=DAYSHUTTER
                        daytime shutter in fractions of a second, i.e. for
                        1/100 specify '100' [default: 50]
  --night-shutter=NIGHTSHUTTER
                        nighttime shutter in fractions of a second [default:
                        200]
  --day-iso=DAYISO      set daytime ISO value (0=auto) [default: 100]
  --night-iso=NIGHTISO  set nighttime ISO value (0=auto) [default: 100]
  --resolution=RESOLUTION
                        set camera resolution [default: 2592x1944]
  --prefix=PREFIX       prefix to use for filenames [default: none]
  --auto-wb             adjust white balance between shots (if false, only
                        adjust when day/night shift is detected) [default:
                        false]
  --led                 do not disable camera led; useful for running without
                        GPIO privileges
  --preview             show a live preview of the current settings for 60
                        seconds, then exit
  -t, --test            capture a test picture as 'test.jpg', then exit
```
