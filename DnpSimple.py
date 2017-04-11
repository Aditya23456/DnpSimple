#!/usr/bin/python

# Simple implementation of DNP
#     - DnpAsm: DNP packet assembler
#     - DnpDisasm: DNP packet disassembler

# This implementation is a tiny subset of DNP.

import crccheck
import socket
import sys
import time

def dump_bytes(data):
    return ' '.join('{:02X}'.format(c) for c in data)

class DnpAsm(object):
    '''Assemble DNP packet'''
    def __init__(self):
        self.data = bytearray()

    def makePrologue(self, src, dst, function):
        self.link_header(src, dst)
        self.transport_header(1, 1, 0)
        self.application_header(1, 1, 0, 0, 0, function)

    def makeEpilogue(self):
        # Calculate link_len
        self.data[2] = len(self.data) - 3  # exclude link_start, link_length

        # Calculate link header CRC
        crc = crccheck.crc.Crc16Dnp()
        crc.process(self.data[0:8])
        value = crc.final()
        self.data.insert(8, value >> 8)
        self.data.insert(8, value & 0xff)

        # Calculate payload CRC
        p = 10
        while len(self.data) - p > 0:
            length = len(self.data) - p
            if length > 16:
                length = 16
            
            crc = crccheck.crc.Crc16Dnp()
            crc.process(self.data[p:p+length])
            value = crc.final()
            p += length
            self.data.insert(p, value >> 8)
            self.data.insert(p, value & 0xff)
            p += 2

    def link_start(self):
        self.data +=bytearray.fromhex('05 64')

    def link_control(self, dir, prm, fcb, fcv, function_code):
        ctrl = function_code
        ctrl |= dir << 7
        ctrl |= prm << 6
        ctrl |= fcb << 5
        ctrl |= fcv << 4
        self.data += bytearray((ctrl,))

    def link_destination(self, addr):
        l = addr & 0xff
        h = addr >> 8
        self.data += bytearray((l, h))

    def link_source(self, addr):
        l = addr & 0xff
        h = addr >> 8
        self.data += bytearray((l, h))

    def link_crc(self, crc):
        l = crc & 0xff
        h = crc >> 8
        self.data += bytearray((l, h))

    def link_length(self, length):
        self.data += bytearray((length,))

    def link_header(self, src, dst):
        self.link_start()
        self.link_length(0)
        self.link_control(1, 1, 0, 0, 4)  # 4: LINK_UNCONFIRMED_USER_DATA
        self.link_destination(dst)
        self.link_source(src)

    def transport_header(self, fin, fir, seq):
        ctrl = seq
        ctrl |= fin << 7
        ctrl |= fir << 6
        self.data += bytearray((ctrl,))

    def application_header(self, fir, fin, con, uns, seq, function):
        ctrl = seq
        ctrl |= fir << 7
        ctrl |= fin << 6
        ctrl |= con << 5
        ctrl |= uns << 4
        self.data += bytearray((ctrl, function))

    def object_header(self, group, variation, qualifier):
        self.data += bytearray((group, variation, qualifier))

    def object_value1(self, v):
        self.data += bytearray((v,))

    def object_value2(self, v):
        v0 = (v >> 0) & 0xff
        v1 = (v >> 8) & 0xff
        self.data += bytearray((v0, v1))

    def object_value4(self, v):
        v0 = (v >> 0) & 0xff
        v1 = (v >> 8) & 0xff
        v2 = (v >> 16) & 0xff
        v3 = (v >> 24) & 0xff
        self.data += bytearray((v0, v1, v2, v3))

    @staticmethod
    def request_class(src, dst, cls):
        function = 1  # READ
        group = 60  # all
        variation = cls + 1  # variation 0 means class 1 poll
        qualifier = 6  # no range, requesting all values

        req = DnpAsm()
        req.makePrologue(src, dst, function)

        req.object_header(group, variation, qualifier)

        req.makeEpilogue()
        return req.data;

    @staticmethod
    def request_confirm(src, dst, cls):
        function = 0  # CONFIRM

        req = DnpAsm()
        req.makePrologue(src, dst, function)
        req.makeEpilogue()
        return req.data;

    @staticmethod
    def request_analog_in(src, dst, index):
        function = 1  # READ
        group = 30  # analog input
        variation = 0  # unspecified
        qualifier = 0x28  # with 2-octet index, 2-octet count

        req = DnpAsm()
        req.makePrologue(src, dst, function)

        req.object_header(group, variation, qualifier)
        req.object_value2(1)  # count
        req.object_value2(index)  # index

        req.makeEpilogue()
        return req.data;

    @staticmethod
    def request_analog_out_status(src, dst, index):
        function = 1  # READ
        group = 40  # analog output status
        variation = 0  # unspecified
        qualifier = 0x28  # with 2-octet index, 2-octet count

        req = DnpAsm()
        req.makePrologue(src, dst, function)

        req.object_header(group, variation, qualifier)
        req.object_value2(1)  # count
        req.object_value2(index)  # index

        req.makeEpilogue()
        return req.data;

    @staticmethod
    def request_binary_in(src, dst, index):
        function = 1  # READ
        group = 1  # binary input
        variation = 0  # unspecified
        qualifier = 0x28  # with 2-octet index, 2-octet count

        req = DnpAsm()
        req.makePrologue(src, dst, function)

        req.object_header(group, variation, qualifier)
        req.object_value2(1)  # count
        req.object_value2(index)  # index

        req.makeEpilogue()
        return req.data;

    @staticmethod
    def request_analog_out(src, dst, index, value):
        function = 5  # APPLICATION_DIRECT_OPERATE
        group = 41  # analog output
        variation = 1  # 32bit value and control status
        qualifier = 0x28  # with 2-octet index, 2-octet count

        req = DnpAsm()
        req.makePrologue(src, dst, function)

        req.object_header(group, variation, qualifier)
        req.object_value2(1)  # count
        req.object_value2(index)
        req.object_value4(value)
        req.object_value1(0)  # control

        req.makeEpilogue()
        return req.data;

    @staticmethod
    def response_analog_out(src, dst, index, value):
        function = 129  # RESPONSE
        group = 41  # analog output
        variation = 1  # 32bit value and control status
        qualifier = 0x28  # with 2-octet index, 2-octet count

        req = DnpAsm()
        req.makePrologue(src, dst, function)

        req.object_value2(0)  # iin
        req.object_header(group, variation, qualifier)
        req.object_value2(1)  # count
        req.object_value2(index)
        req.object_value4(value)
        req.object_value1(0)  # control

        req.makeEpilogue()
        return req.data;

    @staticmethod
    def response_analog_out_status(src, dst, index, value):
        function = 129  # RESPONSE
        group = 40  # analog output status
        variation = 1  # 32bit value and control status
        qualifier = 0x28  # with 2-octet index, 2-octet count

        req = DnpAsm()
        req.makePrologue(src, dst, function)

        req.object_value2(0)  # iin
        req.object_header(group, variation, qualifier)
        req.object_value2(1)  # count
        req.object_value2(index)
        req.object_value1(0)  # flag
        req.object_value4(value)

        req.makeEpilogue()
        return req.data;

