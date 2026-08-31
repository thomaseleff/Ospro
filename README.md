<html>
    <body>
        <p align="center">
            <img src="https://drive.google.com/uc?export=view&id=1mzPPmuXl7es8ZSfsqqIOqaCTgUjjgs_G">
        </p>
        <h1 align="center">Ospro</font></h1>
        <p align="center">Better than decent, open source espresso.</p>
    </body>
</html>

> [!IMPORTANT]
> The resources within this repository are under active development and are expected to change significantly over time without guarantee of backwards compatibility.

## Features
- Data logging of espresso extraction metrics (includes temperature and pressure)
- Temperature control via PID-algorithm
- Pressure profiling via PID-algorithm (in-progress)
- Self-hosted web-interface for browsing historical extractions and creating & sharing espresso extraction profiles (upcoming)

**Ospro** is available at an astounding low cost,
- The cheapest commercial-standard espresso machine with a configurable temperature PID, Rancilio Silvia PID Espresso Machine at **```$1,195 USD```**
- The cheapest with fully-integrated software, Decent DE1PRO at **```$3,699 USD```**
- The cheapest with manual pressure control, Rocket R Nine One Dual-Boiler Espresso Machine at **```$6,500 USD```**

The all-in **Ospro** cost-to-build, including the Gaggia Classic (Evo) Pro, competition-level accessories, hardware and software is less than **```$1,000 USD```**.

## Table of contents
- [Parts](./parts/README.md)
- [Guides](./guides/README.md)

# Installation
Instructions for setting-up the Raspberry Pi operating system and Ospro software application.

## Requirements
- Raspberry Pi OS Bookworm (Python 3.11) or Trixie (Python 3.13)
- Python >=3.11
- [uv](https://docs.astral.sh/uv/) for dependency management (dependencies are declared in [pyproject.toml](pyproject.toml))
- Internet connection

## Instructions
1. Flash a micro-SD card with the Raspberry PI OS version from 2019-07-12 using the official [Raspberry Pi Imager](https://www.raspberrypi.com/software/).
2. Once finished, insert the micro-SD card into the Raspberry Pi, then boot.
3. Once the boot process completes, update the software packages by running the following commands in the terminal,
```
sudo apt update
sudo apt full-upgrade
```
4. Open the Raspberry Pi config and enable SPI and I2C. Open the config by running the following command in the terminal,
```
sudo raspi-config
```
5. Reboot.
6. Once the reboot process completes, open the terminal. Navigate to the location of the USB flash drive storage.
```
cd /media/{user}/{usb-mass-storage-device-name}
```
7. Next, clone the main branch of the **Ospro** repository.
```
git clone --branch main https://github.com/thomaseleff/Ospro.git
```
8. Install [uv](https://docs.astral.sh/uv/) (if not already installed).
```
curl -LsSf https://astral.sh/uv/install.sh | sh
```
9. Navigate into the repository and install the Python requirements. On the Raspberry Pi, include the `rpi` extra for the hardware libraries.
```
cd Ospro
uv sync --extra rpi
```
> On non-Raspberry-Pi machines (e.g. for development), install without the extra: `uv sync`.
>
> When running from a USB flash drive, its filesystem (e.g. FAT32/exFAT) may not support the links `uv` needs for the virtual environment. Point the environment at the home directory (on the internal SD card) before syncing:
> ```
> export UV_PROJECT_ENVIRONMENT=/home/{user}/.venv
> ```
10. Run **Ospro**.
```
uv run python main.py
```