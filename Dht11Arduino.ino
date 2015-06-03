#include "dht11.h"

dht11 DHT11;

#define DHT11PIN 7

void setup()
{
  Serial.begin(115200);
}

void loop()
{
  int chk = DHT11.read(DHT11PIN);

  switch (chk)
  {
    case DHTLIB_OK: 
		Serial.print("OK."); 
		break;
    case DHTLIB_ERROR_CHECKSUM: 
		Serial.print("Checksum error"); 
		break;
    case DHTLIB_ERROR_TIMEOUT: 
		Serial.print("Time out error"); 
		break;
    default: 
		Serial.print("Unknown error"); 
		break;
  }

  Serial.print("H:");
  Serial.print((float)DHT11.humidity, 1);

  Serial.print("T:");
  Serial.print((float)DHT11.temperature, 1);
  Serial.print(";");
  
  delay(2000);
}
