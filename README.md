# Integrating a TOUGHswitch with a UniFi controller

The UniFi controller provides integration for Ubiquiti's UniFi hardware. An important element
that is often used with basic UniFi-based WiFi networks, is the TOUGHswitch, which provides
switching and power-over-ethernet capability for the access points. This family of switches,
however, does not integrate with the UniFi controller
(and [it appears Ubiquiti won't do so](https://community.ubnt.com/t5/UniFi-Routing-Switching/Tough-Switch-integration-with-Unifi-4-6/td-p/1191186)).
This project is an attempt to add this capability (for layer 2).

![UniFi controller with a dummy switch](screenshot-unifi-controller.png)


## 1. Start a local UniFi controller

For testing, it's useful to have a UniFi controller running testing. This is done
most easily using the [docker image](https://hub.docker.com/r/jacobalberty/unifi/):


```sh
$ docker pull jacobalberti/unifi
$ docker run -d --name unifi jacobalberti/unifi
$ docker inspect unifi | grep IPAddress | tail -n 1
# "IPAddress": "172.17.0.3"
```

Then visit the IP-address at port 8443 with a browser using HTTPS, in this case
that would be: https://172.17.0.3:8443/
Follow the installation wizard to get to the dashboard.


## 2. Start a local simulated switch

To test adding a switch, you can build and run the docker image provided here:

```sh
$ docker build -t unidev .
$ docker run --name unidev -t -i unidev
```

Now the simulated switch is waiting for adoption. But the controller doesn't know
about it yet (auto-announcment is being worked on).


## 3. Announce

For the moment, you can do it manually. To send the announcement packet,
[Python](http://www.python.org) is required.

First edit the file `devel/unifi_config.py` and modify the mac and IP address
_of the simulated switch_.

```sh
$ docker inspect unidev | grep '"IPAddress"\|"MacAddress"' | tail -n 2
# "IPAddress": "172.17.0.4",
# "MacAddress": "02:42:ac:11:00:04"
```

Then run [devel/unifi_announce.py](devel/unifi_announce.py):

```sh
$ python2 devel/unifi_announce.py
```

When all goes well, you'll see a new device in the controller, pending adoption.
If this didn't work, you may want to review `bcast` in [unifi_config.py](unifi_config.py).
Make sure that your UniFi controller is covered by this broadcast address.


## 3. Adopt & Inform

Now that the device is visible in the controller, press _Adopt_. The simulated switch
should pick up the adoption, and report back in 30 seconds, after which its state will
move to _Provisioning_. After another 30 seconds at max, it will become _Connected_.


## Integrating with real hardware

_Pending._

- [x] Figure out how to gather information on a TOUGHswitch
  * network config
  * discovered mac addresses + age
  * port for each mac address (maybe not available - what then?)
  * power over ethernet config + status
  * (`mca-status` and `mca-config` may be helpful here)
- [x] Rewrite in C (or something else to generate a small native binary)
- [x] Cross-compile for mips (Atheron AR7240)
- [ ] Let the switch announce itself
- [ ] Figure out how to modify the switch permanently
- [ ] Install-script
- [ ] Add mac address table to status output


## UniFi controller log level

Edit its `data/system.properties` and add the lines

```properties
debug.device=DEBUG
debug.mgmt=DEBUG
debug.sdn=DEBUG
debug.system=DEBUG
```

then look at `log/server.log`. Hint: `docker exec -i -t unifi bash`


## Links

* UniFi protocol
 - [Help: What protocol does the controller use to communicate with the UAP?](https://help.ubnt.com/hc/en-us/articles/204976094-UniFi-What-protocol-does-the-controller-use-to-communicate-with-the-UAP-)
 - [jk-5/unifi-inform-protocol](https://github.com/jk-5/unifi-inform-protocol)
 - [fxkr/unifi-protocol-reverse-engineering](https://github.com/fxkr/unifi-protocol-reverse-engineering)
 - [nutefood/python-ubnt-discovery](https://github.com/nitefood/python-ubnt-discovery)
 - [job/ubbnut](https://github.com/jof/ubbnut)
 - [Ubiquiti inform protocol](https://github.com/mcrute/ubntmfi/blob/master/inform_protocol.md)
 - [model identifiers](https://community.ubnt.com/ubnt/attachments/ubnt/UniFi/194506/1/bundles.json.txt)
* UniFi controller docker image at [jacobalberti/unifi](https://hub.docker.com/r/jacobalberty/unifi/)
* [finish06/unifi-api](https://github.com/finish06/unifi-api) - utitilies to manage a UniFi controller
* [sol1/icinga-ubiquiti-mfi](https://github.com/sol1/icinga-ubiquiti-mfi) - parser for mFi `mca-dump`'s json output
* [mcrute/ubntmfi](https://github.com/mcrute/ubntmfi) - web controller for mFi hardware
* OpenWRT on [UniFi AP AC](https://wiki.openwrt.org/toh/ubiquiti/unifiac)

