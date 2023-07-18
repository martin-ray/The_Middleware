cmake_minimum_required(VERSION 3.19)

project(Example CUDA CXX)
find_package(mgard)
find_package(protobuf)
find_package(hdf5)

# Add include directories
include_directories(
    /usr/include/hdf5/serial
)

# Add library directories
link_directories(
    /usr/lib/x86_64-linux-gnu/hdf5/serial/
)

set (CMAKE_CXX_STANDARD 17)
set (CMAKE_CXX_STANDARD_REQUIRED ON)
set (CMAKE_CUDA_FLAGS "${CMAKE_CUDA_FLAGS} --expt-relaxed-constexpr -w")
add_executable(Example Example.cu)
target_link_libraries(Example
    mgard::mgard
    protobuf
    hdf5
    )
