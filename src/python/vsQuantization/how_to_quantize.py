import numpy as np

# Define a 32-bit float
float32_variable = 3.14159265  # Replace with your value

# Convert to a 16-bit float (half-precision)
float16_variable = np.float16(float32_variable)

# Convert to an 8-bit float
# Note: This conversion is more aggressive and will result in significant data loss
float8_variable = np.float16(float32_variable * 255.0 / 127.0)

# Print the results
print("32-bit float:", float32_variable)
print("16-bit float:", float16_variable)
print("8-bit float:", float8_variable)
