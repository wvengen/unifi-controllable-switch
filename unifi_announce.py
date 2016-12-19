#!/usr/bin/env python
#
# Announce a UniFi device on the network.
#
#
# Tested with UniFi Controller 4.8.12 and 5.3.8.
#
import socket

from unifi_config import bcast, hwaddr, ipaddr, model, version


def make_packet(packet_type, data):
  r = chr(packet_type) + chr(len(data)>>8) + chr(len(data)&0xff)
  if isinstance(data, str):
    r += data
  else:
    r += ''.join(map(chr, data))
  return r


def unifi_bcast(packets):
  bcast_addr = '.'.join(map(str, bcast))
  pkt_data = ''.join(map(lambda p: make_packet(p[0], p[1]), packets))
  udp_data = '\x02\x06' + chr(len(pkt_data)>>8) + chr(len(pkt_data)&0xff) + pkt_data

  sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
  sock.bind((bcast_addr, 0))
  sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, -1)
  ret = sock.sendto(udp_data, (bcast_addr, 10001))


def announce(hwaddr, ipaddr, model, extra=[]):
    '''Broadcast announcement packet (with minimum fields required)'''
    unifi_bcast([
      [0x02, list(hwaddr) + list(ipaddr)],
      [0x01, hwaddr],
      [0x0a, [0, 0, 0, 1]],
      [0x16, version],
      [0x15, model],
      [0x13, hwaddr],
      [0x12, [0, 0, 0, 1]]
    ] + extra)


def announce_ugw(hwaddr, ipaddr, model, extra=[]):
    '''UGW announcement'''
    announce(hwaddr, ipaddr, model, [
      [0x02, list(hwaddr) + list(ipaddr)], # 2nd is used for IP adress
    ] + extra)


def announce_ap_full(hwaddr, ipaddr, model):
    '''UAP full announcement packet'''
    unifi_bcast([
      [0x02, hwaddr + ipaddr], # IP info
      [0x01, hwaddr],          # Hardware address
      [0x0a, [0, 0, 0, 5]],    # Uptime
      [0x0b, 'UBNT'],          # Radio name
      [0x0c, model],           # Model
      [0x03, 'BZ.qca956x.v' + version + '.123456.1234'],
      [0x16, version],         # Firmware version
      [0x15, model],           # Model
      [0x17, [1]],             # Default: yes
      [0x18, [0]],             # Locating: no
      [0x19, [1]],             # DHCP client: yes
      [0x1a, [1]],             # DHCP active: yes
      [0x13, hwaddr],          #
      [0x12, [0, 0, 0, 1]],    # Announcement sequence number
      [0x1b, '3.4.1']          # Platform version
    ])

#announce_ap_full(hwaddr, ipaddr, 'U7P')
#announce_ugw(hwaddr, ipaddr, 'UGW4')
announce(hwaddr, ipaddr, model)

# model identifiers:
#   BZ2LR
#   U2S48 U2L48 U2HSR U2Sv2 U2Lv2 U2IW
#   U7HD U7PG2 U7EDU U7MP U7LT U7MSH U7IW U7LR
#   SW24P US24 US24P250 US24P500
#   US48 US48P500 US48P750
#   US8 US8P150 US16P150 US8P60
#   UGW3 UGW4 UGW8

# http://www.gossamer-threads.com/lists/python/python/578593
# https://wiki.python.org/moin/UdpCommunication
# https://pymotw.com/2/socket/udp.html
# https://www.sk89q.com/2008/10/spoofing-a-udp-packet-in-python/
