cmake_minimum_required(VERSION 3.19)

project(Example CXX)
find_package(mgard)

set (CMAKE_CXX_STANDARD 17)
set (CMAKE_CXX_STANDARD_REQUIRED ON)
add_executable(refactor refactor.cpp)
target_link_libraries(refactor mgard::mgard)
add_executable(reconstructor reconstructor.cpp)
target_link_libraries(reconstructor mgard::mgard)
