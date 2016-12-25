#
# UniFi controllable switch - Dockerfile
#
# Provides a virtual UniFi switch.
#
FROM debian

# we need ssh and some other packages
# note that (older versions) of the UniFi controller only support insecure diffie-hellmap-group1-sha1
RUN apt-get -y update && apt-get install --no-install-recommends -y openssh-server net-tools wget netcat vim-tiny && \
    mkdir /var/run/sshd && \
    sed -i 's/^PermitRootLogin .*/PermitRootLogin yes/' /etc/ssh/sshd_config && \
    echo 'KexAlgorithms diffie-hellman-group1-sha1,diffie-hellman-group-exchange-sha256' >>/etc/ssh/sshd_config

# use UniFi convention for default account
RUN sed -i 's/^root:/ubnt:/' /etc/passwd /etc/shadow && \
    echo 'ubnt:ubnt' | chpasswd && \
    mkdir -p /var/etc && ln -sf $HOME /var/etc/persistent

# UniFi integration
COPY src/syswrapper.sh \
     src/unifi-announce-data \
     src/unifi-daemon \
     src/unifi-inform-data \
     src/unifi-inform-process \
     src/unifi-inform-send \
     src/unifi-inform-status \
     src/zimulate-mca-status \
       /root/
COPY src/shinc/JSON.sh \
     src/shinc/common.sh \
       /root/shinc/

RUN printf '#!/bin/sh\n/root/syswrapper.sh $@\n' >/usr/bin/syswrapper.sh && \
    chmod a+x /usr/bin/syswrapper.sh

# Some TOUGHswitch-specific files are needed to get the status
COPY samples/mca-config /tmp/system.cfg
RUN printf '#!/bin/sh\n/root/zimulate-mca-status $@\n' >/usr/bin/mca-status && \
    chmod a+x /usr/bin/mca-status

## for development, if you want to know what's being sent
#RUN printf '#!/bin/sh\necho "[`date +%%Y%%m%%d\\ %%H:%%M:%%S`] $0 $@\\n" >>/tmp/unifi.log\n' >/usr/bin/syswrapper.sh
#RUN chmod a+x /usr/bin/syswrapper.sh
#RUN touch /tmp/unifi.log
#CMD service ssh start && tail -f /tmp/unifi.log

EXPOSE 22
CMD service ssh start && /root/unifi-daemon
