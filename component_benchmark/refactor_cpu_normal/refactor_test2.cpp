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
#include <bitset>
#include <cmath>
#include <cstdlib>
#include <cstring>
#include <ctime>
#include <iomanip>
#include <iostream>
#include <vector>

#include "mgard/mdr.hpp"

using namespace std;

template <class T, class Refactor>
void evaluate(const vector<T> &data, const vector<uint32_t> &dims,
              int target_level, int num_bitplanes, Refactor refactor) {
  struct timespec start, end;
  int err = 0;
  cout << "Start refactoring" << endl;
  err = clock_gettime(CLOCK_REALTIME, &start);
  refactor.refactor(data.data(), dims, target_level, num_bitplanes);
  err = clock_gettime(CLOCK_REALTIME, &end);
  cout << "Refactor time: "
       << (double)(end.tv_sec - start.tv_sec) +
              (double)(end.tv_nsec - start.tv_nsec) / (double)1000000000
       << "s" << endl;
}

template <class T, class Decomposer, class Interleaver, class Encoder,
          class Compressor, class ErrorCollector, class Writer>
void test(const vector<T> &data, const vector<uint32_t> &dims, int target_level,
          int num_bitplanes, Decomposer decomposer, Interleaver interleaver,
          Encoder encoder, Compressor compressor, ErrorCollector collector,
          Writer writer) {
  auto refactor = MDR::ComposedRefactor<T, Decomposer, Interleaver, Encoder,
                                        Compressor, ErrorCollector, Writer>(
      decomposer, interleaver, encoder, compressor, collector, writer);
  size_t num_elements = 0;
//   auto data = MGARD::readfile<T>(filename.c_str(), num_elements);
  evaluate(data, dims, target_level, num_bitplanes, refactor);
}


std::string filename = "/scratch/aoyagir/step1_500_test.h5";

/*
g++ refactor_test2.cpp -I/usr/include/hdf5/serial -L/usr/lib/x86_64-linux-gnu/hdf5/serial/ -lhdf5 -lzstd -lmgard -lprotobuf
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

    long long unsigned int offset_1 = 1;
    long long unsigned int offset_2 = 1024;
    long long unsigned int offset_3 = 1024;
    long long unsigned int offset_4 = 1024;

    long long int NumElements = offset_1*offset_2*offset_3*offset_4;

    std::vector<float> result2(NumElements);

            // For measuring compression time
    auto start = std::chrono::high_resolution_clock::now();

    std::cout << "slicing and loading the data..." << std::endl;

    dataset.select({start_1,start_2,start_3,start_4},
                    {offset_1, offset_2, offset_3, offset_4}).read(result2.data());

    std::cout << "Load complete!" << std::endl;

    // Stop measuring time
    auto end = std::chrono::high_resolution_clock::now();

    // Calculate the duration in milliseconds
    auto duration = std::chrono::duration_cast<std::chrono::milliseconds>(end - start).count();

    // // Print the execution time
    std::cout << "time taken to load : " << duration << " milliseconds" << std::endl;

    int target_level = 5;

    // これが何なのかわかるようにしてほしい
    int num_bitplanes = 32;


    if (num_bitplanes % 2 == 1) {
        num_bitplanes += 1;
        std::cout << "Change to " << num_bitplanes + 1
                << " bitplanes for simplicity of negabinary encoding"
                << std::endl;
    }

    int num_dims = 3;
    vector<uint32_t> dims(num_dims, 0);
    dims[0] = offset_2;
    dims[1] = offset_3;
    dims[2] = offset_4;

    string metadata_file = "refactored_data/metadata.bin";
    vector<string> files;
    for (int i = 0; i <= target_level; i++) {
        string filename = "refactored_data/level_" + to_string(i) + ".bin";
        files.push_back(filename);
    }
    using T = float;
    using T_stream = uint32_t;
    if (num_bitplanes > 32) {
        num_bitplanes = 32;
        std::cout << "Only less than 32 bitplanes are supported for "
                    "single-precision floating point"
                << std::endl;
    }
    auto decomposer = MDR::MGARDOrthoganalDecomposer<T>();
    // auto decomposer = MDR::MGARDHierarchicalDecomposer<T>();
    auto interleaver = MDR::DirectInterleaver<T>();
    // auto interleaver = MDR::SFCInterleaver<T>();
    // auto interleaver = MDR::BlockedInterleaver<T>();
    auto encoder = MDR::GroupedBPEncoder<T, T_stream>();
    // auto encoder = MDR::NegaBinaryBPEncoder<T, T_stream>();
    // auto encoder = MDR::PerBitBPEncoder<T, T_stream>();
    // auto compressor = MDR::DefaultLevelCompressor();
    auto compressor = MDR::AdaptiveLevelCompressor(32);
    // auto compressor = MDR::NullLevelCompressor();
    auto collector = MDR::SquaredErrorCollector<T>();
    auto writer = MDR::ConcatLevelFileWriter(metadata_file, files);
    // auto writer = MDR::HPSSFileWriter(metadata_file, files, 2048, 512 * 1024 *
    // 1024);

    test<T>(result2, dims, target_level, num_bitplanes, decomposer, interleaver,
            encoder, compressor, collector, writer);

  return 0;
}
