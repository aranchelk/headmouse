import serial
import io
import time


ser = serial.Serial('/dev/ttyACM0', 9600, timeout=1)

for x in range(0,1000):
    ser.write("32100\n-1\n-1\n");
    time.sleep(.03)
