import argparse
import sys
import csv
import smtplib
import time
import datetime

from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# from PyQt5.QtSerialPort import QSerialPort
# from PyQt5.QtSerialPort import QSerialPortInfo
from PyQt5.QtSerialPort import *
from PyQt5.QtCore import *


print()

argparser = argparse.ArgumentParser(description='Log data from DHT11 temperature and humidity sensor.')
argparser.add_argument('-o', '--OutputFile', default='DHT11Log.csv', help='File where the output will be written (CSV format).')
argparser.add_argument('-s', '--SamplingIntervalMin', type=float, default=0.05, help='Period in minutes between two consecutive measurements.')
argparser.add_argument('-t', '--ThresholdCelsius', type=float, default=24.0, help='Trigger threshold temperature that activates warning.')
args = argparser.parse_args()

TemperatureThreshold = float(args.ThresholdCelsius)
print('Output will be logged in:', args.OutputFile)
print('Data sampling interval:', float(args.SamplingIntervalMin))
print('Temperature threshold:', TemperatureThreshold)

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

# State variables

LastTemp = -1.0
CurrentTemp = -1.0

# Main loop

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

  SendEmail = False
  CurrentTemp = float(tTxt)
  if LastTemp != -1.0:
    if CurrentTemp > TemperatureThreshold and LastTemp <= TemperatureThreshold:
      SendEmail = True
    if CurrentTemp <= TemperatureThreshold and LastTemp > TemperatureThreshold:
      SendEmail = True
  LastTemp = CurrentTemp

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

  # Sending email.

  if SendEmail == True:
    sender = "perk.lab.log@gmail.com"
    msg = MIMEMultipart()
    msg['From'] = 'perk.lab.log@gmail.com'
    msg['To'] = 'ungi.tamas@gmail.com, ungi@queensu.ca'
    msg['Subject'] = "Lab humidity = " + hTxt + "%, temp = " + tTxt + "C [end]"
    text=msg.as_string()
    server = smtplib.SMTP('smtp.gmail.com:587')
    server.ehlo()
    server.starttls()
    try:
      server.login('perk.lab.log@gmail.com', 'gaborgoodwin')
    except:
      print("Email login error")
    try:
      server.sendmail(sender,address_book, text)
    except:
      print("Error sending email")

  time.sleep(samplingDelaySec)


sys.exit(0)