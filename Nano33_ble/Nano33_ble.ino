/* Author: Rik Starmans
   Organization: Hexastorm
   License: GPL3
   About: polygon is pulsed for PANASONIC (AN44000A chip) scheme
          polygon is rotated and accelerometer data and IR
          sensor data is collected
 */ 
#include <Wire.h>
#include <SPI.h>
#include <SparkFunLSM9DS1.h> // use modified fork


// main example
//https://github.com/andenore/NordicSnippets/blob/master/examples/pwm/main.c
// arduino example
// http://fab.cba.mit.edu/classes/865.18/people/akaspar/code/chirp_optimized.ino

#include "nrf.h"



#define PWM0_ENABLED 1
#define polygonPin A1
#define irsensorPin A6

// Settings
const int polygon_div = 4; // 952/(5*2)  --> pulse at 95 Hertz 
const int startup_time = 60;  // seconds
const int samples = 10; 

LSM9DS1 imu;
//NRF_PWM0->PSEL.OUT[0]= 0;;



// TODO: move sample_freqs to LSM9DS1 class
const int sample_freqs[6] = {10, 50, 119, 238, 476, 952};
unsigned int sample_freq = sample_freqs[6-1];
int ir_data[samples];
int16_t accel_data[samples];
int polycounter = 0; 


void setup() {
  pinMode(polygonPin, OUTPUT);
  pinMode(irsensorPin, INPUT);
  Serial.begin(115200);
  while (!Serial);
  Wire1.begin();
  Wire1.setClock(400000);
  while (!imu.begin(0x6B, 0X1E, Wire1)) {
    Serial.println("Failed to communicate with LSM9DS1.");
    Serial.println("Will retry in 1 second.");
    delay(1000);
  }
  sample_freq = sample_freqs[imu.settings.accel.sampleRate-1];
  imu.calibrate();
}

void polyflip(){
  polycounter = polycounter + 1;
  if (polycounter>polygon_div){
    polycounter = 0;
    digitalWrite(polygonPin, !digitalRead(polygonPin)); 
  }   
}



void loop() {
    Serial.println("Press 1 to start samples.");
    delay(1000);
    int int_received = Serial.parseInt();
    switch(int_received) {
      // parseInt polls and returns 0 if nothing is received so ignored
      case 0 : break;
      case 1 : {
        Serial.print("Spin up time ");
        Serial.print(startup_time);
        Serial.println(" seconds.");
        unsigned int iteration = 0;
        while( iteration < startup_time*sample_freq){
          if (imu.accelAvailable()){
            ++iteration;
            polyflip();
           }
        }
        Serial.print("Measurement time ");
        Serial.print(samples/sample_freq);
        Serial.println(" seconds.");
        iteration = 0;
        while(iteration<samples){
          if (imu.accelAvailable()){
            ir_data[iteration] = analogRead(irsensorPin);
//            imu.readAccel();
            accel_data[iteration] = imu.ax;
            ++iteration;
            polyflip();
          }
        }
        Serial.print("Writing results ");
        Serial.println(samples);
        for(int sample = 0; sample<samples; sample++){
          Serial.println(ir_data[sample]);
        }
        Serial.println("Measurement completed");
        break;
        }
      default:{
        Serial.println(int_received); 
        Serial.println("Invalid command");
        break;
        }
    };
}