class DnpDisasmBase(object):
    '''Base class with convenience functions'''
    def get_data1(self):
        result = self.data[0]
        del self.data[:1]
        return result

    def get_data2(self):
        result = self.data[0] + (self.data[1] << 8)
        del self.data[:2]
        return result

    def get_data4(self):
        result = self.get_data2() + (self.get_data2() << 16)
        return result

    def get_data6(self):
        result = self.get_data4() + (self.get_data2() << 32)
        return result

    def peek_data2(self):
        result = self.data[0] + (self.data[1] << 8)
        return result

class DnpDataObject(object):
    def __init__(self):
	self.index = None
	self.value = None
	self.flag = None

class DnpDisasmObject(DnpDisasmBase):
    '''Parse object part of DNP packet bytes'''
    def __init__(self, data):
        assert isinstance(data, bytearray)
        self.data = data

        # Get object header
        self.group = self.get_data1()
        self.variation = self.get_data1()
        self.qualifier = self.get_data1()
        self.prefix = (self.qualifier >> 4) & 0x7
        self.ranges = (self.qualifier >> 0) & 0xf
        self.objects = []

        # Process range
        start = -1
        end = -1
        count = -1
        if self.ranges == 0:
            start = self.get_data1()
            end = self.get_data1()
        elif self.ranges == 1:
            start = self.get_data2()
            end = self.get_data2()
        elif self.ranges == 7:
            count = self.get_data1()
        elif self.ranges == 8:
            count = self.get_data2()
        elif self.ranges == 6:
            pass
        else:
            print 'ERROR: Not implemented: group={} variation={} prefix={} ranges={}'.format(
                self.group, self.variation, self.prefix, self.ranges)
            return
        if count < 0:
            count = end + 1 - start

        # Print object header
        rangestr = '<UNKNOWN RANGE>'
        if start >= 0:
            rangestr = '{}-{}'.format(start, end)
        elif count >= 0:
            rangestr = 'count={}'.format(count)
        print '    object (group={} variation={} prefix={} ranges={}({}))'.format(
            self.group, self.variation, self.prefix, self.ranges, rangestr)

        # Debug dump before objects
        # print '>>>', dump_bytes(self.data)

        # Read objects under this object header
        if self.ranges == 6: # No range field, implies all values
            pass
        elif self.ranges != 11:
            for i in range(count):
                # Create a data object
                do = DnpDataObject()
                self.objects.append(do)

                # Decide index
                if self.prefix == 0:
                    do.index = i + start
                elif self.prefix == 1:
                    do.index = self.get_data1()
                elif self.prefix == 2:
                    do.index = self.get_data2()
                elif self.prefix == 3:
                    do.index = self.get_data4()

                # Switch by group and variation
                gv = (self.group, self.variation)
                if gv == (1, 1):  # 8bit binary packed
                    do.value = self.get_data1()
                    assert count == 1  # Then only bit 0 is valid
                    print '      BI index {}: {}'.format(do.index, do.value & 0x1)
                elif gv == (1, 0):  # Index only
                    print '      index {}'.format(do.index)
                elif gv == (1, 2):  # 8bit binary
                    do.flag = self.get_data1()
                    do.value = (do.flag >> 7) & 0x1
                    do.flag &= 0x3f
                    print '      BI index {}: {} (flag=0x{:x})'.format(do.index, do.value, do.flag)
                elif gv == (2, 3):  # 8bit flag and 16bit relative time
                    do.flag = self.get_data1()
                    time = self.get_data2()
                    print '      BI index {}: 0x{:x}'.format(do.index, do.flag)
                elif gv == (30, 0):  # Index only
                    print '      index {}'.format(do.index)
                elif gv == (30, 1):  # 32bit with flag
                    do.flag = self.get_data1()
                    do.value = self.get_data4()
                    print '      AI index {}: {} (flag=0x{:x})'.format(do.index, do.value, do.flag)
                elif gv == (30, 3):  # 32bit value
                    do.value = self.get_data4()
                    print '      AI index {}: {}'.format(do.index, do.value)
                elif gv == (34, 2):  # 32bit value
                    do.value = self.get_data4()
                    print '      deadband index {}: {}'.format(do.index, do.value)
                elif gv == (40, 0):  # Index only
                    print '      index {}'.format(do.index)
                elif gv == (40, 1):  # 32bit with flag
                    do.flag = self.get_data1()
                    do.value = self.get_data4()
                    print '      AO index {}: {} (flag=0x{:x})'.format(do.index, do.value, do.flag)
                elif gv == (40, 2):  # 16bit with flag
                    do.flag = self.get_data1()
                    do.value = self.get_data2()
                    print '      AO index {}: {} (flag=0x{:x})'.format(do.index, do.value, do.flag)
                elif gv == (41, 1):  # 32bit value and control flag
                    do.value = self.get_data4()
                    do.flag = self.get_data1()
                    print '      AO index {}: {} (flag=0x{:x})'.format(do.index, do.value, do.flag)
                elif gv == (42, 2):  # 16bit value and control flag
                    do.flag = self.get_data1()
                    do.value = self.get_data2()
                    print '      AO index {}: {} (flag=0x{:x})'.format(do.index, do.value, do.flag)
                else:
                    print 'ERROR: Not implemented: group={} variation={} prefix={}'.format(
                        self.group, self.variation, self.prefix)
                    return
        else:
            print 'ERROR: Not Implemented: prefix={} ranges={} start={} end={} count={}'.format(
                self.prefix, self.ranges, start, end, count)

