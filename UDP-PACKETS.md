# UniFi UDP packets

For discovery, UniFi uses UDP packets on port 10001.

## UAP discovery

A [forum post](https://community.ubnt.com/t5/UniFi-Wireless/Turn-off-UPD-Broadcast/m-p/1321218#M115798)
shows the contents of such a broadcast packet. Let's see what's in there (skipping IPv4 header). It
consists of a version byte, packet type byte, two length bytes, and then any number of items.

    02                                          - Version 2
    06                                          - Announcement packet
    00 86                                       - Length of the data following

    02  00 0a  04 18 d6 96 0e 1a  c0 a8 25 41   - IP info: hardware address + ip address (192.168.37.65)
    01  00 06  04 18 d6 96 0e 1a                - Hardware address
    0a  00 04  00 07 d1 06                      - Uptime
    0b  00 05  31 73 74 41 50                   - Hostname ("1stAP")
    03  00 22  42 5a 2e 61 72 37 32 34 ...      - "BZ.ar724"... (truncated)

Another announcement packet from a UAP-AC-Lite access point:

    02                                          - Version 2
    06                                          - Announcement packet
    00 8e                                       - Length of the data following
    
    02  00 0a  80 22 a8 53 43 29  c0 a8 01 02   - IP info: hardware address + ip address (192.168.1.2)
    01  00 06  80 22 a8 53 43 29                - Hardware address
    0a  00 04  00 00 00 4d                      - Uptime (just turned on)
    0b  00 04  55 42 4e 54                      - Hostname ("UBNT")
    0c  00 04  55 37 4c 54                      - "U7LT"
    03  00 23  42 5a 2e 71 63 61 39 35 36 78 2e - Full firmware version ("BZ.qca956x.v3.4.14.3413.160119.2258")
               76 33 2e 34 2e 31 34 2e 33 34 31
               33 2e 31 36 30 31 31 39 2e 32 32
               35 38
    16  00 0b  33 2e 34 2e 31 34 2e 33 34 31 33 - Firmware version ("3.4.14.3413")
    15  00 04  55 37 4c 54                      - "U7LT"
    17  00 01  01                               - Default
    18  00 01  00                               - Not locating
    19  00 01  01                               - Dhcp client
    1a  00 01  01                               - Dhcp assigned
    13  00 06  80 22 a8 53 43 29                -
    12  00 04  00 00 00 05                      - Announcement sequence number
    1b  00 05  33 2e 34 2e 31                   - "3.4.1"



## UniFi Controller

Found in the UniFi controller, perhaps for testing:

    02
    06
    .. ..
    
    02  .. ..  00 15 6d 01 00 01  0a 02 02 01
    01  .. ..  00 15 6d 01 00 01
    0a  .. ..  00 00 36 00
    03  .. ..  "BZ.ar7240.v3.1.0.15.150311.1401"
    16  .. ..  "3.1.0"
    15  .. ..  "BZ2"
    23  .. ..  1


## Items

The first byte is the version, this can be 0, 1 or 2. We only look at version 2.

The second byte is the command. 06 (or 0a or ff) are used for announcement
(08, 02 and fe seem to be recognised for different purposes).

Then come the items: one byte type, two bytes length, payload.

 Type |  Format  | Description
 ---- | -------- | -------------
  01  | 06 bytes | mac address
  02  | 0a bytes | mac + ip of interfaces (*)
  03  | string   | full version identifier
  06  | string   | username
  07  | bytes    | salt
  08  | bytes    | challenge
  0a  | 04 bytes | uptime
  0b  | string   | hostname
  0c  | string   | platform
  0d  | string   | essid
  0e  | string   | wmode
  10  | string   | ?
  12  | integer  | ?
  13  | 06 bytes | id? (usually from mac?)
  15  | string   | model
  16  | string   | version
  17  | boolean  | default
  18  | boolean  | locating
  19  | boolean  | using_dhcpc
  1a  | boolean  | dhcpc_bound
  1b  | string   | required_version
  1c  | integer  | sshd_port
  1d  | string   | platform_version

(*) may appear multiple times

