#include <Arduino.h>

#include <WiFi.h>
#include <WiFiUdp.h>
// cguzb chuzd fb
const char* ssid = "MERCUSYS_D96C";
const char* password = "";

const char* udpAddress = "192.168.1.100";  // Dirección IP del AP (ESP32 B)
const int udpPort = 1234;  //  Puerto UDP
WiFiUDP udp;
const int micPin = 33;  // Pin ADC donde está conectado el micrófono (A0)
const int buffer = 256;
byte sample[buffer];

void setup() {
  Serial.begin(115200);

  analogReadResolution(8);  // Resolución a 8 bits para audio
  analogSetAttenuation(ADC_11db);  // Atenuación para 0-3.6V

  WiFi.begin(ssid, password);
  // Esperar conexión
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.println("Conectando al AP...");
  }

  Serial.println("Conectado al AP.");
  delay(100);
}

void loop() { 
  // Leer muestra del micrófono
  /*sample = analogRead(micPin);
  String s = String(sample);
  Serial.println(sample);*/
  // Enviar la muestra por UDP

  for (int i = 0; i < buffer; i++)
  {
    sample[i] = analogRead(micPin);
  }

  udp.beginPacket(udpAddress, udpPort);
  //udp.print((String)sample.c_str());
  Serial.println(sizeof(sample));
  udp.write(sample, (int)sizeof(sample));
  udp.endPacket();

  //delay(2);  // Ajusta según la frecuencia de muestreo deseada (500 Hz aprox.)
}