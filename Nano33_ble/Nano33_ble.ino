/* Author: Rik Starmans
   Organization: Hexastorm
   License: GPL3
   About: polygon is pulsed for PANASONIC (AN44000A chip) scheme
          polygon is rotated and accelerometer data and IR
          sensor data is collected
 */ 
// rotor pulsed via pin A1, i.e. pin 0.05 on microcontroller
#include <Wire.h>
#include <SPI.h>
#include <SparkFunLSM9DS1.h> // use modified fork
#include "nrf.h"

#define PWM_PIN 5UL  
#define irsensorAPin A6
#define irsensorDPin 2


// Settings
const int startup_time = 10;  // seconds
const int samples = 3000;       
const int frequency = 400;    // Hertz


LSM9DS1 imu;
// TODO: move sample_freqs to LSM9DS1 class
const int sample_freqs[6] = {10, 50, 119, 238, 476, 952};
unsigned int sample_freq;
int ir_data[samples];
int16_t accel_data[samples];
uint16_t buf[] = {(1 << 15) | 1500}; // used for duty cycle, must be global

void setuppolygon(int frequency) {
  // sets up hardware pwm
  //  source https://github.com/andenore/NordicSnippets/blob/master/examples/pwm/main.c
  // Start accurate HFCLK (XOSC)
  NRF_CLOCK->TASKS_HFCLKSTART = 1;
  while (NRF_CLOCK->EVENTS_HFCLKSTARTED == 0) ;
  NRF_CLOCK->EVENTS_HFCLKSTARTED = 0;
  // Configure PWM_PIN as output, and set it to 0
  NRF_GPIO->DIRSET = (1 << PWM_PIN);
  NRF_GPIO->OUTCLR = (1 << PWM_PIN);
  NRF_PWM0->PRESCALER   = PWM_PRESCALER_PRESCALER_DIV_16; // 1 us
  NRF_PWM0->PSEL.OUT[0] = PWM_PIN;
  NRF_PWM0->MODE        = (PWM_MODE_UPDOWN_Up << PWM_MODE_UPDOWN_Pos);
  NRF_PWM0->DECODER     = (PWM_DECODER_LOAD_Common       << PWM_DECODER_LOAD_Pos) | 
                          (PWM_DECODER_MODE_RefreshCount << PWM_DECODER_MODE_Pos);
  NRF_PWM0->LOOP        = (PWM_LOOP_CNT_Disabled << PWM_LOOP_CNT_Pos);
  NRF_PWM0->COUNTERTOP = round(1.0/(frequency)*1000000); // assumes prescaler is DIV_16 
  NRF_PWM0->SEQ[0].CNT = ((sizeof(buf) / sizeof(uint16_t)) << PWM_SEQ_CNT_CNT_Pos);
  NRF_PWM0->SEQ[0].ENDDELAY = 0;
  NRF_PWM0->SEQ[0].PTR = (uint32_t)&buf[0];
  NRF_PWM0->SEQ[0].REFRESH = 0;
  NRF_PWM0->SHORTS = 0;
  motoron(false);
}


void motoron(bool on){
  NRF_PWM0->ENABLE = (int) on;
  NRF_PWM0->TASKS_SEQSTART[0] = (int) on;
}


void setup() {
  setuppolygon(frequency);
  pinMode(irsensorDPin, INPUT); 
  pinMode(irsensorAPin, INPUT);
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


void loop() {
    Serial.println("Press 1 to start samples.");
    Serial.println("Press 2 to calibrate IR sensor.");
    Serial.println("Press 3 to spin polygon.");
    Serial.setTimeout(2000);
    int int_received = Serial.parseInt();
    switch(int_received) {
      // parseInt polls and returns 0 if nothing is received so ignored
      case 0 : break;
      case 1 : {
        motoron(true);
        Serial.print("Process time ");
        Serial.print(round(startup_time+samples/sample_freq));
        Serial.println(" seconds.");
        // wait for polygon to stabilize
        unsigned int iteration = 0;
        int tijd = millis();
        //TODO: you could simplify with sleep
        //      move the check after samples
        while(iteration < startup_time*sample_freq){
             if (imu.accelAvailable())
                {
                imu.readAccel();
                iteration = iteration + 1;
                }
        }
        int verschil = millis()-tijd;
        if(1.1*verschil<startup_time*1000||startup_time*1000<0.9*verschil){
          // frequency accelerometer is probably wrong
          Serial.println("Error: time difference out of bounds");
        }
        // execute measurements
        iteration = 0;
        int digitalout = 1;
        while(iteration<samples){
          if(digitalRead(irsensorDPin) == 0) digitalout = 0;
          if (imu.accelAvailable()){
            //ir_data[iteration] = analogRead(irsensorAPin);
            ir_data[iteration] = digitalout;
            imu.readAccel();
            accel_data[iteration] = imu.ax;
            digitalout = 1;
            ++iteration;
          }
        }
        motoron(false);
        Serial.print("Rotor frequency ");
        Serial.print(frequency);
        Serial.println(" Hz.");
        Serial.print("Sample frequency ");
        Serial.print(sample_freq);
        Serial.println(" Hz.");
        Serial.print("Samples collected ");
        Serial.println(samples);
        for(int sample = 0; sample<samples; sample++){
          Serial.println(ir_data[sample]);
          Serial.println(accel_data[sample]);
        }
        Serial.println("Measurement completed");
        break;
        }
      case 2 :{
        Serial.setTimeout(500);
        Serial.println("Starting IR calibration, press 1 to exit.");
        while(true)
        {
          if (Serial.parseInt() == 1) break;
          Serial.println(analogRead(irsensorAPin));
          Serial.println(digitalRead(irsensorDPin));
        }
        break;
      }
      case 3 :{
        motoron(true);
        while(true){
          Serial.setTimeout(500);
          Serial.println("Spinning polygon, press 1 to exit.");
          if (Serial.parseInt() == 1){
            motoron(false);
            break;
          }
        }
        break; 
      }      
      default:{
        Serial.println(int_received); 
        Serial.println("Invalid command");
        break;
        }
    };
}
