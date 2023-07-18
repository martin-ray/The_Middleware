#include <cmath>
#include <cstddef>

#include <algorithm>
#include <array>
#include <iostream>
#include <vector>
#include <chrono>
#include <highfive/H5File.hpp>
#include <mgard/mdr.hpp>
#include <iostream>

#include "mgard/compress.hpp"
#include "mgard/compress_x_lowlevel.hpp"


std::string filename = "/scratch/aoyagir/step1_500_test.h5";

/*
g++ compress_hdf5.cpp -I/usr/include/hdf5/serial -L/usr/lib/x86_64-linux-gnu/hdf5/serial/ -lhdf5 -lzstd -lmgard -lprotobuf
*/

int main() {

    // Open the file as read-only
    HighFive::File file(filename, HighFive::File::ReadOnly);

    // Get the dataset named "data"
    HighFive::DataSet dataset = file.getDataSet("data");

    // Retrieve the datatype of the dataset
    HighFive::DataType datatype = dataset.getDataType();
    std::cout << "Datatype: " << datatype.string() << std::endl;

    // Retrieve the dataspace of the dataset
    HighFive::DataSpace dataspace = dataset.getSpace();

    // Get the number of dimensions of the dataset
    std::size_t numDimensions = dataspace.getNumberDimensions();
    std::cout << "Number of dimensions: " << numDimensions << std::endl;

    // Get the size of each dimension
    auto dimensions = dataspace.getDimensions();
    std::cout << "Dimensions: ";
    for (const auto& dim : dimensions) {
        std::cout << dim << " ";
    }

    std::cout << std::endl;

    // slicing 
    long long unsigned int start_1 = 0;
    long long unsigned int start_2 = 0;
    long long unsigned int start_3 = 0;
    long long unsigned int start_4 = 0;

    long long unsigned int n1 = 1;
    long long unsigned int n2 = 512;
    long long unsigned int n3 = 512;
    long long unsigned int n4 = 128;

    long long int NumElements = n1*n2*n3*n4;

    std::vector<float> sim_data(NumElements);

    // For measuring load time
    auto start = std::chrono::high_resolution_clock::now();

    dataset.select({start_1,start_2,start_3,start_4,start_5},
                    {offset_1, offset_2, offset_3, offset_4, offset_5}).read(sim_data.data());

    // Stop measuring load time
    auto end = std::chrono::high_resolution_clock::now();

    // Calculate the duration in milliseconds
    auto duration = std::chrono::duration_cast<std::chrono::milliseconds>(end - start).count();

    // // Print the execution time
    std::cout << "time_to_load " << duration << " milliseconds" << std::endl;


    std::vector<mgard_x::SIZE> shape{n1, n2, n3, n4};
    mgard_x::Config config;
    mgard_x::Hierarchy<4, double, mgard_x::OPENMP> hierarchy(shape, config);
    mgard_x::Array<4, double, mgard_x::OPENMP> in_array(shape);
    in_array.load(sim_data.data());


    std::cout << "Compressing with MGARD-X OPENMP backend..." << std::flush;
    double tol = 0.01, s = 0, norm;
    mgard_x::Compressor compressor(hierarchy, config);
    mgard_x::Array<1, unsigned char, mgard_x::OPENMP> compressed_array;
    
    for(int i = 0 ; i < 20 ; i++){

        auto start = std::chrono::high_resolution_clock::now();

        compressor.Compress(in_array, mgard_x::error_bound_type::REL, tol, s, norm,
                            compressed_array, 0);

        auto end = std::chrono::high_resolution_clock::now();

        mgard_x::DeviceRuntime<mgard_x::OPENMP>::SyncQueue(0);

        // get the time and throughput
        auto duration = std::chrono::duration_cast<std::chrono::milliseconds>(end - start).count();

        // Get compressed size in number of bytes.
        size_t compressed_size = compressed_array.shape(0);
        unsigned char *compressed_array_cpu = compressed_array.hostCopy();

        // `compressed` contains the compressed data buffer. We can query its size in
        // bytes with the `size` member function.
        std::cout << "compression ratio: "
                    << static_cast<float>(NumElements * sizeof(loaded_data.data())) / compressed.size()
                    << std::endl 
                    << NumElements * sizeof(loaded_data.data())
                    << " bytes -> " 
                    << compressed.size()
                    << " bytes"
                    <<  std::endl 
                    << "ThroughPut:"
                    << (float)NumElements * sizeof(loaded_data.data())/ duration*1000/1024.0/1024.0/1024.0
                    << " (GByte/sec)"
                    << std::endl << std::endl;

        tolerance *= 10;
    }

  return 0;
}
