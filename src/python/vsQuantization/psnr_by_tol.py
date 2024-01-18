import h5py 
import numpy as np
import _mgard as mgard
import time
import cupy

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

