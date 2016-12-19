#!/usr/bin/env python
#
#
# tested with UniFi Controller 5.3.8
#
import os
import zlib
import urllib2
from binascii import a2b_hex
from struct import pack, unpack
from Crypto import Random
from Crypto.Cipher import AES

from unifi_config import hwaddr, ipaddr, model, version, inform_url, auth_key


def mac2a(mac):
  return ':'.join(map(lambda i: '%02x'%i, mac))

def ip2a(ip):
  return '.'.join(map(str, ip))


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


def post(url, key, json):
  headers = {
    'Content-Type': 'application/x-binary',
    'User-Agent': 'AirControl Agent v1.0'
  }
  data = packet_encode(key, json)
  req = urllib2.Request(url, data, headers)
  res = urllib2.urlopen(req)

  # parse response
  return packet_decode(key, res.read())


print post(inform_url, a2b_hex(auth_key), '''{
  "mac": "''' + mac2a(hwaddr) + '''",
  "ip": "''' + ip2a(ipaddr) + '''",
  "model": "''' + model + '''",
  "version": "''' + version + '''",
  #"cfgversion": "1234567890123456"
}''')

