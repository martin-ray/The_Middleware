#include "mgard/compress_x_lowlevel.hpp"
#include <iostream>
#include <vector>
#include <chrono>
#include <highfive/H5File.hpp>
#include <iostream>
#include <fstream>


std::string filename = "/scratch/aoyagir/step1_500_test.h5";


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

  mgard_x::SIZE n1 = 1;
  mgard_x::SIZE n2 = 1024/2;
  mgard_x::SIZE n3 = 1024/2/2/2;
  mgard_x::SIZE n4 = 1024/2/2/2;
 
  std::cout << "inpute the slice range" << std::endl;
  std::cin >> n1 >> n2 >> n3 >> n4;

  long long int NumElements = n1*n2*n3*n4;
  std::cout << "numelelments: " << NumElements << std::endl;

  std::vector<float> result2(NumElements);


  std::cout << "loading data..." << std::endl;
  dataset.select({start_1,start_2,start_3,start_4},
                  {n1,n2,n3,n4}).read(result2.data());
  std::cout << "done loading." << std::endl;


  std::cout << "Preparing data...";
  
  std::vector<mgard_x::SIZE> shape{n2, n3, n4};
  mgard_x::Config config;
//   config.lossless = mgard_x::lossless_type::Huffman_LZ4;
  mgard_x::Hierarchy<3, float, mgard_x::OPENMP> hierarchy(shape, config);
  mgard_x::Array<3, float, mgard_x::OPENMP> in_array(shape);
  in_array.load(result2.data());
  std::cout << "Done\n";

  std::cout << "Compressing with MGARD-X OPENMP backend..." << std::flush;
  float tol = 0.000000001, s = 0, norm;
  
  mgard_x::Compressor compressor(hierarchy, config);
  std::cout << "came here1" << std::endl;
  mgard_x::Array<1, unsigned char, mgard_x::OPENMP> compressed_array;
  std::cout << "came here2" << std::endl;


  auto start = std::chrono::high_resolution_clock::now();
  compressor.Compress(in_array, mgard_x::error_bound_type::REL, tol, s, norm,
                      compressed_array, 0);
  std::cout << "came here3" << std::endl;
  auto end = std::chrono::high_resolution_clock::now();

  // get the time and throughput
  auto duration = std::chrono::duration_cast<std::chrono::milliseconds>(end - start).count();


  // Get compressed size in number of bytes.
  size_t compressed_size = compressed_array.shape(0);
  unsigned char *compressed_array_cpu = compressed_array.hostCopy();
  std::cout << "Done\n";
  std::cout << "exetime:" << (float)duration/1000 << " sec" << std::endl;
  std::cout << "size: " << (float)32*n1*n2*n3*n4/8/1024/1024/1024 << " GBytes" << std::endl;
  std::cout << "Throughput: " << (float)32*n1*n2*n3*n4/8/1024/1024/1024/((float)duration/1000) << "Gbytes/sec" << std::endl;

  // Dump the compressed array
  std::ofstream outFile("binary_dump.bin", std::ios::binary);
  if (!outFile.is_open()) {
      std::cerr << "Error opening file for writing!" << std::endl;
      return 1;
  }

  std::cout << "dumping compressed binary..." << std::endl;
  outFile.write(reinterpret_cast<const char*>(compressed_array_cpu), compressed_size);

  mgard_x::DeviceRuntime<mgard_x::OPENMP>::SyncQueue(0);

  std::cout << "Decompressing with MGARD-X OPENMP backend...";
  // decompression
  mgard_x::Array<3, float, mgard_x::OPENMP> decompressed_array;
  compressor.Decompress(compressed_array, mgard_x::error_bound_type::REL, tol,
                        s, norm, decompressed_array, 0);
  mgard_x::DeviceRuntime<mgard_x::OPENMP>::SyncQueue(0);
  float *decompressed_array_cpu = decompressed_array.hostCopy();
  std::cout << "Done\n";
}