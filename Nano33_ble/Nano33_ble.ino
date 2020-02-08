/*
  Rotor calibration

  Program that can be used to calibrate a rotor
*/
// modified library
// change acceleration read out
// hex(int('11000000',2)) = 0xc0
// 952 = 1 1 0 
//  2g = 0 0 
// rest default 0 0
// example hex(int('01110000',2)) = 0x70
// 119 = 0 1 1
// 4G = 1 0 
// rest default 0 0
// assumed division head to be changed to 2.0
#include <Arduino_LSM9DS1.h>


// you read out at 952 hertz, so i use a divisor of 48

int divisor_half = 24;

int int_received = 0;
int myInts[1000];
int16_t nogmeerints[1000];

// the setup routine runs once when you press reset:
void setup() {
  pinMode(A0, OUTPUT);  
  // initialize serial communication at 9600 bits per second:
  Serial.begin(9600);
  while (!Serial);
  Serial.println("awaiting command");
  if (!IMU.begin()) {
    Serial.println("Failed to initialize IMU!");
    while (1);
  }
}


// the loop routine runs over and over again forever:
void loop() {
    int_received = Serial.parseInt();
    switch(int_received) {
      case 0 : // parseInt polls and returns 0 if nothing is received so ignored
               break;
      case 1 : {Serial.println("Polygon motor on");
               int polygon_cnt = 0;
               int total_time = 10*952;
               int iteration = 0;
               float x, y, z;
               while(iteration<total_time){
                if (IMU.accelerationAvailable()) {
                    iteration = iteration + 1;
                    IMU.readAcceleration(x, y, z);
                    polygon_cnt = polygon_cnt + 1;
                    if (polygon_cnt >= (divisor_half*2)){
                      polygon_cnt = 0;
                    }
                    if (polygon_cnt >= divisor_half){
                      digitalWrite(A0, HIGH);
                    }
                    else{
                      digitalWrite(A0, LOW);
                    }
               }
               }
               break;}
      default:{Serial.println(int_received); 
              Serial.println("Invalid command");
              break;}
    };
}
