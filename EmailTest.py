import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

address_book = ['ungi.tamas@gmail.com']
msg = MIMEMultipart()
sender = 'ungi@queensu.ca'
subject = "Tema"
body = "This is my email body"

msg['From'] = sender
msg['To'] = ','.join(address_book)
msg['Subject'] = subject
msg.attach(MIMEText(body, 'plain'))
text=msg.as_string()

# Send the message via our SMTP server
server = smtplib.SMTP('smtp.gmail.com:587')
server.ehlo()
server.starttls()

print("Logging in...")
server.login('perk.lab.log@gmail.com', 'gaborgoodwin')
try:
  server.login('perk.lab.log@gmail.com', 'gaborgoodwin')
  print("-- success")
except:
  print("Email login error")

try:
  server.sendmail(sender,address_book, text)
  print('Email sent')
except:
  print("Error sending email")


server.quit()