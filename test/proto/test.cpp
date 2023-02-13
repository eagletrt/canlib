#include <random>
#include <stdio.h>

#define  CANLIB_TIMESTAMP
#define  bms_NETWORK_IMPLEMENTATION
#define  bms_PROTO_INTERAFCE_IMPLEMENTATION
#include "lib/bms/c/ids.h"
#include "proto/bms/cpp/bms.pb.h"
#include "proto/bms/cpp/proto_interface.h"
#define  primary_NETWORK_IMPLEMENTATION
#define  primary_PROTO_INTERAFCE_IMPLEMENTATION
#include "lib/primary/c/ids.h"
#include "proto/primary/cpp/primary.pb.h"
#include "proto/primary/cpp/proto_interface.h"
#define  secondary_NETWORK_IMPLEMENTATION
#define  secondary_PROTO_INTERAFCE_IMPLEMENTATION
#include "lib/secondary/c/ids.h"
#include "proto/secondary/cpp/secondary.pb.h"
#include "proto/secondary/cpp/proto_interface.h"

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

void add_bms_messages(bms::Pack* pack, bms_devices* devs){
  uint64_t data;
  uint8_t can_data[8];
  for(uint16_t index = 0; index < bms_MESSAGE_COUNT; index++){
    data = 2*(uint64_t)lrand48();
    for(int j = 0; j < 8; j++){
      can_data[j] = (data >> (j*8)) & 0xFF;
    }
    canlib_message_id id = bms_id_from_index(index);
    bms_devices_deserialize_from_id(devs, id, can_data, id/1.0);
    bms_proto_serialize_from_id(id, pack, devs);
  }
}

void add_primary_messages(primary::Pack* pack, primary_devices* devs){
  uint64_t data;
  uint8_t can_data[8];
  for(uint16_t index = 0; index < primary_MESSAGE_COUNT; index++){
    data = 2*(uint64_t)lrand48();
    for(int j = 0; j < 8; j++){
      can_data[j] = (data >> (j*8)) & 0xFF;
    }
    canlib_message_id id = primary_id_from_index(index);
    primary_devices_deserialize_from_id(devs, id, can_data, id/1.0);
    primary_proto_serialize_from_id(id, pack, devs);
  }
}

void add_secondary_messages(secondary::Pack* pack, secondary_devices* devs){
  uint64_t data;
  uint8_t can_data[8];
  for(uint16_t index = 0; index < secondary_MESSAGE_COUNT; index++){
    data = 2*(uint64_t)lrand48();
    for(int j = 0; j < 8; j++){
      can_data[j] = (data >> (j*8)) & 0xFF;
    }
    canlib_message_id id = secondary_id_from_index(index);
    secondary_devices_deserialize_from_id(devs, id, can_data, id/1.0);
    secondary_proto_serialize_from_id(id, pack, devs);
  }
}

int main() {
  srand48(time(NULL));

  bms::Pack bms_pack;
  bms_devices* devs = bms_devices_new();
  primary::Pack primary_pack;
  primary_devices* primary_devs = primary_devices_new();
  secondary::Pack secondary_pack;
  secondary_devices* secondary_devs = secondary_devices_new();

  network_enums net_enums;
  network_signals net_signals;
  network_strings net_strings;

  char wait;
  // printf("Adding messages to proto packs\n");
  // printf("Press enter to continue...\n");
  // scanf("%c", &wait);

  for(int i = 0; i < 10; i++){
    add_bms_messages(&bms_pack, devs);
    add_primary_messages(&primary_pack, primary_devs);
    add_secondary_messages(&secondary_pack, secondary_devs);
  }

  // printf("Deserializing proto packs\n");
  // printf("Press enter to continue...\n");
  // scanf("%c", &wait);

  bms_proto_deserialize(&bms_pack, &net_enums, &net_signals, &net_strings, 0);
  primary_proto_deserialize(&primary_pack, &net_enums, &net_signals, &net_strings, 0);
  secondary_proto_deserialize(&secondary_pack, &net_enums, &net_signals, &net_strings, 0);

  // printf("Printing all the deserialized values\n");
  // printf("Press enter to continue...\n");
  // scanf("%c", &wait);

  for(const auto& message : net_signals){
    for(const auto& signal : message.second){
      printf("SIGNAL >> %s.%s:\n", message.first.c_str(), signal.first.c_str());
      for(int i = 0; i < signal.second.size(); i++){
        printf("\t\t\t%f\n", signal.second[i]);
      }
    }
  }
  for(const auto& message : net_enums){
    for(const auto& signal : message.second){
      printf("ENUM >> %s.%s:\n", message.first.c_str(), signal.first.c_str());
      for(int i = 0; i < signal.second.size(); i++){
        printf("\t\t\t%" PRIu64 "\n", signal.second[i]);
      }
    }
  }
  for(const auto& message : net_strings){
    for(const auto& signal : message.second){
      printf("STRING >> %s.%s:\n", message.first.c_str(), signal.first.c_str());
      for(int i = 0; i < signal.second.size(); i++){
        printf("\t\t\t%s\n", signal.second[i].c_str());
      }
    }
  }

  return 0;
}
