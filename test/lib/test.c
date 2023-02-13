#include <stdio.h>

#define CANLIB_TIMESTAMP

#define primary_NETWORK_IMPLEMENTATION
#include "lib/primary/c/network.h"

#define primary_IDS_IMPLEMENTATION
#include "lib/primary/c/ids.h"

#define primary_WATCHDOG_IMPLEMENTATION
#include "lib/primary/c/watchdog.h"

void print_byte_as_bits(char val) {
  for (int i = 7; 0 <= i; i--) {
    printf("%c", (val & (1 << i)) ? '1' : '0');
  }
}

void print_bits(unsigned char* bytes, size_t num_bytes) {
  printf("[ ");
  for (size_t i = 0; i < num_bytes; i++) {
    print_byte_as_bits(bytes[i]);
    printf(" ");
  }
  printf("]\n");
}

int main() {
  uint8_t data[8] = {0};
  primary_serialize_CAR_STATUS(data, primary_InverterStatus_ON,
                            primary_InverterStatus_ON, primary_CarStatus_DRIVE);

  printf("CAR_STATUS ");
  print_bits(data, 8);

  memset(data, 0, 8);
  primary_serialize_DAS_ERRORS(data, primary_DasErrors_FSM |
                                      primary_DasErrors_INVL_TOUT |
                                      primary_DasErrors_PEDAL_IMPLAUSIBILITY);

  printf("DAS_ERRORS ");
  print_bits(data, 8);

  memset(data, 0, 8);
  primary_serialize_SET_TS_STATUS(data, primary_Toggle_OFF);

  printf("SET_TS_STATUS ");
  print_bits(data, 8);

  return 0;
}
