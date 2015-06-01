import argparse
import sys


# from PyQt5.QtSerialPort import QSerialPort
# from PyQt5.QtSerialPort import QSerialPortInfo
from PyQt5.QtSerialPort import *
from PyQt5.QtCore import *


print()

argparser = argparse.ArgumentParser(description='Log data from DHT11 temperature and humidity sensor.')
argparser.add_argument('OutputFile', default='DHT11Log.csv')
args = argparser.parse_args()

print('Output will be logged in:', args.OutputFile)

print("Searching for Arduino on serail ports...")

portList = QSerialPortInfo.availablePorts()

portReader = None

for portItem in portList:
  print(portItem.portName(), ":", portItem.description())
  if portItem.description() == "Arduino Uno":
    portReader = portItem

if portReader == None:
  print("Arduino was not found")
  sys.exit(1)

try:
  serialPort = QSerialPort(portReader)
except ValueError:
  print("Could not cast item to QSerialPort!")
  sys.exit(1)

serialPort.setBaudRate(115200)

print("Arduino was found on port ", serialPort.portName())
print("Baud rate:", serialPort.baudRate())

print("Trying to read data")

serialPort.open(QIODevice.ReadOnly)

readData = serialPort.readAll()

for i in range(2):
  serialPort.waitForReadyRead(4000)
  readData.append(serialPort.readAll())

#print(str(readData).decode("utf-8", "strict"))
bs = bytes(readData)

print(bs.decode('ascii', 'ignore'))



sys.exit(0)