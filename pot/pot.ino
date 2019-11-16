#include "DHT.h" // for dht11 reading
//#include <Servo.h> // for servo motor control
#include "kalman.cpp" // kalman's filter
#include <SoftwareSerial.h> // for communication through hc06

// pins
const byte restartButton = 2; // some button
const byte tempSensor = 4; // dht11 temperature sensor
const byte bluetoothPWR = 7; // bluetooth power pin
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

// filters
Kalman lightFilter;
Kalman tempFilter(6.21, 0.05);
Kalman humFilter;

// bluetooth
SoftwareSerial BTSerial(bluetoothTX, bluetoothRX); // to arduino's rx and tx

// dht11
DHT dht(tempSensor, DHT11);

// servo motor
//Servo waterSM;

void restartBT() {
	digitalWrite(bluetoothPWR, HIGH); // power up bluetooth
	BTSerial.begin(9600); // restart serial bridge
	delay(1000); // wait for power on
	digitalWrite(bluetoothPWR, LOW); // power down bluetooth
	delay(100); // wait for power off
}

void set(String name, String pin) {
	Serial.println("[!] Entering setup mode");
	digitalWrite(led, HIGH); // light the light (kinda su mode)

	// kick bt client
	restartBT();

	BTSerial.print("AT+NAME"); BTSerial.print(name); delay(1000); // restore name
	BTSerial.print("AT+PIN"); BTSerial.print(pin); delay(1000); // restore pin

	// double blink (kinda success)
	for (int i = 0; i < 4; i++) {
		digitalWrite(led, i % 2);
		delay(500);
	}
	digitalWrite(led, LOW);

	Serial.print("[!] Settings were changed to name '"); Serial.print(name);
	Serial.print("' and pin: "); Serial.println(pin);
}

void setServo(int pos) {
	int degree = constrain(pos, 0, 180);
	//waterSM.write(degree);

	int pulse = degree * int(1856 / 180) + 544;
	for (int i = 0; i < 32; i++) {
		digitalWrite(servoMotor, HIGH);
		delayMicroseconds(pulse);
		digitalWrite(servoMotor, LOW);
		delay(20);
	}

	Serial.print("[!] Servo was set to ");
	Serial.println(pos);
}

void reset() { // reset parameters
	Serial.println("[!] Resetting the settings...");
	Serial.println("[!] Bluetooth pair must be disconnected (bt red light should blink)");

	setServo(0);

	// reset name and pin
	String name = String("SmartPot");
	String pin = String("0000");
	set(name, pin);
}

void setup() {
	pinMode(restartButton, INPUT);
	dht.begin();
	//waterSM.attach(servoMotor);
	setServo(0);
	pinMode(led, OUTPUT);
	pinMode(lightSensor, INPUT);
	pinMode(waterSensor, INPUT);
	pinMode(tempSensor, INPUT);
	pinMode(bluetoothPWR, OUTPUT);
	digitalWrite(bluetoothPWR, HIGH); // power up bluetooth

	Serial.begin(9600);
	BTSerial.begin(9600);
	Serial.println("[!] SmartPot has started");
}

void onMessage(String msg) { // recieve bluetooth message event
	msg.remove(msg.lastIndexOf('\n'));
	Serial.print("[>] "); Serial.println(msg);
	msg.toLowerCase();

	if (msg.startsWith("get")) {
		String ans;
		ans.concat("Light:"); ans.concat(lightIntersity);
		ans.concat("|Water:"); ans.concat(waterLevel);
		ans.concat("|Temp:"); ans.concat(temperature);
		ans.concat("|Hum:"); ans.concat(humidity);

		BTSerial.println(ans);
		Serial.print("[<] "); Serial.println(ans);
	} else if (msg.startsWith("setup")) {
		String name = String("SmartPot"); // custom name
		//name.concat(msg.substring(9));
		String pin = msg.substring(5, 9); // 4-digit pin
		set(name, pin); // set the settings

		Serial.println("[!] SmartPot was paired to the hub");
	} else if (msg.startsWith("set")) {
		int servoPos = msg.substring(3).toInt(); // parse degree
		setServo(servoPos);
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
	if (isnan(t)) t = -1000.0;
	float res = tempFilter.filter(t);
	return res;
}

float getHum() { // get humidity
	float h = dht.readHumidity();
	if (isnan(h)) h = -1000.0;
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
		if (msg.startsWith("AT")) {
			msg.remove(msg.indexOf('\n'));
			restartBT(); // kick clients
			BTSerial.print(msg);
		} else onMessage(msg);
	}

	delay(1000);
}