class Function:
    def __init__(self, data):
        self.code = data

    def __str__(self):
        result = '<UNKNOWN COMMAND>'
        if self.code == 0x0: result = 'CONFIRM'
        if self.code == 0x1: result = 'READ'
        if self.code == 0x2: result = 'WRITE'
        if self.code == 0x5: result = 'DIRECT_OPERATE'
        if self.code == 0x81: result = 'RESPONSE'
        return '{:s}({:d})'.format(result, self.code)

class Control:
    def __init__(self, data):
        self.code = data
        self.con = False
        self.uns = False
        self.strings = []
        if self.code & (1 << 5):  # Confirmation required
            self.strings.append('CON')
            self.con = True
        if self.code & (1 << 4):  # Unsolicited response
            self.strings.append('UNS')
            self.uns = True

    def __str__(self):
        return '0x{:02x}({:s})'.format(self.code, ','.join(self.strings))

class IIN:
    def __init__(self, data):
        self.code = data

    def __str__(self):
        result = []
        if self.code & (1 << 0): result.append('ALL_STATIONS')
        if self.code & (1 << 1): result.append('CLASS1')
        if self.code & (1 << 2): result.append('CLASS2')
        if self.code & (1 << 3): result.append('CLASS3')
        if self.code & (1 << 4): result.append('NEED_TIME')
        if self.code & (1 << 5): result.append('LOCAL_CONTROL')
        if self.code & (1 << 6): result.append('DEVICE_TROUBLE')
        if self.code & (1 << 7): result.append('DEVICE_RESTART')
        if self.code & (1 << 8): result.append('NO_FUNC_CODE_SUPPORT')
        if self.code & (1 << 9): result.append('OBJECT_UNKNOWN')
        if self.code & (1 << 10): result.append('PARAMETER_ERROR')
        if self.code & (1 << 11): result.append('EVENT_BUFFER_OVERFLOW')
        if self.code & (1 << 12): result.append('ALREADY_EXECUTING')
        if self.code & (1 << 13): result.append('CONFIG_CORRUPT')
        return '0x{:x}({:s})'.format(self.code, ','.join(result))

