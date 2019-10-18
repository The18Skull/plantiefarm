#include "DHT.h"
#include <Servo.h>
#include <SoftwareSerial.h> // for communication through hc06

// easiest kalman's filter realization
class Kalman {
  private:
    float deviation = 0.25;
    float coeff = 0.05;
    float pc = 0.0;
    float g = 0.0;
    float p = 1.0;
    float xp = 0.0;
    float zp = 0.0;
    float xe = 0.0;
  public:
    Kalman() {
      return;
    }
    Kalman(float dev, float c) {
      this->deviation = dev;
      this->coeff = c;
    }
    float filter(float val) {
      this->pc = this->p + this->coeff;
      this->g = this->pc / (this->pc + this->deviation);
      this->p = (1.0 - this->g) * this->pc;
      this->xp = this->xe;
      this->zp = this->xp;
      this->xe = this->g * (val - this->zp) + this->xp;
      return this->xe;
    }
};

// pins
const byte restartButton = 2; // some button
const byte tempSensor = 4; // dht11 temperature sensor
const byte servoMotor = 5; // sg90 servo motor
const byte bluetoothRX = 7; // hc06 bluetooth uart rx
const byte bluetoothTX = 8; // hc06 bluetooth uart tx
const byte led = 13; // arduino's led
const byte lightSensor = A4; // some mh-series photoresistor
const byte waterSensor = A5; // some default arduino water sensor

// variables
float lightIntersity = 0.0;
float waterLevel = 0.0;
float temperature = 0.0;
int servoState = 0;

// filters
Kalman lightFilter;
Kalman tempFilter(6.21, 0.05);

// bluetooth
SoftwareSerial BTSerial(bluetoothTX, bluetoothRX); // to arduino's rx and tx

// dht11
DHT dht(tempSensor, DHT11);

// servo motor
Servo waterSM;

void reset() { // reset parameters
  Serial.println("[!] Now restarting...");
  //BTSerial.write("AT+NAMEHC-06");
  //BTSerial.write("AT+AT+BAUD4");
  //BTSerial.write("AT+PIN0000");
  for (int i = 0; i < 4; i++) { // double blink (kinda success)
    delay(100);
    digitalWrite(led, i % 2 == 0);
  }
  delay(1000);
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
  attachInterrupt(digitalPinToInterrupt(restartButton), reset, FALLING);

  Serial.begin(9600);
  Serial.println("[!] Arduino has started");
  BTSerial.begin(9600);
}

void onMessage(String msg) { // recieve bluetooth message event
  Serial.print("[>] ");
  Serial.println(msg);

  if (msg.compareTo(String("GET")) == 0) {
    String ans;
    ans.concat("Light:");
    ans.concat(lightIntersity);
    ans.concat("|Water:");
    ans.concat(waterLevel);
    ans.concat("|Temp:");
    ans.concat(temperature);

    char buf[100];
    ans.toCharArray(buf, 100);
    BTSerial.write(buf);

    Serial.print("[<] ");
    Serial.println(ans);
  } else if (msg.startsWith(String("SET"))) {
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

//float getHum() { // get humidity
//  float h = dht.readHumidity();
//  if (isnan(h)) {
//    h = -1000.0;
//  }
//  float res = humFilter.filter(h);
//  return res;
//}

void loop() {
  lightIntersity = getLight();
  waterLevel = getWater();
  temperature = getTemp();

  if (BTSerial.available()) {
    String msg = BTSerial.readString();
    onMessage(msg);
  }
  if (Serial.available()) {
    String msg = Serial.readString();
    onMessage(msg);
  }

  delay(100);
}
