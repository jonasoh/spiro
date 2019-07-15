# SPIRO is a Smart Plate Imaging Robot
SPIRO is a Raspberry Pi based imaging platform designed for highly reproducible, high temporal resolution timelapse imaging of biological samples grown on Petri dishes: plant seedlings, fungal mycelium, bacterial colonies etc.

SPIRO supports imaging of up to four plates at the same time. It is designed it to be suitable for the two most poular Petri dish formats: round 9 cm plates and square 12 cm plates.

## Hardware

SPIRO is based around [Raspberry Pi 3 B+](https://www.raspberrypi.org/products/raspberry-pi-3-model-b-plus/), using 3D printed parts to hold everything together. It works with both the [official camera module](https://www.raspberrypi.org/products/camera-module-v2/) as well as with third-party cameras. We use the [Arducam Motorized Focus camera](http://www.arducam.com/programmable-motorized-focus-camera-raspberry-pi/), which allows focusing the images via the built-in live view web server.

The image below is a link to a YouTube video showing some of its design and features.

[![SPIRO intro](https://user-images.githubusercontent.com/6480370/60589568-1e46ed80-9d9a-11e9-96ae-08fe85d8b415.png)](http://www.youtube.com/watch?v=fh5NMvDNjNc "SPIRO intro")

The system basically consists of a camera, a green LED illuminator for imaging in the dark, and a motor-controlled imaging stage, as shown below. 

![SPIRO close-up](https://user-images.githubusercontent.com/6480370/60957134-6a4ae280-a304-11e9-8a03-0d854267297b.jpeg)

It is relatively cheap and easy to assemble multiple systems for running larger experiments.

![Multiple SPIROs](https://user-images.githubusercontent.com/6480370/60957494-0bd23400-a305-11e9-85d2-895cf8936120.jpeg)

## Examples

Below is a timelapse sequence of *Arabidopsis* seedlings growing on agar. The image has been heavily downscaled due to size constraints.

![Timelapse example](https://user-images.githubusercontent.com/6480370/60673063-350f4200-9e77-11e9-9fad-f9ec3140b05c.gif)

Below are examples of the image quality for day and night images. Click for full resolution.

![Day example picture](https://user-images.githubusercontent.com/6480370/60673390-e2825580-9e77-11e9-853c-9be434a332e5.jpg)

![Night example picture](https://user-images.githubusercontent.com/6480370/60673407-eca45400-9e77-11e9-8c57-25c65ecdbf42.jpg)

## 3D printer models

Models for the 3D printed hardware components can be found at [AlyonaMinina/SPIRO](https://github.com/AlyonaMinina/SPIRO).

## ImageJ macros

A few ImageJ macros that take advantage of the capabilities of SPIRO can be found at [jiaxuanleong/spiro-IJmacros](https://github.com/jiaxuanleong/spiro-IJmacros).

## Installation

First, prepare the SD card with a fresh release of Raspbian Lite (follow the official [instructions](https://www.raspberrypi.org/documentation/installation/installing-images/README.md)). 

Connect the Raspberry Pi to a screen and keyboard. Log in using the default credentials (username `pi`, password `raspberry`). Start the system configuration:
```
sudo raspi-config
```

In the raspi-config interface, make the following changes:
* Change the password
* Under *Interfacing*, enable *Camera*, *I2C*, and *SSH*. 
* In the *Advanced Options*, set *Memory Split* to 256.
* Under *Localisation Options*, make sure to set the *Timezone*. Please note that a working network connection is required to maintain the correct date.
* If needed, configure *Network* and *Localization* options here as well. Set a *Hostname* under Network if you plan on running several SPIROs.
* Finally, select *Finish*, and choose to reboot the system when asked. 

Next, make sure the system is up to date, and install the required tools (answer yes to any questions):

```
sudo apt update
sudo apt upgrade
sudo apt install python3-pip git i2c-tools
```

Finally, install the SPIRO software and its dependencies:

```
sudo pip3 install git+https://github.com/jonasoh/spiro#egg=spiro
```

You may now run the spiro software using the command
```
spiro
```

## Usage

### Working with SPIRO

To manage your images (and possibly diagnose problems), you need an SSH/SFTP client. Depending on your operating system and how comfortable you are with a computer, there are several choices. A few of them are listed below.

**Windows**
* [MobaXterm](https://mobaxterm.mobatek.net/) is a popular SSH client that also supports file transfer. Recommended for beginners. 
* [FileZilla](https://filezilla-project.org/) is also a popular SFTP client, but has been known to bundle malware with its installer.
* [PuTTY](https://www.chiark.greenend.org.uk/~sgtatham/putty/latest.html) is a lightweight and popular SSH client.
* [WinSCP](https://winscp.net/eng/index.php) can be used to transfer files from SPIRO using the SFTP protocol.

**Mac**
* On Mac, an SSH client is built in to the system. Using the *Terminal*, connect to SPIRO using the command `ssh pi@1.2.3.4` (where `1.2.3.4` is the IP address of your system). Images can be transferred using the builtin commands `scp` and `sftp`, although this requires some knowledge about using the command line.
* [Transmit](https://panic.com/transmit/) is the best graphical SFTP client for Mac.
* [Cyberduck](https://cyberduck.io/) may be another alternative.
* [FileZilla](https://filezilla-project.org/) also has a Mac version.
