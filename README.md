# cubini
A python library to control several Thorlabs' KPZ101 piezo controler cubes. Each KPZ101 is interfaced using the virtual com port [implementation](https://github.com/pyusb/pyusb/blob/master/tools/vcp_terminal.py) of `pyusb`.

## Installation
To install the package from source simply do
```
sudo apt install libusb
sudo apt install python-usb

python2.7 setup.py install
```

*Requirements*: This library works on top of `pyusb` which uses `libusb` so these should both be installed as well.

## Use without sudo
If you want to use the library without root rights run the following steps first.
 1. Add the user to the plugdev group
 `sudo useradd -G plugdev USERNAME`
 2. Add the evaluation board to the plugdev group by edditing a new rules file
 `sudo vim /etc/udev/rules.d/10-kpz101.rules`
  and adding the following line
  `ATTRS{idProduct}=="faf0", ATTRS{idVendor}=="0403", MODE="666", GROUP="plugdev"`
 3. Reload the udev rules
 `sudo udevadm trigger`
