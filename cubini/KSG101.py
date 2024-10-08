import time
import usb
from vcp_terminal import ComPort
from struct import pack


class KSG101(object):

    channel = 1
    destination = 0x50
    source = 0x01

    def __init__(self, serial_number=None):
        self.com = None

        # find matching USB devices
        devs = usb.core.find(find_all=True, idVendor=0x0403, idProduct=0xfaf0)
        ksg = None
        for dev in devs:
            try:
                sn = int(usb.util.get_string(dev, dev.iSerialNumber))
                if sn == serial_number:
                    ksg = dev
                    break
            except:
                pass

        assert ksg is not None, 'No KPZ101 with matching serial number {} found!'.format(serial_number)

        time.sleep(.1)
        # open serial communication channel with the device
        self.com = ComPort(usb_device=ksg)

        # initialize FTDI chip according to APT documentation
        self.com.setLineCoding(baudrate=115200, databits=8, stopbits=1)
        time.sleep(.1)

        # Get HW info; MGMSG_HW_REQ_INFO; may be require by a K Cube to allow confirmation Rx messages
        # use the length of the response as a check for uncorrupted communication
        hw_info = self.get_hwinfo()
        print hw_info
        assert len(hw_info) == 90, 'Communication corrupted for KSG101 SN {}, response length {} != 90 bytes.'.format(serial_number, len(hw_info))

        time.sleep(0.1)

    def __del__(self):
        if self.com is not None:
            self.com.disconnect()

    def get_hwinfo(self):
        """
        MGMSG_HW_REQ_INFO 0x0005
        """
        self.com.write(pack('<HBBBB', 0x0005, 0x00, 0x00, 0x50, 0x01))
        time.sleep(0.1)
        return self.com.readBytes()

    def enable_channel(self):
        """
        Enables the high voltage ouput.
        MGMSG_MOD_SET_CHANENABLESTATE 0x0210
        """
        self.com.write(pack('<HBBBB', 0x0210, self.channel, 0x01, self.destination, self.source))

    def disable_channel(self):
        """
        Enables the high voltage ouput.
        MGMSG_MOD_SET_CHANENABLESTATE 0x0210
        """
        self.com.write(pack('<HBBBB', 0x0210, self.channel, 0x02, self.destination, self.source))

    def set_sg_settings(self):
        """
        MGMSG_PZ_SET_TSG_IOSETTINGS 0x07DA
        """

    def set_zero(self):
        """
        MGMSG_PZ_SET_ZERO 0x0658
        """
        self.com.write(pack('<HBBBB', 0x0658, self.channel, 0x00, self.destination, self.source))

    def get_status(self):
        """
        MGMSG_PZ_REQ_PZSTATUSUPDATE 0x0660
        MGMSG_PZ_GET_PZSTATUSUPDATE 0x0661
        """
        self.com.write(pack('<HBBBB', 0x0660, self.channel, 0x00, self.destination, self.source))
        time.sleep(0.1)
        return self.com.readBytes()

    def get_sg_reading(self):
        """
        get strain gauge reading
        MGMSG_PZ_REQ_TSG_READING 0x07DD
        MGMSG_PZ_GET_TSG_READING 0x07DE
        """
        self.com.write(pack('<HBBBB', 0x07DD, self.channel, 0x00, self.destination, self.source))
        time.sleep(0.1)
        return self.com.readBytes()


def test():
    d = KSG101(59500009)
    d.enable_channel()
    time.sleep(1)
    # print d.set_zero()
    print d.get_status()
    print d


if __name__ == '__main__':
    test()
