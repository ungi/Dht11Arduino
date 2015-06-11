import argparse
import csv
import datetime
import logging
import smtplib
import sys
import time

from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from PyQt5.QtSerialPort import *
from PyQt5.QtCore import *

# Parse command line arguments.

argparser = argparse.ArgumentParser(description='Log data from DHT11 temperature and humidity sensor.')
argparser.add_argument('-a', '--AddressBook', default='AddressBook.txt', help="Text file with one email address in each line. Emails will be sent to all.")
argparser.add_argument('-o', '--OutputFile', default='DHT11Log.csv', help='File where the output will be written (CSV format).')
argparser.add_argument('-p', '--PasswordFile', default='password.txt', help='File that stores email smtp username and password in the first and second line.')
argparser.add_argument('-s', '--SamplingIntervalMin', type=float, default=0.05, help='Period in minutes between two consecutive measurements.')
argparser.add_argument('-t', '--ThresholdCelsius', type=float, default=24.0, help='Trigger threshold temperature that activates warning.')
argparser.add_argument('-d', '--DebugMode', action='store_true', help='Set this for debug mode logging.')
argparser.add_argument('-f', '--From', default="DHT Monitor", help='What should appear as sender in the emails')
args = argparser.parse_args()

if args.DebugMode:
  logging.basicConfig(filename='DhtMonLog.txt',level=logging.DEBUG)
else:
  logging.basicConfig(filename='DhtMonLog.txt',level=logging.INFO)
logging.basicConfig(format='%(asctime)s %(message)s')

TemperatureThreshold = float(args.ThresholdCelsius)

# Print parameters, so user can check if they are right.

print('Using email addresses from:', args.AddressBook)
print('Email sender:              ', args.From)
print('Output will be logged in:  ', args.OutputFile)
print('Email smtp password file:  ', args.PasswordFile)
print('Temperature threshold:     ', TemperatureThreshold)
print('Data will be recorded in every', float(args.SamplingIntervalMin), "minutes")

# Find Arduino device.

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

serialPort.open(QIODevice.ReadOnly)
readData = serialPort.readAll()

# Computing sampling delay.

SamplingDelaySec = float(args.SamplingIntervalMin) * 60.0

# State variables

LastTemp = -1.0
CurrentTemp = -1.0
LastGreetingDay = ""
LastWarningHour = ""

# Main loop

while True:
  logging.debug("Loop cycle started -----------------------------------")

  # Flush the message buffer.

  serialPort.waitForReadyRead(5000)
  readData = serialPort.readAll()

  time.sleep(2.5) # Wait for fresh data.

  # Read new data.

  serialPort.waitForReadyRead(5000)
  readData = serialPort.readAll()

  # Find measurement values in the received message.

  ByteString = bytes(readData)
  dataString = ByteString.decode('ascii', 'ignore')

  logging.debug("Received string: " + dataString)

  FirstPos = dataString.find("OK.")
  if len(dataString) - FirstPos < 16:
    print("Error: Message too short:", str(dataString))
    logging.error('Message too short, length=' + str(len(dataString)) + " -- msg=" + str(dataString))
    continue

  HumidPos = dataString.find("H:", FirstPos, len(dataString))
  TemprPos = dataString.find("T:", FirstPos, len(dataString))
  EndPos   = dataString.find(";", FirstPos, len(dataString))
  if HumidPos == -1:
    logging.error('Error parsing message from Arduino: ' + str(dataString))
    logging.error("Could not find: H:")
    continue
  if TemprPos == -1:
    logging.error('Error parsing message from Arduino: ' + str(dataString))
    logging.error("Could not find: T:")
    continue
  HumidText = dataString[HumidPos + 2:TemprPos]
  TemprText = dataString[TemprPos + 2:EndPos]

  # Compute timestamp.

  TimeStamp = time.time()
  DateTimeStamp = datetime.datetime.fromtimestamp(TimeStamp).strftime('%Y-%m-%d %H:%M:%S')
  DateStamp = datetime.datetime.fromtimestamp(TimeStamp).strftime('%Y-%m-%d')
  HourStamp = datetime.datetime.fromtimestamp(TimeStamp).strftime('%H')

  logging.debug("Computed timestamp for log file: " + DateTimeStamp)

  # Decide if email needs to be sent.

  SendEmail = False

  try:
    CurrentTemp = float(TemprText)
  except:
    logging.error('TemprText cannot be converted:' + TemprText)
    logging.error(sys.exc_info()[0])
    continue

  logging.debug("Current temp  = " + str(CurrentTemp))
  logging.debug("Last temp     = " + str(LastTemp))

  if LastTemp == -1.0:
    FilteredCurrentTemp = CurrentTemp
  else:
    FilteredCurrentTemp = ( CurrentTemp + LastTemp ) / 2.0

  logging.debug("Filtered temp = " + str(FilteredCurrentTemp))

  if LastTemp != -1.0 and FilteredCurrentTemp > TemperatureThreshold:
    if LastWarningHour != HourStamp:
      SendEmail = True
      LastWarningHour = HourStamp
    else:
      logging.debug("Skipping warning because HourStamp=" + HourStamp + " and LastWarningHour=" + LastWarningHour)

  LastTemp = CurrentTemp

  if HourStamp == "08" and DateStamp != LastGreetingDay:  # Send an email at about 8 am every day.
    SendEmail = True
    logging.debug("Greeting, because DateStamp=" + DateStamp + " and LastGreetingDay=" + LastGreetingDay)
    LastGreetingDay = DateStamp


  # Write current measurements in output to file.

  try:
    f = open(args.OutputFile, 'a', newline='')
    outputWriter = csv.writer(f, delimiter=',')
    outputWriter.writerow([DateTimeStamp, HumidText, str(FilteredCurrentTemp)])
    f.close()
  except:
    print("Warning: Unable to write output file. Data dropped.")
    logging.error(sys.exc_info()[0])
    continue

  # Read smtp password from file.

  try:
    PasswordFile = open(args.PasswordFile, "r")
    SmtpUser = PasswordFile.readline()
    SmtpPassword = PasswordFile.readline()
    PasswordFile.close()
  except:
    logging.error("Unable to read file: " + args.PasswordFile + " - Email will not be sent.")
    SendEmail = False

  # Read recipient email addresses from file.

  try:
    AddressFile = open(args.AddressBook, 'r')
    Recipients = AddressFile.readlines()
  except:
    logging.error("Unable to read address book file: " + args.AddressBook + " - Email will not be sent.")
    SendEmail = False

  for i in range(len(Recipients)):
    Recipients[i] = Recipients[i].rstrip()  # Removing endline characters.

  # Sending email.

  if SendEmail == True:
    msg = MIMEMultipart()
    msg['From'] = args.From
    msg['To'] = 'Undisclosed recipients'
    msg['Subject'] = "Humidity = " + HumidText + "%, temperature = " + str(FilteredCurrentTemp) + "C [end]"
    text=msg.as_string()
    server = smtplib.SMTP('smtp.gmail.com:587')
    server.ehlo()
    server.starttls()
    try:
      server.login(SmtpUser, SmtpPassword)
    except:
      print("Email login error")
      logging.error(sys.exc_info()[0])
    try:
      server.sendmail(SmtpUser, Recipients, text)
      logging.debug('Email sent')
    except:
      print("Error sending email")
      logging.error(sys.exc_info()[0])

  time.sleep(SamplingDelaySec)


sys.exit(0)