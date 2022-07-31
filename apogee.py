from serial import Serial
from time import sleep
import sys
import struct

GET_VOLT = b'\x55!'
READ_CALIBRATION = b'\x83!'
SET_CALIBRATION = b'\x84%s%s!'
READ_SERIAL_NUM = b'\x87!'
GET_LOGGING_COUNT = b'\xf3!'
GET_LOGGED_ENTRY = b'\xf2%s!'
ERASE_LOGGED_DATA = b'\xf4!'

class Quantum(object):
    def __init__(self):
        """Initializes class variables, and attempts to connect to device"""
        print()
        self.quantum = None
        self.offset = 0.0
        self.multiplier = 1.0
        self.serialnumner=0
        self.connect_to_device()

    def connect_to_device(self):
        """This function creates a Serial connection with the defined comport
        and attempts to read the calibration values"""
        #port = '/dev/tty.usbmodem1411' # you'll have to check your device manager and put the actual com port here
        port = sys.argv[1]

        print("serial port", port)
        self.quantum = Serial(port, 115200, timeout=5)
        try:
            self.quantum.write(READ_SERIAL_NUM)
            sernum = self.quantum.read(5)[1:5]
            self.serialnumber=struct.unpack('<f', sernum)[0]
            print("serial number: ", int(self.serialnumber))
            self.quantum.write(READ_CALIBRATION)
            calibration= self.quantum.read(10)
            multiplier = calibration[1:5]
            offset=calibration[5:9]
            self.multiplier = struct.unpack('<f', multiplier)[0]
            self.offset = struct.unpack('<f', offset)[0]
            print("multiplier", self.multiplier)
            print("offset", self.offset)
        except IOError as data:
            print("x",data)
            self.quantum = None


    def get_micromoles(self):
        """This function converts the voltage to micromoles"""
        voltage = self.read_voltage()
        if voltage == 9999:
            # you could raise some sort of Exception here if you wanted to
            return
        # this next line converts volts to micromoles
        micromoles = (voltage - self.offset) * self.multiplier * 1000

        if micromoles < 0:
            micromoles = 0
        return micromoles

    def read_voltage(self):
        """This function averages 5 readings over 1 second and returns the result."""
        if self.quantum == None:
            try:
                print("Connect")
                self.connect_to_device()
            except IOError:
                print("IO Error")
                return 9999
            print("Success")
        # you can raise some sort of exception here if you need to return

        # store the responses to average
        response_list = []
        # change to average more or less samples over the given time period
        number_to_average = 11
        # change to shorten or extend the time duration for each measurement
        # be sure to leave as floating point to avoid truncation
        number_of_seconds = 0.66
        for i in range(number_to_average):
            try:
                self.quantum.write(GET_VOLT)
                response = self.quantum.read(5)[1:]
            except IOError as data:
                # dummy value to know something went wrong. could raise an
                # exception here alternatively
                return 9999
            else:
                if not response:
                    print ("No resp.")
                    continue

                # if the response is not 4 bytes long, this line will raise
                # an exception
                voltage = struct.unpack('<f', response)[0]
                response_list.append(voltage)
                sleep(number_of_seconds/number_to_average)
        if response_list:
            response_list.sort()
#            print(response_list)
            return response_list[int(len(response_list)/2)]
        return 0.0



if __name__ == '__main__':
    q = Quantum()
    while True:
        print(q.get_micromoles())
