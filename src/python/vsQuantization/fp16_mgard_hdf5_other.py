import h5py 
import numpy as np
import _mgard as mgard
import time
import math
import numpy as np

def psnr(original_data, decompressed_data):
    """
    Calculate Peak Signal-to-Noise Ratio (PSNR) between two 3D arrays with dynamic maximum value determination.

    Args:
        original_data (numpy.ndarray): The original data as a 3D numpy array (float).
        decompressed_data (numpy.ndarray): The decompressed data as a 3D numpy array (float).

    Returns:
        float: The PSNR value.
    """
    # Ensure the input arrays have the same shape
    if original_data.shape != decompressed_data.shape:
        raise ValueError("Input arrays must have the same shape")

    # Calculate the mean squared error (MSE) between the two arrays
    mse = np.mean((original_data - decompressed_data) ** 2)

    # Calculate the dynamic maximum possible value based on the maximum value in the input arrays
    max_possible_value = np.max([np.max(original_data), np.max(decompressed_data)])

    # Calculate the PSNR using the formula: PSNR = 20 * log10(max_possible_value / sqrt(MSE))
    psnr_value = 20 * np.log10(max_possible_value / np.sqrt(mse))

    return psnr_value

def maxError(original_data,decompressed_data):
    if original_data.shape != decompressed_data.shape:
        raise ValueError("Input arrays must have the same shape")
    max_error = abs(np.max(original_data - decompressed_data))
    return max_error

def rmse(original_data,decompressed_data):
    return np.sqrt(np.mean((original_data - decompressed_data) ** 2))



class Slicer:

    # default 引数
    def __init__(self,filename="/scratch/aoyagir/step1_500_test.h5") -> None:
        self.filename = filename
        self.file = h5py.File(filename, 'r')
        self.dataset = self.file['data']
        print(self.dataset.shape)

    # Access specific elements in the concatenated array
    def access_array_element(self,timestep, x, y, z):
        element = self.dataset[timestep, x, y, z]
        return element

    # Access a subset of the concatenated array
    def slice_multiple_step(self, file, timestep_start, timestep_end, x_start, x_end, y_start, y_end, z_start, z_end):
        subset = self.dataset[timestep_start:timestep_end, x_start:x_end, y_start:y_end, z_start:z_end]
        return subset
    
    # slice siingle step
    def slice_single_step(self, timestep,  x_start, x_end, y_start, y_end, z_start, z_end):
        subset = self.dataset[timestep,  x_start:x_end, y_start:y_end, z_start:z_end]
        retsubset = np.squeeze(subset)
        return retsubset

    # slice sigle step by size
    def get_xyz_offset_by_size(self, size):
        # 100MB -> 「100/(sizeof(float))」個のデータ
        sizeFloat = 4 # byte
        return int((size/sizeFloat)**(1/3))


### main
# どこまでスケールさせるかだけど、64MiB, 512MiB, 1024MiB, の3つを、二つのデータに対してやればいい。今回の、jhtdbね。
# あと、データの違いによるPSNRの違いだけど、これは64MiBに対して、何個かやればいい。って感じにしようか。
# あとは、
slicer = Slicer("/scratch/aoyagir/step128.h5")
prefix = "./SDRbench/"
file_paths = [
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
        ]

data2dims = {

    "Hurricate_ISABEL/100x500x500/CLOUDf48.bin.f32":[100,500,500],
    "Hurricate_ISABEL/100x500x500/PRECIPf48.bin.f32":[100,500,500],
    "Hurricate_ISABEL/100x500x500/QCLOUDf48.bin.f32":[100,500,500],
    "Hurricate_ISABEL/100x500x500/Vf48.bin.f32":[100,500,500],
    "NYX/SDRBENCH-EXASKY-NYX-512x512x512/dark_matter_density.f32":[512,512,512],
    "SDRBENCH-SCALE_98x1200x1200/PRES-98x1200x1200.f32":[98,1200,1200],
    "SDRBENCH-SCALE_98x1200x1200/RH-98x1200x1200.f32":[98,1200,1200],
    "SDRBENCH-SCALE_98x1200x1200/QS-98x1200x1200.f32":[98,1200,1200],
    "SDRBENCH-SCALE_98x1200x1200/QR-98x1200x1200.f32":[98,1200,1200],
    "SDRBENCH-SCALE_98x1200x1200/V-98x1200x1200.f32":[98,1200,1200],
    "SDRBENCH-SCALE_98x1200x1200/V-98x1200x1200.f32":[98,1200,1200],
    "JHTDB": None
}

