/* Author: Rik Starmans
 * About: PWM test
 *
 */
#define PWM_PIN 5UL //(PIN A1 is PIN0.05 on microcontoller)
#define PWM_POLARITY_OFFSET  (1 << 15)
#include <nrf.h>

// Looked at various snippets
// Nordic; works;
// https://github.com/andenore/NordicSnippets/blob/master/examples/pwm/main.c
// Other examples one can look at;
//  https://lists.zephyrproject.org/g/devel/message/1732
//  http://fab.cba.mit.edu/classes/865.18/people/akaspar/code/chirp_optimized.ino
uint16_t buf[] = {(1 << 15) | 1500};

void setup() {
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
  NRF_PWM0->COUNTERTOP = 10000; // 20ms period
  NRF_PWM0->SEQ[0].CNT = ((sizeof(buf) / sizeof(uint16_t)) << PWM_SEQ_CNT_CNT_Pos);
  NRF_PWM0->SEQ[0].ENDDELAY = 0;
  NRF_PWM0->SEQ[0].PTR = (uint32_t)&buf[0];
  NRF_PWM0->SEQ[0].REFRESH = 0;
  NRF_PWM0->SHORTS = 0;
  NRF_PWM0->ENABLE = 1;
  NRF_PWM0->TASKS_SEQSTART[0] = 1;

  Serial.begin(115200);
  while (!Serial);
}

void loop() {
  NRF_PWM0->ENABLE = 1;
  NRF_PWM0->TASKS_SEQSTART[0] = 1;
  Serial.println("10 seconds on");
  delay(10000);
  Serial.println("10 seconds off");
  NRF_PWM0->ENABLE = 0;
  NRF_PWM0->TASKS_SEQSTART[0] = 0;
  delay(10000);
}
