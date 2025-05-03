# LG-ultrafine-brightness Controller
A tool to adjust LG Ultrafine Series Monitor without Bootcamp in Linux and Windows.

## Support List:
* 24MD4KL
* 27MD5KL
* 27MD5KA

## Python version
* required python version is 3.12 (tested on this version).

## Build
* `python3 -m venv lg_venv`
* `source ./lg_venv/bin/activate`
* `pip install -r requirements.txt`
## Usage:
(sudo is need due to libusb)

manuall set brightness: * `sudo ./bin/python3 main.py`


directly set brightness to 20 through cmd: * `sudo ./bin/python3 main.py 20`



