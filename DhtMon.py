import argparse
import sys
import csv
import time
import datetime

# from PyQt5.QtSerialPort import QSerialPort
# from PyQt5.QtSerialPort import QSerialPortInfo
from PyQt5.QtSerialPort import *
from PyQt5.QtCore import *


print()

argparser = argparse.ArgumentParser(description='Log data from DHT11 temperature and humidity sensor.')
argparser.add_argument('-o', '--OutputFile', default='DHT11Log.csv', help='File where the output will be written (CSV format).')
argparser.add_argument('-s', '--SamplingIntervalMin', type=float, default=0.05, help='Period in minutes between two consecutive measurements.')
args = argparser.parse_args()

print('Output will be logged in:', args.OutputFile)
print('Data sampling interval:', float(args.SamplingIntervalMin))

print("Searching for Arduino on serail ports...")

portList = QSerialPortInfo.availablePorts()

portReader = None

for portItem in portList:
  # print(portItem.portName(), ":", portItem.description())
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
# print("Baud rate:", serialPort.baudRate())

serialPort.open(QIODevice.ReadOnly)
readData = serialPort.readAll()

# Computing sampling delay.

samplingDelaySec = float(args.SamplingIntervalMin) * 60.0

while True:
  for i in range(2):
    serialPort.waitForReadyRead(3000)
    readData.append(serialPort.readAll())

  # Find first set of measurement values.

  bs = bytes(readData)
  dataString = bs.decode('ascii', 'ignore')
  firstPos = dataString.find('OK.')
  #print("First position:", firstPos)
  hPos = dataString.find("H:", firstPos, len(dataString)-firstPos)
  tPos = dataString.find("T:", firstPos, len(dataString)-firstPos)
  endPos = dataString.find(";", firstPos, len(dataString)-firstPos)
  if len(dataString)-firstPos < 18:
    print("Error: Message too short:", str(dataString))
  if hPos == -1 or tPos == -1:
    print("Error parsing message from Arduino: ", str(dataString))
  hTxt = dataString[hPos+2:tPos]
  tTxt = dataString[tPos+2:endPos]
  #print("H:", hTxt)
  #print("T:", tTxt)

  # Write output to file.
  try:
    f = open(args.OutputFile, 'a', newline='')
    outputWriter = csv.writer(f, delimiter=',')
    timeStamp = time.time()
    dateTimeStamp = datetime.datetime.fromtimestamp(timeStamp).strftime('%Y-%m-%d %H:%M:%S')
    outputWriter.writerow([dateTimeStamp, hTxt, tTxt])
    f.close()
  except:
    print("Warning: Unable to write output file. Data dropped.")

  time.sleep(samplingDelaySec)


sys.exit(0)