# create a file to write the results
import csv
from datetime import datetime

# Get the current date and time
current_time = datetime.now()

# Format the current date and time as a string
timestamp = current_time.strftime("%Y%m%d_%H%M%S")
timestep = 0
# Create the file name based on the timestamp
csv_file = f'bench_{timestamp}_timestep_{timestep}_psrn_by_tol.csv'
header = ['tol', 'oriSize','compressedsize','psnr','max_error','rmse','comp_ratio','method',"time","data"]

with open(csv_file, "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(header)


# Define the number of repetitions and initialize a list for results

tols = [0.00001, 0.00005, 0.0001, 0.0005, 0.001, 0.005, 0.01, 0.02, 0.03, 0.05, 0.1, 0.5, 1]
offsets = [256,323,256*2,256*4] # 323は、128MiBを作り出します！！いいね！
# get the offset size

for file_path in file_paths:

    for offset in offsets:
        
        elements = offset**3
        OriginalSize = offset**3*4

        original = None

        if file_path == "JHTDB":
            original = slicer.slice_single_step(timestep, 0, offset, 0, offset, 0, offset)
        else:
            with open(prefix + file_path, "rb") as file:
                original = np.fromfile(file, dtype=np.float32)
                dims = data2dims[file_path]
                original = original.reshape(dims[0],dims[1],dims[2])
                x_offset = dims[0]
                y_mutl_z_offset = int(elements/x_offset)
                y_z_offset = int(math.sqrt(y_mutl_z_offset))
                if y_z_offset > dims[1] :
                    continue
                else:
                    original = original[0:x_offset,0:y_z_offset,0:y_z_offset]
            
        configGPU = mgard.Config()
        configGPU.dev_type = mgard.DeviceType.CUDA

        # warm up 
        for _ in range(3):
            compressed = mgard.compress(original, 0.1, 0, mgard.ErrorBoundType.REL, configGPU)
        # Wrap your outer loop with tqdm to create a progress bar

        for tol in tols: 
            if tol == 0:
                print("passed")
                continue
            print(tol)

            flag = False

            # Your code here
            load_exe_times = []  # List to store execution times for each repetition
            comp_exe_times = []
            decomp_exe_times = []
            comp_data_size = None


            try:
                start_tiime = time.time()
                compressed = mgard.compress(original, tol, 0, mgard.ErrorBoundType.REL, configGPU)
                end_time = time.time()
                compression_time = end_time - start_tiime
                compressedSize = compressed.nbytes
                
                start_decomp_time = time.time()
                decompressed = mgard.decompress(compressed, configGPU)
                end_decomp_time = time.time()
                decompression_time = end_decomp_time - start_decomp_time

                ratio = original.nbytes/compressedSize

                p = psnr(original,decompressed)
                maxE = maxError(original,decompressed)
                Rmse = rmse(original,decompressed)

                # ['tol', 'oriSize','compressedsize','psnr','comp_ratio','is_quantimized',"time"]
                row_data = [tol,OriginalSize ,compressedSize, p,maxE,Rmse,ratio,"MGARD",compression_time + decompression_time,file_path]

                # Write the data row
                with open(csv_file, "a", newline="") as f:
                    writer = csv.writer(f)
                    writer.writerow(row_data)



                # quantimization
                start_tiime = time.time()
                quantimized = np.float16(original)
                end_time = time.time()
                time_for_quantimizing = end_time - start_tiime
                
                quantimizedSize = quantimized.nbytes
                ratio = original.nbytes/quantimizedSize
                p = psnr(original,quantimized)
                maxE = maxError(original,quantimized)
                Rmse = rmse(original,quantimized)
                row_data = [0,OriginalSize,quantimizedSize,p,maxE,Rmse,ratio,"numpy",time_for_quantimizing,file_path]
                with open(csv_file, "a", newline="") as f:
                    writer = csv.writer(f)
                    writer.writerow(row_data)
                flag = True
            except Exception as e:
                print(e)

    