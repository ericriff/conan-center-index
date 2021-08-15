cmake_minimum_required(VERSION 3.1)
project(test_package LANGUAGES C)

include(${CMAKE_BINARY_DIR}/conanbuildinfo.cmake)
conan_basic_setup()

find_package(aws-kvs-c-producer REQUIRED)

add_executable(${PROJECT_NAME} test_package.c)

if(${TEST_COMMON_CURL})
   add_compile_definitions("TEST_COMMON_CURL")
   target_link_libraries(${PROJECT_NAME} aws-kvs-c-producer::cproducer)
endif()

if(${TEST_COMMON_LWS})
   add_compile_definitions("TEST_COMMON_LWS")
   target_link_libraries(${PROJECT_NAME} aws-kvs-c-producer::kvsCommonLws)
endif()
