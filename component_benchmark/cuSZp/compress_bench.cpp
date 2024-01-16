#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <string.h>
#include <cuda_runtime.h>
#include <cuSZp/cuSZp_utility.h>
#include <cuSZp/cuSZp_entry_f32.h>
#include <cuSZp/cuSZp_timer.h>

#include <iostream>
#include <vector>
#include <chrono>
#include <highfive/H5File.hpp>


// nvcc compress_bench.cpp -lcudart -I/usr/include/hdf5/serial \
-L/usr/lib/x86_64-linux-gnu/hdf5/serial/ -I /usr/local/include/cuSZp/ -lhdf5 -lcuSZp -lcudart -lcudadevrt -lcudart

std::string filename = "/scratch/aoyagir/step1_2.h5";

using namespace std;

void print_statistics(float *data_ori, const float *data_dec,
                      size_t data_size) {
  double max_val = data_ori[0];
  double min_val = data_ori[0];
  double max_abs = fabs(data_ori[0]);

  for (int i = 0; i < data_size; i++) {
    if (data_ori[i] > max_val)
      max_val = data_ori[i];
    if (data_ori[i] < min_val)
      min_val = data_ori[i];
    if (fabs(data_ori[i]) > max_abs)
      max_abs = fabs(data_ori[i]);
  }

  double max_err = 0;
  int pos = 0;
  double mse = 0;

  for (int i = 0; i < data_size; i++) {
    double err = data_ori[i] - data_dec[i];
    mse += err * err;
    if (fabs(err) > max_err) {
      pos = i;
      max_err = fabs(err);
    }
  }
  mse /= data_size;

  double psnr = 20 * log10((max_val - min_val) / sqrt(mse));
  cout << "Max value = " << max_val << ", min value = " << min_val << endl;
  cout << "Max error = " << max_err << ", pos = " << pos << endl;
  cout << "MSE = " << mse << ", PSNR = " << psnr << endl;

}

  // slicing 
  long long unsigned int start_1 = 0;
  long long unsigned int start_2 = 0;
  long long unsigned int start_3 = 0;
  long long unsigned int start_4 = 0;

  long long unsigned int n1 = 1;
  long long unsigned int n2 = 1024/2;
  long long unsigned int n3 = 1024/2/2/2;
  long long unsigned int n4 = 1024/2/2/2;

  // tolerance 
  float tol = 0.0001;

int main(int argc, char *argv[]) {

    // parse command line args
    if(argc != 6){
        std::cout << "input format error\n ./a.out <time_step> <x> <y> <z> <tol>" << std::endl;
        std::exit(0);
    }

    n1 = std::stoll(argv[1]);
    n2 = std::stoll(argv[2]);
    n3 = std::stoll(argv[3]);
    n4 = std::stoll(argv[4]);
    long long int NumElements = n2*n3*n4;

    tol = std::stof(argv[5]);

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
    std::vector<float> data(NumElements);
    // float *data = (float*)malloc(sizeof(float)*NumElements);

    std::cout << "loading data..." << std::endl;
    dataset.select({start_1,start_2,start_3,start_4},
                    {1,n2,n3,n4}).read(data.data());
    std::cout << start_1 << ","<<start_2 << ","<< start_3 << ","<<start_4 << ","<<n1 << ","<<n2 << ","<<n3 << ","<<n4 << std::endl;

    // for(int i=0;i<data.size();i++){
    //   std::cout << data[i] << std::endl;
    // }
    

    std::cout << "done loading" << std::endl;
    char errorMode[20] = "REL";
    // printf("cuSZp_gpu_f32_api testfloat_8_8_128.dat REL 1e-3     # compress dataset with relative 1E-3 error bound\n");

    float errorBound = tol;

    // For measuring the end-to-end throughput.
    TimingGPU timer_GPU;

    // Input data preparation on CPU.
    float* oriData = NULL;
    float* decData = NULL;
    unsigned char* cmpBytes = NULL;
    size_t nbEle = 0;
    size_t cmpSize = 0;

    std::cout << "step0" << std::endl;

    oriData = data.data();//readFloatData_Yafan(oriFilePath, &nbEle, &status);
    std::cout << oriData << std::endl;
    nbEle = NumElements;
    std::cout << "num of elements = " << nbEle << std::endl;
    decData = (float*)malloc(nbEle*sizeof(float));
    cmpBytes = (unsigned char*)malloc(nbEle*sizeof(float));

    std::cout << "step 0.5" << std::endl;


    // Generating error bounds.
    if(strcmp(errorMode, "REL")==0) {
        std::cout << "here" << std::endl;
        float max_val = oriData[0];
        float min_val = oriData[0];
        for(size_t i=0; i<nbEle; i++) {
            if(oriData[i]>max_val)
                max_val = oriData[i];
            else if(oriData[i]<min_val)
                min_val = oriData[i];
        }
        errorBound = errorBound * (max_val - min_val);
        std::cout << max_val << min_val << std::endl;
    }

    std::cout << "step1" << std::endl;


    // Input data preparation on GPU.
    float* d_oriData;
    float* d_decData;
    unsigned char* d_cmpBytes;
    size_t pad_nbEle = (nbEle + 262144 - 1) / 262144 * 262144; // A temp demo, will add more block sizes in future implementation.
    cudaMalloc((void**)&d_oriData, sizeof(float)*pad_nbEle);
    cudaMemcpy(d_oriData, oriData, sizeof(float)*pad_nbEle, cudaMemcpyHostToDevice);
    cudaMalloc((void**)&d_decData, sizeof(float)*pad_nbEle);
    cudaMemset(d_decData, 0, sizeof(float)*pad_nbEle);
    cudaMalloc((void**)&d_cmpBytes, sizeof(float)*pad_nbEle);

    std::cout << "step2" << std::endl;

    // Initializing CUDA Stream.
    cudaStream_t stream;
    cudaStreamCreate(&stream);

    std::cout << "step3" << std::endl;


    // Just a warmup.
    for(int i=0; i<3; i++)
        SZp_compress_deviceptr_f32(d_oriData, d_cmpBytes, nbEle, &cmpSize, errorBound, stream);

    // cuSZp compression.
    auto start = std::chrono::high_resolution_clock::now();
    timer_GPU.StartCounter(); // set timer
    SZp_compress_deviceptr_f32(d_oriData, d_cmpBytes, nbEle, &cmpSize, errorBound, stream);
    auto end = std::chrono::high_resolution_clock::now();
    float comptime = std::chrono::duration_cast<std::chrono::milliseconds>(end - start).count();
    float cmpTime = timer_GPU.GetCounter();

    std::cout << "step4" << std::endl;

    // cuSZp decompression.
    timer_GPU.StartCounter(); // set timer
    start = std::chrono::high_resolution_clock::now();
    SZp_decompress_deviceptr_f32(d_decData, d_cmpBytes, nbEle, cmpSize, errorBound, stream);
    end = std::chrono::high_resolution_clock::now();
    float decomptime = std::chrono::duration_cast<std::chrono::milliseconds>(end - start).count();
    float decTime = timer_GPU.GetCounter();

    // Print result.
    printf("cuSZp finished!\n");
    printf("cuSZp compression   end-to-end speed: %f GB/s\n", (nbEle*sizeof(float)/1024.0/1024.0/1024)/((float)comptime/1000));
    printf("cuSZp decompression end-to-end speed: %f GB/s\n", (nbEle*sizeof(float)/1024.0/1024.0/1024)/((float)decomptime/1000));
    printf("Comptime: %f sec. Decomptiime: %f sec. Total: %f\n",comptime/1000,decomptime/1000,comptime/1000 + decomptime/1000);
    printf("cuSZp compression ratio: %f\n\n", (nbEle*sizeof(float)/1024.0/1024.0)/(cmpSize*sizeof(unsigned char)/1024.0/1024.0));

    // Error check
    cudaMemcpy(cmpBytes, d_cmpBytes, cmpSize*sizeof(unsigned char), cudaMemcpyDeviceToHost);
    cudaMemcpy(decData, d_decData, sizeof(float)*nbEle, cudaMemcpyDeviceToHost);
    int not_bound = 0;
    for(size_t i=0; i<nbEle; i+=1)
    {
        if(abs(oriData[i]-decData[i]) > errorBound*1.1)
        {
            not_bound++;
            // printf("not bound: %zu oriData: %f, decData: %f, errors: %f, bound: %f\n", i, oriData[i], decData[i], abs(oriData[i]-decData[i]), errBound);
        }
    }
    if(!not_bound) printf("\033[0;32mPass error check!\033[0m\n");
    else printf("\033[0;31mFail error check!\033[0m\n");
    
    print_statistics(oriData,decData,nbEle);
    
    // Free allocated data.
    std::cout << "step10" << std::endl;
    free(oriData);
    std::cout << "step11" << std::endl;
    free(decData);
    std::cout << "step12" << std::endl;
    free(cmpBytes);
    std::cout << "step13" << std::endl;
    cudaFree(d_oriData);
    std::cout << "step14" << std::endl;
    cudaFree(d_decData);
    std::cout << "step15" << std::endl;
    cudaFree(d_cmpBytes);
    std::cout << "step16" << std::endl;
    cudaStreamDestroy(stream);
    std::cout << "step17" << std::endl;

    
    return 0;
}