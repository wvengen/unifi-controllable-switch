#!/usr/bin/env python
#
#
# tested with UniFi Controller 5.3.8
#
import os
import json
import zlib
import urllib2
from binascii import a2b_hex
from struct import pack, unpack
from Crypto import Random
from Crypto.Cipher import AES

from unifi_config import hwaddr, ipaddr, inform_url, auth_key, cfgdir, model, version


def mac2a(mac):
  return ':'.join(map(lambda i: '%02x'%i, mac))

def mac2serial(mac):
  return ''.join(map(lambda i: '%02x'%i, mac))

def ip2a(ip):
  return '.'.join(map(str, ip))


def cfg(fn, key):
  '''read key from configuration file'''
  fp = os.path.join(cfgdir, fn)
  try:
    with open(fp) as f:
      for line in f:
        if line.startswith(key + '='):
          return line.split('=', 1)[1].rstrip()
  except IOError:
    pass

def cfg_replace(fn, contents):
  '''replace configuration file'''
  fp = os.path.join(cfgdir, fn)
  try:
    os.mkdir(cfgdir)
  except OSError:
    pass
  with open(fp, 'w') as f:
    f.write(contents)


def packet_encode(key, json):
  iv = Random.new().read(16)

  # zlib compression
  payload = zlib.compress(json)
  # padding - http://stackoverflow.com/a/14205319
  pad_len = AES.block_size - (len(payload) % AES.block_size)
  payload += chr(pad_len) * pad_len
  # encryption
  payload = AES.new(key, AES.MODE_CBC, iv).encrypt(payload)

  # encode packet
  data = 'TNBU'                     # magic
  data += pack('>I', 0)             # packet version
  data += pack('BBBBBB', *hwaddr)   # mac address
  data += pack('>H', 3)             # flags
  data += iv                        # encryption iv
  data += pack('>I', 1)             # payload version
  data += pack('>I', len(payload))  # payload length
  data += payload

  return data


def packet_decode(key, data):
  magic = data[0:4]
  if magic != 'TNBU':
      raise Exception('Missing magic in response: "%s" instead of "TNBU"'%(magic))
  mac = unpack('BBBBBB', data[8:14])
  if mac != hwaddr:
      raise Exception('Mac address changed in response: %s -> %s'%(mac2a(hwaddr), mac2a(mac)))

  flags = unpack('>H', data[14:16])[0]
  iv = data[16:32]
  payload_len = unpack('>I', data[36:40])[0]
  payload = data[40:(40+payload_len)]

  # decrypt if required
  if flags & 0x01:
      payload = AES.new(key, AES.MODE_CBC, iv).decrypt(payload)
      # unpad - https://gist.github.com/marcoslin/8026990#file-server-py-L43
      pad_size = ord(payload[-1])
      if pad_size > AES.block_size:
          raise Exception('Response not padded or padding is corrupt')
      payload = payload[:(len(payload) - pad_size)]
  # uncompress if required
  if flags & 0x02: payload = zlib.decompress(payload)

  return payload


def inform(url, key, json):
  headers = {
    'Content-Type': 'application/x-binary',
    'User-Agent': 'AirControl Agent v1.0'
  }
  data = packet_encode(key, json)
  req = urllib2.Request(url, data, headers)
  res = urllib2.urlopen(req)

  # parse response
  return packet_decode(key, res.read())


r = inform(inform_url, a2b_hex(auth_key), json.dumps({
  'mac': mac2a(hwaddr),
  'ip': ip2a(ipaddr),
  'model': model,
  'version': version,
  'serial': mac2serial(hwaddr),
  'uptime': 1,
  'cfgversion': cfg('_cfg', 'cfgversion'),
  'if_table': [{
    'mac': mac2a(hwaddr),
    'ip': ip2a(ipaddr),
    'name': 'eth0',
    'speed': 1000,
    'full_duplex': True
  }],
  'port_table': [{
    'port_idx': 1,
    'port_poe': True,
    'media': 'GE',          # GE SFP SFP+
    'name': 'port one',
    'enable': True,
    'autoneg': True,
    'poe_enable': True,
    'poe_mode': 'pasv24',

    'up': True,
    'speed': 1000,
    'full_duplex': True,
    'tx_packets': 22345,
    'tx_bytes': 28394,
    'tx_errors': 5,
    'rx_packets': 192,
    'rx_bytes': 1882,
    'rx_errors': 10,
    'stp_state': 'forwarding',
    'stp_pathcost': 20000,

    'mac_table': [
        {'mac': '01:02:03:04:05:06', 'age': 30, 'uptime': 1002, 'type': 'usw'}
      # optional type: usw uap
    ]

    #'is_uplink': False,
    #'switch_vlan_enabled': False,
    #'jumbo': True,
    #'flowctrl_rx': False,
    #'flowctrl_tx': False,
  }, {
    'port_idx': 2,
    'port_poe': True,
    'media': 'GE',
    'name': 'port two',
    'enable': True,
    'up': True,
    'speed': 10,
    'full_duplex': False,
    'tx_packets': 10,
    'tx_bytes': 203,
    'tx_errors': 0,
    'rx_packets': 2,
    'rx_bytes': 12,
    'rx_errors': 1,
    'stp_state': 'blocking'
  }]
}))
r = json.loads(r)

if r['_type'] == 'setparam':
  # save configuration
  othercfg = ''
  for key, val in r.items():
    if key.endswith('_cfg'):
      cfg_replace(key[0:(len(key)-4)], val)
    elif key != '_type' and key != 'server_time_in_utc':
      othercfg += key + '=' + val + '\n'
  cfg_replace('_cfg', othercfg)

print json.dumps(r, indent=2)
