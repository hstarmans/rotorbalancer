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
#include <Timer.h> // https://github.com/contrem/arduino-timer

#define polygonPin A3
#define irsensorPin A0

// Settings
const int polygon_freq = 20;  // Hertz
const int startup_time = 60;  // seconds
const int samples = 1000; 

Timer<1, micros> polygon_timer;
LSM9DS1 imu;

// TODO: move sample_freqs to LSM9DS1 class
const int sample_freqs[6] = {10, 50, 119, 238, 476, 952};
unsigned int sample_freq = sample_freqs[6-1];
int ir_data[samples];
int16_t accel_data[samples];

bool toggle_polygon(void *) {
  digitalWrite(polygonPin, !digitalRead(polygonPin)); 
  return true; // keep timer active? true
}


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
  polygon_timer.every( 1000000/polygon_freq, toggle_polygon);
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
        Serial.print(startup_time)
        Serial.println(" seconds.")
        unsigned int iteration = 0;
        while( iteration < startup_time*sample_freq){
          polygon_timer.tick();
          if (imu.accelAvailable()) ++iteration;
        }
        Serial.print("Measurement time ");
        Serial.print(samples/sample_freq);
        Serial.println(" seconds.");
        iteration = 0;
        while(iteration<samples){
          polygon_timer.tick();
          if (imu.accelAvailable()){
            ir_data[iteration] = analogRead(irsensorPin);
            imu.readAccel();
            accel_data[iteration] = imu.ax;
            ++iteration;
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
