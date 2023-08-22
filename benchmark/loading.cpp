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


std::string filename = "/scratch/aoyagir/step1_500_test.h5";

/*
g++ compress_hdf5.cpp -I/usr/include/hdf5/serial -L/usr/lib/x86_64-linux-gnu/hdf5/serial/ -lhdf5 -lzstd -lmgard -lprotobuf
*/


  // slicing 
  long long unsigned int start_1 = 0;
  long long unsigned int start_2 = 0;
  long long unsigned int start_3 = 0;
  long long unsigned int start_4 = 0;

  long long unsigned int n1 = 10;
  long long unsigned int n2 = 1024;
  long long unsigned int n3 = 1024;
  long long unsigned int n4 = 1024;

  long long int NumElements = n1*n2*n3*n4;


int main(int argc, char *argv[]) {

  // parse command line args
  if(argc != 5){
    std::cout << "input format error\n ./a.out <time_step> <x> <y> <z>" << std::endl;
    std::exit(0);
  }

  n1 = std::stoll(argv[1]);
  n2 = std::stoll(argv[2]);
  n3 = std::stoll(argv[3]);
  n4 = std::stoll(argv[4]);
  NumElements = n1*n2*n3*n4;

  // Open the file as read-only
  HighFive::File file(filename, HighFive::File::ReadOnly);

  // Get the dataset named "data"
  HighFive::DataSet dataset = file.getDataSet("data");


  std::cout << "########### dataset info ###############" << std::endl;
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
  std::cout << "Dimensions of whole data: ";
  for (const auto& dim : dimensions) {
      std::cout << dim << " ";
  }

  std::cout << std::endl;

  std::cout << "########### slice info ###############" << std::endl;



  // size of original data(in GiB)
  double original_data = (double)NumElements*sizeof(float)/1024/1024/1024;

  // ここでmallocするのにも時間がかかる。実際は一回確保しておいたメモリスペースを関数に参照わたしして使いまわすのがよさそう
  std::cout << "allocating memory..." << std::endl;
  std::vector<float> data(NumElements);

  // print the slice part
  std::cout << "slicing " << n1 << " " << n2 << " " << n3 << " " << n4 << std::endl;
  std::cout << "sliced data size : " << original_data << "GiB" << std::endl << std::flush;

  // measure load time
  auto start = std::chrono::high_resolution_clock::now();

  // slice the data
  dataset.select({start_1,start_2,start_3,start_4},
                  {n1, n2, n3, n4}).read(data.data());



  // Stop measuring time
  auto end = std::chrono::high_resolution_clock::now();

  // Calculate the duration in milliseconds
  auto duration = std::chrono::duration_cast<std::chrono::milliseconds>(end - start).count();

  // // Print the execution time
  std::cout << "time_to_load " << n1 << " " 
  << n2 << " " << n3 << " " << n4 << " : " 
  << duration << " milliseconds" << std::endl;

  // print throughput
  std::cout << "throughput:\n" << original_data/(duration/1000.0) << " GiB/sec" << std::endl;

  return 0;
}
