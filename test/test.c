#include <stdio.h>

#define test_IMPLEMENTATION
#include "lib/test/c/network.h"

#define test_IDS_IMPLEMENTATION
#include "lib/test/c/ids.h"

#define test_WATCHDOG_IMPLEMENTATION
#include "lib/test/c/watchdog.h"

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
  // ENUMS
  uint8_t data[8] = {0};
  test_serialize_CAR_STATUS(data, test_InverterStatus_ON,
                            test_InverterStatus_ON, test_CarStatus_RUN);

  printf("CAR_STATUS ");
  print_bits(data, 8);

  // BITSETS
  memset(data, 0, 8);
  test_serialize_DAS_ERRORS(data, test_DasErrors_FSM |
                                      test_DasErrors_INVL_TOUT |
                                      test_DasErrors_PEDAL_IMPLAUSIBILITY);

  printf("DAS_ERRORS ");
  print_bits(data, 8);

  return 0;
}
