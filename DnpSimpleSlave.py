#!/usr/bin/python

import DnpSimple
import socket
import sys

# Wait for TCP client
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(('', 20000))
server.listen(5)

# Initialize DNP points
ao = {}

# Infinite loop for each client connection
try:
    while True:
        # Wait for DNP master
        print 'DNP slave waiting'
        client, address = server.accept()
    
        # Infinite loop for each request
        while True:
            # Receive request
            rxdata = bytearray(client.recv(512))
            if not rxdata:
                break;
            req = DnpSimple.DnpDisasm(rxdata, request=True)

            # Process request
            fg = (req.application_function, req.objects[0].group)
            if fg == (5, 41):
                # AO output
                do = req.objects[0].objects[0]
                print 'AO[{}] = {}'.format(do.index, do.value)
                ao[do.index] = do.value
                txdata = DnpSimple.DnpAsm.response_analog_out(
                    src=0, dst=123, index=0, value=do.value)
            elif fg == (1, 40):
                # AO status
                value = ao.get(do.index, 0)
                txdata = DnpSimple.DnpAsm.response_analog_out_status(
                    src=0, dst=123, index=0, value=value)
            else:
                raise Error('UNIMPLEMENTED')

            res = DnpSimple.DnpDisasm(txdata)
            client.send(txdata)

    print 'Client disconnected'
    client.close()

except KeyboardInterrupt:
    print
    client.close()
    sys.exit(0)
except:
    client.close()
    raise

# Local Variables:
# compile-command: "python DnpSimpleSlave.py"
# End:
