#include "mgard/compress_x_lowlevel.hpp"

#include <iostream>
#include <vector>
int main() {

  mgard_x::SIZE n1 = 200;
  mgard_x::SIZE n2 = 2000;
  mgard_x::SIZE n3 = 3000;
  // prepare
  std::cout << "Preparing data...";
  double *in_array_cpu = new double[n1 * n2 * n3];
  //... load data into in_array_cpu
  std::vector<mgard_x::SIZE> shape{n1, n2, n3};
  mgard_x::Config config;
  config.lossless = mgard_x::lossless_type::Huffman_Zstd;
  mgard_x::Hierarchy<3, double, mgard_x::SERIAL> hierarchy(shape, config);
  mgard_x::Array<3, double, mgard_x::SERIAL> in_array(shape);
  in_array.load(in_array_cpu);
  std::cout << "Done\n";

  std::cout << "Compressing with MGARD-X SERIAL backend..." << std::flush;
  double tol = 0.01, s = 0, norm;
  mgard_x::Compressor compressor(hierarchy, config);
  mgard_x::Array<1, unsigned char, mgard_x::SERIAL> compressed_array;


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
  std::cout << "Done\n";
  std::cout << "exetime:" << (double)duration/1000 << " sec" << std::endl;
  std::cout << "size: " << (double)64*n1*n2*n3/8/1024/1024/1024 << " GBytes" << std::endl;
  std::cout << "Throughput: " << (double)64*n1*n2*n3/8/1024/1024/1024/((double)duration/1000) << "Gbytes/sec" << std::endl;



  std::cout << "Decompressing with MGARD-X SERIAL backend...";
  // decompression
  mgard_x::Array<3, double, mgard_x::SERIAL> decompressed_array;
  compressor.Decompress(compressed_array, mgard_x::error_bound_type::REL, tol,
                        s, norm, decompressed_array, 0);
  mgard_x::DeviceRuntime<mgard_x::SERIAL>::SyncQueue(0);
  delete[] in_array_cpu;
  double *decompressed_array_cpu = decompressed_array.hostCopy();
  std::cout << "Done\n";
}