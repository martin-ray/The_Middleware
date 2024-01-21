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
#include <string>



// singularity shell --nv szp7.sif
// nvcc compress_bench2.cpp -lcudart -I/usr/include/hdf5/serial \
-L/usr/lib/x86_64-linux-gnu/hdf5/serial/ -I /usr/local/include/cuSZp/ -lhdf5 -lcuSZp -lcudart -lcudadevrt -lcudart

std::string filename = "/scratch/aoyagir/step128.h5";

using namespace std;

struct Statistics {
    float psnr;
    double max_err;
    double rmse;
};

struct Statistics print_statistics(float *data_ori, const float *data_dec,
                      size_t data_size) {


    Statistics stats;

    //   std::cout << "In print_statistics function" << std::endl;
    float max_val = data_ori[0];
    float min_val = data_ori[0];
    float max_abs = fabs(data_ori[0]);

    //   std::cout << "stat step1" << std::endl;
    for (int i = 0; i < data_size; i++) {
        if (data_ori[i] > max_val)
        max_val = data_ori[i];
        if (data_ori[i] < min_val)
        min_val = data_ori[i];
        if (fabs(data_ori[i]) > max_abs)
        max_abs = fabs(data_ori[i]);
    }

    //   std::cout << "stat step2" << std::endl;
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
    //   cout << "Max value = " << max_val << ", min value = " << min_val << endl;
    //   cout << "Max error = " << max_err << ", pos = " << pos << endl;
    //   cout << "MSE = " << mse << ", PSNR = " << psnr << endl;
    double rmse = sqrt(mse);
    stats.psnr = psnr;
    stats.max_err = max_err;
    stats.rmse = rmse;
    return stats;

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

std::string prefix = "./SDRbench/";

std::vector<std::string> file_paths = {
    "Hurricate_ISABEL/100x500x500/CLOUDf48.bin.f32",
    "Hurricate_ISABEL/100x500x500/PRECIPf48.bin.f32",
    "Hurricate_ISABEL/100x500x500/QCLOUDf48.bin.f32",
    "Hurricate_ISABEL/100x500x500/Vf48.bin.f32",
    "NYX/SDRBENCH-EXASKY-NYX-512x512x512/dark_matter_density.f32",
    "SDRBENCH-SCALE_98x1200x1200/PRES-98x1200x1200.f32",
    "SDRBENCH-SCALE_98x1200x1200/RH-98x1200x1200.f32",
    "SDRBENCH-SCALE_98x1200x1200/QS-98x1200x1200.f32",
    "SDRBENCH-SCALE_98x1200x1200/QR-98x1200x1200.f32",
    "SDRBENCH-SCALE_98x1200x1200/V-98x1200x1200.f32",
    "SDRBENCH-SCALE_98x1200x1200/V-98x1200x1200.f32",
    "JHTDB"
};

std::vector<float> tols = {
    0.000001,0.00001, 0.00005, 0.0001, 0.0005, 0.001, 0.005, 0.01, 0.02, 0.03, 0.05, 0.1,
};

std::vector<long unsigned int> offsetSizes = {
    256,
    323,
    256*2,
    256*4
};

int main(int argc, char *argv[]) {

    // parse command line args

    printf("tol,oriSize,compressedsize,psnr,max_error,rmse,comp_ratio,method,time,data\n");

    for(auto file_path : file_paths){
        for(auto offsetSize : offsetSizes) {
            for(auto tol : tols){

                size_t elements = offsetSize*offsetSize*offsetSize;
                size_t OriginalSize = elements*sizeof(float);
                
                if (file_path == "JHTDB"){

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

                    // Get the size of each dimension
                    auto dimensions = dataspace.getDimensions();

                    std::vector<float> data(elements);

                    // load the data
                    dataset.select({0,0,0,0},
                                    {1,offsetSize,offsetSize,offsetSize}).read(data.data());

                    char errorMode[20] = "REL";

                    float errorBound = tol;

                    // Input data preparation on CPU.
                    float* oriData = NULL;
                    float* decData = NULL;
                    unsigned char* cmpBytes = NULL;
                    size_t nbEle = elements;
                    size_t cmpSize = 0;
                    oriData = data.data();
                    decData = (float*)malloc(nbEle*sizeof(float));
                    cmpBytes = (unsigned char*)malloc(nbEle*sizeof(float));

                    // Generating error bounds.
                    float max_val = oriData[0];
                    float min_val = oriData[0];

                    for(size_t i=0; i<nbEle; i++)
                    {
                        if(oriData[i]>max_val)
                            max_val = oriData[i];
                        else if(oriData[i]<min_val)
                            min_val = oriData[i];
                    }
                    errorBound = errorBound * (max_val - min_val);

                    // warm up
                    for(int i=0;i<3;i++)SZp_compress_hostptr_f32(oriData, cmpBytes, nbEle, &cmpSize, errorBound);

                    // cuSZp compression.
                    auto start = std::chrono::high_resolution_clock::now();
                    SZp_compress_hostptr_f32(oriData, cmpBytes, nbEle, &cmpSize, errorBound);
                    auto end = std::chrono::high_resolution_clock::now();
                    float comptime = std::chrono::duration_cast<std::chrono::milliseconds>(end - start).count();
                    
                    
                    // cuSZp decompression.
                    start = std::chrono::high_resolution_clock::now();
                    SZp_decompress_hostptr_f32(decData, cmpBytes, nbEle, cmpSize, errorBound);
                    end = std::chrono::high_resolution_clock::now();
                    float decomptime = std::chrono::duration_cast<std::chrono::milliseconds>(end - start).count();

                    float total_time = (comptime + decomptime)/1000.0;

                    float comp_ratio = (nbEle*sizeof(float)/1024.0/1024.0)/(cmpSize*sizeof(unsigned char)/1024.0/1024.0);
                    Statistics stats;
                    stats = print_statistics(oriData,decData,elements);

                    // std::cout << "finish print_statistics" << std::endl;
                    //'tol', 'oriSize','compressedsize','psnr','max_error','rmse','comp_ratio','method',"time","data"
                    printf("%f,%d,%d,%f,%f,%f,%f,cuSZp,%f,",tol,OriginalSize,cmpSize,stats.psnr,stats.max_err,stats.rmse,comp_ratio,total_time);
                    std::cout << file_path << std::endl;
                    
                } else {
                    // std::cout << "Non jhtdb" << std::endl;
                    float* oriData = NULL;
                    float* decData = NULL;
                    unsigned char* cmpBytes = NULL;
                    size_t nbEle = 0;
                    size_t cmpSize = 0;
                    float errorBound = tol;
                    std::string oriFilePath = prefix + file_path;
                    char* oriFilePath2 = new char[oriFilePath.length() + 1];
                    strcpy(oriFilePath2, oriFilePath.c_str());


                    int status=0;
                    oriData = readFloatData_Yafan(oriFilePath2, &nbEle, &status);
                    // std::cout << "step1" << std::endl;
                    
                    if (nbEle < elements)continue; // cannot read

                    decData = (float*)malloc(elements*sizeof(float));
                    cmpBytes = (unsigned char*)malloc(elements*sizeof(float));
                    
                    // Generating error bounds.
                    float max_val = oriData[0];
                    float min_val = oriData[0];

                    for(size_t i=0; i<elements; i++)
                    {
                        if(oriData[i]>max_val)
                            max_val = oriData[i];
                        else if(oriData[i]<min_val)
                            min_val = oriData[i];
                    }
                    errorBound = errorBound * (max_val - min_val);
                    // std::cout << "step2" << std::endl;

                    // warm up
                    for(int i=0;i<3;i++)SZp_compress_hostptr_f32(oriData, cmpBytes, elements, &cmpSize, errorBound);

                    // std::cout << "step3" << std::endl;
                    // cuSZp compression
                    auto start = std::chrono::high_resolution_clock::now();
                    SZp_compress_hostptr_f32(oriData, cmpBytes, elements, &cmpSize, errorBound);
                    auto end = std::chrono::high_resolution_clock::now();
                    float comptime = std::chrono::duration_cast<std::chrono::milliseconds>(end - start).count();
                    
                    // std::cout << "step4" << std::endl;
                    // cuSZp decompression.
                    start = std::chrono::high_resolution_clock::now();
                    SZp_decompress_hostptr_f32(decData, cmpBytes, elements, cmpSize, errorBound);
                    end = std::chrono::high_resolution_clock::now();
                    float decomptime = std::chrono::duration_cast<std::chrono::milliseconds>(end - start).count();

                    float total_time = (comptime + decomptime)/1000;


                    // printf("cuSZp finished!\n");
                    float comp_ratio = (elements*sizeof(float)/1024.0/1024.0)/(cmpSize*sizeof(unsigned char)/1024.0/1024.0);
                    // printf("compression ratios: %f\n\n", comp_ratio);
                    // printf("stats:\n");
                    Statistics stats;
                    stats = print_statistics(oriData,decData,elements);
                    // std::cout << "finish print_statistics" << std::endl;
                    //'tol', 'oriSize','compressedsize','psnr','max_error','rmse','comp_ratio','method',"time","data"
                    printf("%lf,%lld,%ld,%f,%f,%f,%f,cuSZp,%f,",tol,OriginalSize,cmpSize,stats.psnr,stats.max_err,stats.rmse,comp_ratio,total_time);
                    std::cout << file_path << std::endl;
                    delete[] oriFilePath2;
                    // delete[] oriData;
                    // delete[] decData;
                }
            }
        }
    }
    return 0;
}