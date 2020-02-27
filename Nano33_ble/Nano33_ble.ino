/* Author: Rik Starmans
   Organization: Hexastorm
   License: GPL3
   About: polygon is pulsed for PANASONIC (AN44000A chip) scheme
          polygon is rotated and accelerometer data and IR
          sensor data is collected
 */ 
#include <Wire.h>
#include <SPI.h>
#include <SparkFunLSM9DS1.h>
#include <Timer.h>

#define polygonPin A3
#define 

auto polygon_timer = timer_create_default();


bool toggle_polygon(void *) {
  digitalWrite(polygonPin, !digitalRead(polygonPin)); 
  return true; // keep timer active? true
}



int int_received = 0;
unsigned long tijd;
LSM9DS1 imu;


void setup() {
  pinMode(polygonPin, OUTPUT);   
  digitalWrite(polygonPin, LOW);
  Serial.begin(115200);
  while (!Serial);
  Wire1.begin();
  Wire1.setClock(400000);
  while (!imu.begin(0x6B, 0X1E, Wire1)) 
  {
    Serial.println("Failed to communicate with LSM9DS1.");
    Serial.println("Will retry in 1 second.");
    delay(1000);
  }
  polygon_timer.every( ,toggle_polygon);
}

void loop() {
    Serial.println("awaiting command");
    Serial.println(imu.settings.gyro.sampleRate);
    delay(1000);
    int_received = Serial.parseInt();
    switch(int_received) {
      case 0 : // parseInt polls and returns 0 if nothing is received so ignored
               break;
      case 1 : {Serial.println("One received");
               int total_time = 952;
               int iteration = 0;
               tijd = millis();
               while(iteration<total_time){
                if (imu.accelAvailable())
                {
                imu.readAccel();
                iteration = iteration + 1;
                }
               }
               unsigned long difference; 
               difference = millis()-tijd;
               if(difference>1100){
                  Serial.println("Test failed");
                  Serial.println(difference);
               }
               else{
                  Serial.println("Test succeeded in ms");
                  Serial.println(difference);
               }
               break;}
      default:{Serial.println(int_received); 
              Serial.println("Invalid command");
              break;}
    };
}
