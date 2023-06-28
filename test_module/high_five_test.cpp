#include <highfive/H5File.hpp>
#include <iostream>

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

        std::cout << std::endl;
    } catch (Exception& e) {
        std::cerr << "Exception caught: " << e.what() << std::endl;
        return 1;
    }

    return 0;
}
