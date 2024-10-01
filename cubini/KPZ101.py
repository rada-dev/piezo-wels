import time
import usb
from vcp_terminal import ComPort
from struct import pack


class KPZ101(object):

    channel = 1
    destination = 0x50
    source = 0x01

    MAX_POSITION = 30 # micrometers
    position_to_device_unit_sf = 32767. / MAX_POSITION     # scale factor

    # The piezo actuator connected to the T-Cube has a specific  maximum operating voltage range.
    # This parameter sets the maximum output to the value specified as follows:
    # 0x01 VOLTAGELIMIT_75V 75V limit
    # 0x02 VOLTAGELIMIT_100V 100V limit
    # 0x03 VOLTAGELIMIT_150V 150V limit
    MAX_VOLTAGE = 75  # one of 75, 100, 150V
    voltage_to_device_unit_sf = 32767. / MAX_VOLTAGE  # scale factor, short int value = voltage * scale factor

    # When the T-Cube Piezo Driver unit is used in conjunction with the T-Cube Strain Gauge Reader (TSG001)
    # on the T-Cube Controller Hub (TCH001), a feedback signal can be passed from the Strain Gauge Reader to the Piezo unit.
    # High precision closed loop operation is then possible using our complete range of feedback-equipped piezo actuators.
    # This parameter is used to select the way in which the feedback signal is routed to the Piezo unit as follows:
    # 0x01 HUB_ANALOGUEIN_A the feedback signals run through all T-Cube bays.
    # 0x02 HUB_ANALOGUEIN_B the feedback signals run between adjacent pairs of T-Cube bays (i.e. 1&2, 3&4, 5&6).
    # This setting is useful when several pairs of Strain Gauge/Piezo Driver cubesare being used on the same hub.
    # 0x03 EXTSIG_SMA the feedback signals run through the rear panel SMA connectors.
    FEEDBACK_SOURCE = 0x03 # only matters in case of closed loop operation

    # When in closed-loop mode, position is maintained by a feedback signal from the piezo actuator.
    # This is only possible when using actuators equipped with position sensing.
    # This method sets the control loop status The Control Mode is specified in the Mode parameter as follows:
    # 0x01  Open Loop (no feedback)
    # 0x02  Closed Loop (feedback employed)
    # 0x03  Open Loop Smooth
    # 0x04  Closed Loop Smooth
    POS_CONTROL_MODE = 0x04

    # The following values are entered into the VoltSrc parameter to select the various analog sources.
    # 0x00 Software Only: Unit responds only to software inputs and the HV amp output is that set using the SetVoltOutput method or via the GUI panel.
    # 0x01 External Signal: Unit sums the differential signal on the rear panel EXT IN (+) and EXT IN (-) connectors
    # with the voltage set using the SetVoltOutput method
    # 0x02 Potentiometer: The HV amp output is controlled by a potentiometer input (either on the control panel, or
    # connected to the rear panel User I/O D-type connector) summed with the voltage set using the SetVoltOutput method.
    # The values can be 'bitwise ord' to sum the software source with either or both of the other source options.
    INPUT_MODE = 0x00

    def __init__(self, serial_number=None):
        self.com = None
        
        # find matching USB devices
        devs = usb.core.find(find_all=True, idVendor=0x0403, idProduct=0xfaf0)
        kpz = None
        for dev in devs:
            try:
                sn = usb.util.get_string(dev, dev.iSerialNumber)
                if sn == str(serial_number):
                    kpz = dev
                    #print(kpz)
            except:
                pass
            
        assert kpz is not None, 'No KPZ101 with matching serial number {} found!'.format(serial_number)
        
        time.sleep(.1)
        # open serial communication channel with the device
        com = ComPort(usb_device=kpz)
        
        # initialize FTDI chip according to APT documentation
        com.setLineCoding(baudrate=115200, databits=8, stopbits=1)
        
        # Get HW info; MGMSG_HW_REQ_INFO; may be require by a K Cube to allow confirmation Rx messages
        # use the length of the response as a check for uncorrupted communication
        hw_info = self.get_hwinfo()
        assert len(hw_info) == 90, 'Communication corrupted for KPZ101 SN {}, response length {} != 90 bytes.'.format(serial_number, len(hw_info))

        self.com = com
        time.sleep(0.1)

    def __del__(self):
        if self.com is not None:
            self.com.disconnect()

    def get_hwinfo(self):
        """
        MGMSG_HW_REQ_INFO 0x0005
        """
        com.write(pack('<HBBBB', 0x0005, 0x00, 0x00, 0x50, 0x01))
        time.sleep(0.1)
        return com.readBytes()

    def set_max_voltage(self):
        """
        Sets the maximum output voltage and update the voltage scale factor.
        MGMSG_PZ_SET_TPZ_IOSETTINGS 0x07D4
        """
        # 0x01 VOLTAGELIMIT_75V 75V limit
        # 0x02 VOLTAGELIMIT_100V 100V limit
        # 0x03 VOLTAGELIMIT_150V 150V limit
        voltage_bytes = {75: 0x01, 100: 0x02, 150: 0x03}
        voltage_byte = voltage_bytes[self.MAX_VOLTAGE]
        self.com.write(pack('<HBBBBHHHHH', 0x07D4, 0x0A, 0x00, self.destination | 0x80, self.source, self.channel, voltage_byte, self.FEEDBACK_SOURCE, 0x00, 0x00))
    
    def set_input_mode(self):
        """
        Sets the input mode. For documentation check APT docs p. 160.
        MGMSG_PZ_SET_INPUTVOLTSSRC 0x0652
        """
        assert self.INPUT_MODE in (0x00, 0x01, 0x02), "Invalid input mode"
        self.com.write(pack('<HBBBBHH', 0x0652, 0x04, 0x00, self.destination | 0x80, self.source, self.channel, self.INPUT_MODE))

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

    def set_pos_control_mode(self):
        """
        MGMSG_PZ_SET_POSCONTROLMODE 0x0640
        """
        assert pos_control_mode in (0x01, 0x02, 0x03, 0x04), "Invalid control mode"
        self.com.write(pack('<HBBBB', 0x0640, self.channel, self.POS_CONTROL_MODE, self.destination, self.source))
    
    def set_output_voltage(self, v):
        """
        Set the output voltage.
        MGMSG_PZ_SET_OUTPUTVOLTS 0x0643
        """
        assert 0 <= v <= self.MAX_VOLTAGE, 'Voltage out of limits!'
        voltage_device_units = int(round(self.voltage_to_device_unit_sf * v))     # short int value to be sent
        # 0x0643 command id
        # 0x04 0x00 data packet length -> 4B (channel 2B + voltage 2B)
        # dest | 0x80 destination, bitwise or cause data packet follows
        # 4B data packet (channel 2B + voltage 2B)
        self.com.write(pack('<HBBBBHH', 0x0643, 0x04, 0x00, self.destination | 0x80, self.source, self.channel, voltage_device_units))

    def set_output_position(self, p):
        """
        Used to set the output position of piezo actuator. This command is applicable only in Closed Loop mode.
        If called when in Open Loop mode it is ignored.
        The position of the actuator is relative to the datum set for the arrangement using the ZeroPosition method.
        MGMSG_PZ_SET_OUTPUTPOS 0x0646
        """
        # !!! The position of the actuator is relative to the datum set for the arrangement using the ZeroPosition method.
        assert -self.MAX_POSITION <= p <= self.MAX_POSITION, "Invalid value, MAX_POSITION set to {}".format(self.MAX_POSITION)
        # The output position of the piezo relative to the zero position.
        # The voltage is set as a signed 16-bit integer in the range 0 to 32767 (0 to 7FFF).
        # This corresponds to 0 to 100% of the maximum piezo extension. The negative range (0x800 to FFFF) is not used at this time.
        position_device_units = int(round(self.position_to_device_unit_sf * p))
        self.com.write(pack('<HBBBBHH', 0x0646, 0x04, 0x00, self.destination | 0x80, self.source, self.channel, position_device_units))

    def set_proportional_integral_terms(self, proportional, integral):
        """
        MGMSG_PZ_SET_PICONSTS 0x0655
        """
        assert 0 <= p <= 255, "Invalid value, accepted values 0-255"
        assert 0 <= i <= 255, "Invalid value, accepted values 0-255"
        self.com.write(pack('<HBBBBHHH', 0x0655, 0x06, 0x00, self.destination | 0x80, self.source, self.channel, proportional, integral))


def test():
    d = KPZ101(29253043)
    d.set_max_voltage()
    d.set_input_mode()
    d.set_pos_control_mode()
    d.set_proportional_integral_terms(120, 120)
    d.enable_channel()
    print d


if __name__ == '__main__':
    test()
