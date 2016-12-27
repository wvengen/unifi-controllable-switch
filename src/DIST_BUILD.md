# TOUGHswitch firmware with support for a UniFi controller

_TOUGHswitch version: @@FW_VERSION@@_
_UniFi adaptation version: @@FW_UNIVERS@@_

This package allows you to add support for a UniFi controller to existing
TOUGHswitch firmware. Instructions are for Debian or Ubuntu Linux.


### 1. Install dependencies

```
sudo apt-get install make gcc libc6-dev zlib1g-dev wget squashfs-tools
```


### 2. Build firmware

```
make firmware
```

This will download the TOUGHswitch firmware from its official location.
Then it will be unpacked, modified, and repacked. The resulting firmware
file will be named `SW.v<version>.<build_number>.unifi<version>.bin`.


### 3. Install firmware

You can use the web-interface to upload the `.bin` file and press _Update_.
After a couple of minutes, the switch will announce itself to the controller.

