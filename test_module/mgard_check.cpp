#include <highfive/H5File.hpp>
#include <mgard/mdr.hpp>
#include <iostream>

// g++ mgard_check.cpp -I/usr/include/hdf5/serial -L/usr/lib/x86_64-linux-gnu/hdf5/serial/ -lhdf5 -lzstd -lmgard
using namespace HighFive;

std::string filename = "/home2/aoyagir/isotropic1024coarse/pressure2_hdf5/output_test.h5";

int main() {
    try {
        // Open the file as read-only
        File file(filename, File::ReadOnly);

        // Get the dataset named "data"
        DataSet dataset = file.getDataSet("data");

        // Retrieve the datatype of the dataset
        DataType datatype = dataset.getDataType();
        std::cout << "Datatype: " << datatype.string() << std::endl;

        // Retrieve the dataspace of the dataset
        DataSpace dataspace = dataset.getSpace();

        // Get the number of dimensions of the dataset
        std::size_t numDimensions = dataspace.getNumberDimensions();
        std::cout << "Number of dimensions: " << numDimensions << std::endl;

        // Get the size of each dimension
        auto dimensions = dataspace.getDimensions();
        std::cout << "Dimensions: ";
        for (const auto& dim : dimensions) {
            std::cout << dim << " ";
        }

        // slicing 

        std::vector<std::vector<std::vector<std::vector<std::vector<double>>>>> result;
        long long unsigned int start_1 = 0;
        long long unsigned int start_2 = 0;
        long long unsigned int start_3 = 0;
        long long unsigned int start_4 = 0;
        long long unsigned int start_5 = 0;

        long long unsigned int offset_1 = 1;
        long long unsigned int offset_2 = 100;
        long long unsigned int offset_3 = 100;
        long long unsigned int offset_4 = 100;
        long long unsigned int offset_5 = 1;

        std::vector<long long unsigned> starts = {start_1,start_2,start_3,start_4,start_5};
        std::vector<long long unsigned> offsets = {offset_1, offset_2, offset_3, offset_4, offset_5};


        dataset.select({start_1,start_2,start_3,start_4,start_5},
                       {offset_1, offset_2, offset_3, offset_4, offset_5}).read(result);

        int sizeDim1 = result.size();
        int sizeDim2 = result[0].size();
        int sizeDim3 = result[0][0].size();
        int sizeDim4 = result[0][0][0].size();
        int sizeDim5 = result[0][0][0][0].size();

        std::cout << "t=" << sizeDim1 << "," << "x=" << sizeDim2 
        << ",y=" << sizeDim3 << ",z=" << sizeDim4 << ",scalar=" << sizeDim5 << std::endl;  
    } catch (Exception& e) {
        std::cerr << "Exception caught: " << e.what() << std::endl;
        return 1;
    }

    return 0;
}
