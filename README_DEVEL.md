# Developing the TOUGHswitch UniFi adaptation

When running the scripts from a development machine, TOUGHswitch commands are not
available, and static files in `samples/` are used to simulate.



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
$ make -C src
$ docker build -t unidev .
$ docker run --name unidev -t -i unidev
```

Now the simulated switch will start sending announcement packets, and it will
show up in the UniFi controller.


## 3. Adopt & Inform

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
