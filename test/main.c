#define test_IMPLEMENTATION
#include "common.h"
#include "lib/test/c/network.h"

int main() {
  uint8_t data[8] = {0};
  test_serialize_CAR_STATUS(data, test_InverterStatus_ON,
                            test_InverterStatus_ON, test_CarStatus_RUN);

  print_bits(data, 8);

  return 0;
}
