cmake_minimum_required(VERSION 3.0)
project(test)


include(FindProtobuf)
find_package(Protobuf REQUIRED)
include_directories(${PROTOBUF_INCLUDE_DIR})

add_executable(test test.cpp proto/test/cpp/test.pb.cc)
target_link_libraries(test ${PROTOBUF_LIBRARY})
target_compile_features(test PRIVATE cxx_std_17)
