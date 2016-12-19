#
# Common configuration for UniFi device tools
#
# You'll probably need to change the addresses for your situation.
#

# broadcast address to reach controller
bcast  = (172,  17, 255, 255)
# inform url (communicated by controller on adoption)
inform_url = 'http://172.17.0.3:8080/inform'
# auth key (communicated by controller on adoption)
auth_key = 'abc...'

# device's mac and IP addres
hwaddr = (0x02, 0x42, 0xac, 0x11, 0x00, 0x04)
ipaddr = (172,  17, 0, 4)
ipmask = (255, 255, 0, 0)


# device's model identifier
model = 'US8P150'
# device's firmware version
version = '3.4.5.6789'