class DnpDisasm(DnpDisasmBase):
    '''Parse DNP packet bytes'''
    def __init__(self, data, request=False):
        assert isinstance(data, bytearray)
        self.data = bytearray(data)  # Make a copy

        if request:
            print '>', dump_bytes(self.data)
        else:
            print '<', dump_bytes(self.data)

        # Get link header
        self.link_start = self.get_data2()
        self.link_length = self.get_data1()
        self.link_control = self.get_data1()
        self.link_destination = self.get_data2()
        self.link_source = self.get_data2()
        self.link_crc = self.get_data2()
        # print '    link (control=0x{:x}, dst=0x{:x}, src=0x{:x})'.format(
        #     self.link_control, self.link_destination, self.link_source)
        assert self.link_start == 0x6405

        # Remove payload CRC, for each 16 byte payload and at the end
        p = 0
        while p < len(self.data):
            if len(self.data) - p >= 18:
                p += 16
            else:
                p = len(self.data) - 2
            del self.data[p:p+2]

        # Get transport header
        self.transport_header = self.get_data1()
        # print '    transport (header=0x{:x})'.format(self.transport_header)

        # Debug dump for application after without CRC
        # print '>>>', dump_bytes(self.data)

        # Get application header
        self.application_control = self.get_data1()
        self.application_function = self.get_data1()
        control = Control(self.application_control)
        function = Function(self.application_function)
        print '    application (control={:s} function={:s})'.format(control, function)

        self.application_con = control.con
        self.application_uns = control.uns

        if self.application_function & 0x80:
            self.iin = self.get_data2()
            iin = IIN(self.iin)
            print '    iin={:s}'.format(iin)

        # Get objects
        self.objects = []
        while self.data:
            self.objects.append(DnpDisasmObject(self.data))
