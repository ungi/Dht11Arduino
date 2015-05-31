import sys

from PyQt5.QtSerialPort import QSerialPort
from PyQt5.QtSerialPort import QSerialPortInfo


print("Searching for Arduino on serail ports...")

portList = QSerialPortInfo.availablePorts()

for portItem in portList:
  print(portItem.portName(), ": ", portItem.description())


sys.exit(0)