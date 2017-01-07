#!/usr/bin/env python
#
#
# UniFi (inform) packet decoder
#
import sys
import zlib
import snappy
from binascii import a2b_hex
from struct import pack, unpack
from Crypto.Cipher import AES


def packet_decode(key, data):
  magic = data[0:4]
  if magic != 'TNBU':
      raise Exception('Missing magic in response: "%s" instead of "TNBU"'%(magic))
  mac = unpack('BBBBBB', data[8:14])

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
  if flags & 0x04: payload = snappy.decompress(payload)

  return payload



print packet_decode(a2b_hex(sys.argv[1]), sys.stdin.read())
