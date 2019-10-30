#include "DHT.h" // for dht11 reading
#include "kalman.cpp" // kalman's filter
#include <Servo.h> // for servo motor control
#include <SoftwareSerial.h> // for communication through hc06

// pins
const byte restartButton = 2; // some button
const byte tempSensor = 4; // dht11 temperature sensor
const byte servoMotor = 9; // sg90 servo motor
const byte bluetoothTX = 10; // hc06 bluetooth tx
const byte bluetoothRX = 11; // hc06 bluetooth rx
const byte led = 13; // arduino's led
const byte lightSensor = A4; // some mh-series photoresistor
const byte waterSensor = A5; // some default arduino water sensor

// variables
float lightIntersity = 0.0;
float waterLevel = 0.0;
float temperature = 0.0;
float humidity = 0.0;
int servoState = 0;

// filters
Kalman lightFilter;
Kalman tempFilter(6.21, 0.05);
Kalman humFilter;

// bluetooth
SoftwareSerial BTSerial(bluetoothTX, bluetoothRX); // to arduino's rx and tx

// dht11
DHT dht(tempSensor, DHT11);

// servo motor
Servo waterSM;

void reset() { // reset parameters
  digitalWrite(led, HIGH); // light the light (kinda su mode)
  Serial.println("[!] Resetting the settings...");
  Serial.println("[!] Bluetooth pair must be disconnected (bt red light should blink)");

  delay(1000); // wait for user to disconnect
  BTSerial.print("AT+NAMEHC-06"); delay(1000); // restore name
  BTSerial.print("AT+BAUD4"); delay(1000); // restore baud
  BTSerial.print("AT+PIN0000"); delay(1000); // restore pin

  servoState = 0; // reset servo motor
  waterSM.write(servoState);

  for (int i = 0; i < 4; i++) { // double blink (kinda success)
    digitalWrite(led, i % 2);
    delay(500);
  }
  digitalWrite(led, LOW);
}

void setup() {
  pinMode(restartButton, INPUT);
  dht.begin();
  waterSM.attach(servoMotor);
  waterSM.write(servoState);
  pinMode(led, OUTPUT);
  pinMode(lightSensor, INPUT);
  pinMode(waterSensor, INPUT);
  pinMode(tempSensor, INPUT);

  Serial.begin(9600);
  Serial.println("[!] SmartPot has started");
  BTSerial.begin(9600);
}

void onMessage(String msg) { // recieve bluetooth message event
  msg.remove(msg.lastIndexOf('\n'));
  Serial.print("[>] ");
  Serial.println(msg);
  msg.toLowerCase();

  if (msg.startsWith("get")) {
    String ans;
    ans.concat("Light:");
    ans.concat(lightIntersity);
    ans.concat("|Water:");
    ans.concat(waterLevel);
    ans.concat("|Temp:");
    ans.concat(temperature);
    ans.concat("|Hum:");
    ans.concat(humidity);

    BTSerial.println(ans);

    Serial.print("[<] ");
    Serial.println(ans);
  } else if (msg.startsWith("setup")) {
    String pin = msg.substring(5, 9); // 4-digit pin
    int idx = msg.substring(9).toInt(); // any-digit index number

    delay(1000); // wait for user to disconnect
    BTSerial.print("AT+NAMESmartPot-"); BTSerial.print(idx); delay(1000);
    BTSerial.print("AT+PIN"); BTSerial.print(pin); delay(1000);

    Serial.print("[!] SmartPot was paired to the hub with index ");
    Serial.print(idx);
    Serial.print(" and password ");
    Serial.println(pin);
  } else if (msg.startsWith("set")) {
    servoState = msg.substring(3).toInt();
    servoState = 0 <= servoState && servoState <= 180 ? servoState : 0;
    waterSM.write(servoState);

    Serial.print("[!] Servo was set to ");
    Serial.println(servoState);
  }
}

float getLight() { // get light state and illumination
  int raw = analogRead(lightSensor);
  float conv = (1.0 - float(raw) / 1023.0) * 100.0;
  float res = lightFilter.filter(conv);
  return res;
}

float getWater() { // get water level
  int raw = analogRead(waterSensor);
  float res = (float(raw) / 1023.0) * 100.0;
  return res;
}

float getTemp() { // get temperature
  float t = dht.readTemperature();
  if (isnan(t)) {
    t = -1000.0;
  }
  float res = tempFilter.filter(t);
  return res;
}

float getHum() { // get humidity
  float h = dht.readHumidity();
  if (isnan(h)) {
    h = -1000.0;
  }
  float res = humFilter.filter(h);
  return res;
}

void loop() {
  lightIntersity = getLight();
  waterLevel = getWater();
  temperature = getTemp();
  humidity = getHum();

  if (digitalRead(restartButton)) reset(); // check reset button state

  if (BTSerial.available()) {
    String msg = BTSerial.readString();
    onMessage(msg);
  }
  if (Serial.available()) {
    String msg = Serial.readString();
    if (msg.startsWith("AT")) { // only if unpaired
      msg.remove(msg.indexOf('\n'));
      BTSerial.print(msg);
    }
    else onMessage(msg);
  }

  delay(1000);
}
