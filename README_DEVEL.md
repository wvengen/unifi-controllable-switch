# Developing the TOUGHswitch UniFi adaptation

When running the scripts from a development machine, TOUGHswitch commands are not
available, and static files in `samples/` are used to simulate.


## Building from scratch

All source code can be found in [src/](src/). The TOUGHswitch is a MIPS platform
(running Linux 2.6 with [uClibc](https://uclibc.org/)), so cross-compilation is needed.
A reliable way is running an old [Debian mips image](https://people.debian.org/~aurel32/qemu/mips/)
with qemu. This is fully integrated with the [Makefile](src/Makefile). Some dependencies
are needed, though:

```
sudo apt-get install make gcc libc6-dev zlib1g-dev wget squashfs-tools \
                     qemu-system-mips qemu-utils netcat openssh-client
```

By default, `make` will build a binary for the build system (for development). To
cross-compile, `make mips/unifi-inform-data` will download the cross-compilation
environment (once), run qemu, setup a build system in there, compile the source,
and copy out the resulting binary. `make dist.mips.tar.gz` bundles all files needed
to run on the device.

For a new release `make dist.build.tar.gz` will create an archive with just the
tools to modify existing firmware.


## Local development environment

For development, it may be useful to test without real hardware. This can be done
using [Docker](http://docker.com). No cross-compilation is needed here.


### 1. Start a local UniFi controller

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


### 2. Start a local simulated switch

To test adding a switch, you can build and run the docker image provided here:

```sh
$ make -C src
$ docker build -t unidev .
$ docker run --name unidev -t -i unidev
```

Now the simulated switch will start sending announcement packets, and it will
show up in the UniFi controller.


### 3. Adopt & Inform

Now that the device is visible in the controller, press _Adopt_. The simulated switch
should pick up the adoption, and report back in 30 seconds, after which its state will
move to _Provisioning_. After another 30 seconds at max, it will become _Connected_.


## Python scripts

To work out the protocol, Python scripts may be easier. These can be found in `devel/`.
Configure the mac and IP address in [devel/unifi_config.py](devel/unifi_config.py) for
announcement using `python2` [`devel/unifi_announce.py`](devel/unifi_announce.py).

For the inform request, also configure `inform_url` and `auth_key`, then run
`python2` [`devel/unifi_inform.py`](devel/unifi_inform.py).



## UniFi controller log level

Edit its `data/system.properties` and add the lines

```properties
debug.device=DEBUG
debug.mgmt=DEBUG
debug.sdn=DEBUG
debug.system=DEBUG
```

then look at `log/server.log`. Hint: `docker exec -i -t unifi bash`

Most of these can also be set in the controller settings.
