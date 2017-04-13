DnpSimple is a simple implementation of the DNP protocol.

It is free. It may be useful for

  - Studying and experimenting DNP
  - Writing test script

All in one Python file DnpSimple.py.

  - DnpSimple.DnpAsm is DNP assembler class
  - DnpSimple.DnpDisasm is DNP disassembler class

At this point, only analog out point is supported.

Take a look at DnpSimpleMaster.py and DnpSimpleSlave.py for example.

Shown below is a session example.

    $ python ~/lab/dnpsimple/DnpSimpleMaster.py
    > 05 64 14 C4 7B 00 00 00 57 26 C0 C0 05 29 01 28 01 00 00 00 39 30 00 00 00 B5 5A
        application (control=0xc0() function=DIRECT_OPERATE(5))
        object (group=41 variation=1 prefix=2 ranges=8(count=1))
          AO index 0: 12345 (flag=0x0)
    < 05 64 16 C4 7B 00 00 00 E0 00 C0 C0 81 00 00 29 01 28 01 00 00 00 39 30 00 00 82 A8 00 FF FF
        application (control=0xc0() function=RESPONSE(129))
        iin=0x0()
        object (group=41 variation=1 prefix=2 ranges=8(count=1))
          AO index 0: 12345 (flag=0x0)
    > 05 64 0F C4 7B 00 00 00 1A 57 C0 C0 01 28 00 28 01 00 00 00 01 C8
        application (control=0xc0() function=READ(1))
        object (group=40 variation=0 prefix=2 ranges=8(count=1))
          index 0
    < 05 64 16 C4 7B 00 00 00 E0 00 C0 C0 81 00 00 28 01 28 01 00 00 00 00 39 30 00 A2 D5 00 FF FF
        application (control=0xc0() function=RESPONSE(129))
        iin=0x0()
        object (group=40 variation=1 prefix=2 ranges=8(count=1))
          AO index 0: 12345 (flag=0x0)

    $ python ~/lab/dnpsimple/DnpSimpleSlave.py
    DNP slave waiting
    > 05 64 14 C4 7B 00 00 00 57 26 C0 C0 05 29 01 28 01 00 00 00 39 30 00 00 00 B5 5A
        application (control=0xc0() function=DIRECT_OPERATE(5))
        object (group=41 variation=1 prefix=2 ranges=8(count=1))
          AO index 0: 12345 (flag=0x0)
    AO[0] = 12345
    < 05 64 16 C4 7B 00 00 00 E0 00 C0 C0 81 00 00 29 01 28 01 00 00 00 39 30 00 00 82 A8 00 FF FF
        application (control=0xc0() function=RESPONSE(129))
        iin=0x0()
        object (group=41 variation=1 prefix=2 ranges=8(count=1))
          AO index 0: 12345 (flag=0x0)
    > 05 64 0F C4 7B 00 00 00 1A 57 C0 C0 01 28 00 28 01 00 00 00 01 C8
        application (control=0xc0() function=READ(1))
        object (group=40 variation=0 prefix=2 ranges=8(count=1))
          index 0
    < 05 64 16 C4 7B 00 00 00 E0 00 C0 C0 81 00 00 28 01 28 01 00 00 00 00 39 30 00 A2 D5 00 FF FF
        application (control=0xc0() function=RESPONSE(129))
        iin=0x0()
        object (group=40 variation=1 prefix=2 ranges=8(count=1))
          AO index 0: 12345 (flag=0x0)
