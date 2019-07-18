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
* **Change the password**. The system will allow network access, and a weak password **will** compromise your network security **and** your experimental data.
* After changing the password, connect the network cable (if you are using wired networking).
* Under *Interfacing*, enable *Camera*, *I2C*, and *SSH*. 
* In the *Advanced Options*, set *Memory Split* to 256.
* Under *Localisation Options*, make sure to set the *Timezone*. Please note that a working network connection is required to maintain the correct date.
* If needed, configure *Network* and *Localization* options here as well. Set a *Hostname* under Network if you plan on running several SPIROs.
* Finally, select *Finish*, and choose to reboot the system when asked. 
* After reboot, the system shows a message on the screen showing its IP address ("My IP address is: *a.b.c.d*"). Make a note of this address as you will need it to access the system over the network. Make sure that your network allows access to ports 8080 on this IP address.

Next, make sure the system is up to date, and install the required tools (answer yes to any questions):

```
sudo apt update
sudo apt upgrade
sudo apt install python3-pip git i2c-tools
```

Then, install the SPIRO software and its dependencies:

```
pip3 install git+https://github.com/jonasoh/spiro#egg=spiro
```

Finally, instruct the system to automatically run the SPIRO control software on boot:

```
spiro --install
systemctl enable --user spiro
sudo loginctl enable-linger pi
systemctl --user start spiro
```

You may now place the system in the setting in which you will be using it for your experiments.

## Usage

### Working with SPIRO

To manage your images you need an SFTP client. For managing SPIRO (e.g., for updating the software and diagnosing problems), an SSH client is very useful. Depending on your operating system and how comfortable you are with a computer, there are several choices. A few of them are listed below.

**Windows**
* [MobaXterm](https://mobaxterm.mobatek.net/) is a popular SSH client that also supports file transfer. Recommended for beginners. 
* [FileZilla](https://filezilla-project.org/) is also a popular SFTP client, but has been known to bundle malware with its installer.
* [PuTTY](https://www.chiark.greenend.org.uk/~sgtatham/putty/latest.html) is a lightweight and popular SSH client.
* [WinSCP](https://winscp.net/eng/index.php) can be used to transfer files from SPIRO using the SFTP protocol.

**Mac**
* On Mac, an SSH client is built in to the system. Using the *Terminal*, connect to SPIRO using the command `ssh pi@1.2.3.4` (where `1.2.3.4` is the IP address of your system).
* [Transmit](https://panic.com/transmit/) is the best graphical SFTP client for Mac.
* [Cyberduck](https://cyberduck.io/) may be another alternative.
* [FileZilla](https://filezilla-project.org/) also has a Mac version.
* Images can be transferred using the builtin commands `scp` and `sftp`, although this requires some knowledge of the command line.

### Connecting to the web interface

SPIRO is controlled via its web interface. To access the system, point your web browser to the address *http://**a.b.c.d**/*, where *a.b.c.d* is the IP address you noted previously. At the first access, you are asked to set a password for the system. **Do not use the same password as you set previously!** This password is for the web interface and should be regarded as a low-privilege password.

### Setting up imaging

After logging in to the system, you are presented with the *Live view*. Here, you can adjust the image in real time, allowing you to make sure that the camera is at a proper distance from the plate, that the focus is set correctly, and that the LED illuminator is working and placed in a position where reflections are not an issue.

Under *Day image settings* and *Night image settings*, you can adjust the exposure time for day and night images in real time. For night images, make sure that representative conditions are used (i.e., turn off the lights in the growth chamber). When the image is captured according to your liking, choose *Update and save*.

For locating the initial imaging position, the system turns the cube until a positional switch is activated. It then turns the cube a predefined amount of steps (*calibration value*). The check that the calibration value is correct, go to the *Start position calibration* view. Here, you may try out the current value, as well as change it. Make sure to click *Save value* if you change it.

### Starting an experiment

When imaging parameters are set up to your liking, you are ready to start your experiments. In the *Experiment control* view, choose a name for your experiment, as well as the duration and imaging frequency. After you choose *Start experiment*, the system will disable most of the functionality of the web interface, displaying a simple status window containing experiment parameters, as well as the last image captured.

### Downloading images

The images should be downloaded using the SFTP client you installed previously. Log in to the system using its IP address, username *pi*, and the password you set during the initial set up steps. Images are contained within directories in the home folder. After downloading, you should remove them from the system to make sure that it doesn't run out of disk space.

## Maintaining the system

### Restarting the software

If for some reason the software ends up in an unusable state, you can restart it by issuing the following command:

```
systemctl --user restart spiro
```

It has happened that the camera has become unresponsive, due to bugs in the underlying library. In this case, rebooting the system is the only way of getting it back into a usable state:

```
sudo shutdown -r now
```

### Shutting down the system

If you want to power down the system, always perform a clean shutdown to ensure that no damage is caused to the filsesystem:

```
sudo shutdown -h now
```

After a few seconds, when only the red LED on the Raspberry Pi is lit, you may pull the power.

### Keeping software up to date

You should regularly update the underlying operating system to make sure that it has the latest security patches. To do so, log in using your SSH client (or connect a screen and keyboard), and issue the following commands, answering *Y* to any queries:

```
sudo apt update
sudo apt upgrade
```

To update the SPIRO control software, issue the commands:

```
pip3 install -U git+https://github.com/jonasoh/spiro#egg=spiro
```

After updating the SPIRO software, or if you for any other reason need to restart the software, use the following command:

```
systemctl --user restart spiro
```

### Troubleshooting

To view the last 50 entries in the SPIRO log, use the command `journalctl --user-init -n 50`. This may give an indication of whatever is causing problems.
