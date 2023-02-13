#include <stdio.h>

#define CANLIB_TIMESTAMP
#define bms_NETWORK_IMPLEMENTATION
#define bms_PROTO_INTERAFCE_IMPLEMENTATION
#include "lib/bms/c/ids.h"
#include "proto/bms/cpp/bms.pb.h"
#include "proto/bms/cpp/proto_interface.h"

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
  bms::Pack pack;
  bms_devices* devs = bms_devices_new();

  ((bms_message_BOARD_STATUS*)devs[bms_INDEX_BOARD_STATUS_CELLBOARD0]->message_raw)->_timestamp = 1;
  ((bms_message_BOARD_STATUS*)devs[bms_INDEX_BOARD_STATUS_CELLBOARD0]->message_raw)->errors = 1000;
  for(int i = 0; i < 100; i++){
    bms_proto_serialize_from_id(bms_ID_BOARD_STATUS_CELLBOARD0, &pack, devs);
  }

  network_enums net_enums;
  network_signals net_signals;
  network_strings net_strings;

  bms_proto_deserialize(&pack, &net_enums, &net_signals, &net_strings, 0);

  for(const auto& message : net_signals){
    for(const auto& signal : message.second){
      for(int i = 0; i < signal.second.size(); i++){
        printf("signal\t\t%s.%s: %f\n", message.first.c_str(), signal.first.c_str(), signal.second[i]);
      }
    }
  }
  for(const auto& message : net_enums){
    for(const auto& signal : message.second){
      for(int i = 0; i < signal.second.size(); i++){
        printf("enum\t\t%s.%s: %" PRIu64 "\n", message.first.c_str(), signal.first.c_str(), signal.second[i]);
      }
    }
  }
  for(const auto& message : net_strings){
    for(const auto& signal : message.second){
      for(int i = 0; i < signal.second.size(); i++){
        printf("string\t\t%s.%s: %s\n", message.first.c_str(), signal.first.c_str(), signal.second[i].c_str());
      }
    }
  }

  return 0;
}
