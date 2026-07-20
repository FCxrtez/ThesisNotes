import numpy as np


def exec_fp16_sum(i1, i2, i3, i4):
    np_float16 = [np.float16(n) for n in [i1, i2, i3, i4]]

    for n in np_float16:
        result += n
    
    fp16_result = np.float16(result)

def exec_fp32_sum(i1, i2, i3, i4):
    np_float32 = [np.float32(n) for n in [i1, i2, i3, i4]]

    for n in np_float32:
        result += n
    
    fp16_result = np.float16(result)

def exec_fp64_sum(i1, i2, i3, i4):
    np_float64 = [np.float64(n) for n in [i1, i2, i3, i4]]

    for n in np_float64:
        result += n
    
    fp16_result = np.float16(result)

def exec_fused_sum(i1, i2, i3, i4, intermediate_dtype=np.float16):
    """
    computes the sum of 4 operands using a parametrized intermediate precision,
    then casts the final result back to FP16.
    """

    operands = np.array([i1, i2, i3, i4], dtype= intermediate_dtype)

    total_sum = np.sum(operands)

    return np.float16(total_sum)