import sys
import time

# from PyQt5.QtSerialPort import QSerialPort
# from PyQt5.QtSerialPort import QSerialPortInfo
from PyQt5.QtSerialPort import *
from PyQt5.QtCore import *



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

print("Arduino was found on port ", serialPort.portName())

print("Trying to read data")

serialPort.open(QIODevice.ReadOnly)

readData = serialPort.readAll()
serialPort.waitForReadyRead(4000)
readData.append(serialPort.readAll())
serialPort.waitForReadyRead(4000)
readData.append(serialPort.readAll())
serialPort.waitForReadyRead(4000)
readData.append(serialPort.readAll())
serialPort.waitForReadyRead(4000)
readData.append(serialPort.readAll())

#print(str(readData).decode("utf-8", "strict"))
print(str(readData).decode(encoding='UTF-8'))

sys.exit(0)