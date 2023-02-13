cmake_minimum_required(VERSION 3.0)
project(test)

# set copile with debug symbols
set(CMAKE_BUILD_TYPE Debug)

include(FindProtobuf)
find_package(Protobuf REQUIRED)
include_directories(${PROTOBUF_INCLUDE_DIR})

add_executable(test test.cpp proto/bms/cpp/bms.pb.cc proto/primary/cpp/primary.pb.cc proto/secondary/cpp/secondary.pb.cc)
target_link_libraries(test ${PROTOBUF_LIBRARY})
target_compile_features(test PRIVATE cxx_std_17)
