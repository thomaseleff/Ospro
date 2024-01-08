# Ospro
Better than decent, open-source espresso machine software, offering data logging, temperature control and pressure profiling via a Raspberry Pi & Python.

> [!IMPORTANT]
> The software, breadboard prototype and build-guides within this repository are under-development and are expected to change significantly over time without guarantee of backwards compatibility.

## Table of contents
- [Parts](./parts/README.md)
- [Guides](./guides/README.md)

# Installation
Instructions for setting-up the Raspberry Pi operating system and Ospro software application.

## Requirements
- Raspberry Pi OS v2019-07-12 (~[/raspbian/images/raspbian-2019-07-12](http://downloads.raspberrypi.org/raspbian/images/raspbian-2019-07-12/) a.k.a. "buster")
- Python v3.7.3 (included in the Raspberry Pi OS)
- Python libraries specified within [requirements_RPi.txt](requirements_RPi.txt)
- Internet connection

## Instructions
1. Flash a micro-SD card with the Raspberry PI OS version from 2019-07-12 using the official [Raspberry Pi Imager](https://www.raspberrypi.com/software/).
2. Once finished, insert the micro-SD card into the Raspberry Pi, then boot.
3. Once the boot process completes, open the Raspberry Pi config and enable SPI and I2C. Open the config by running the following command in the terminal,
```
sudo raspi-config
```
4. Reboot.
5. Once the re-boot process completes, open the terminal. Navigate to the location of the USB flash drive storage.
```
cd /media/{user}/{usb-mass-storage-device-name}
```
6. Next, clone the main branch of the Ospro repository.
```
git clone --branch main https://github.com/thomaseleff/Ospro.git
```
7. Navigate back to the root directory.
```
cd ~
```
8. Create a Python virtual environment to install the Python requirements.
```
python3 -m venv .ospro
```
6. Activate the environment.
```
source .ospro/bin/activate
```
7. Install the Python requirements.
```
python3 -m pip install -r /media/{user}/{usb-mass-storage-device-name}/Ospro/requirements_RPi.txt
```
8. Run Ospro.
```
python3 /media/{user}/{usb-mass-storage-device-name}/Ospro/main.py
```