#!/usr/bin/python

import DnpSimple
import socket
import sys

# Connect to TCP server
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect(('localhost', 20000))

# Write to Analog Out
txdata = DnpSimple.DnpAsm.request_analog_out(
    src=0, dst=123, index=0, value=12345)
req = DnpSimple.DnpDisasm(txdata, request=True)
client.send(txdata)

rxdata = bytearray(client.recv(512))
res = DnpSimple.DnpDisasm(rxdata)

# Read back from Analog Out
txdata = DnpSimple.DnpAsm.request_analog_out_status(
    src=0, dst=123, index=0)
req = DnpSimple.DnpDisasm(txdata, request=True)
client.send(txdata)

rxdata = bytearray(client.recv(512))
res = DnpSimple.DnpDisasm(rxdata)

# Close TCP
client.close()
sys.exit(0)

# Local Variables:
# compile-command: "python DnpSimpleMaster.py"
# End:
