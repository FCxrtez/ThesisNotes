import numpy as np

if __name__ == "__main__":
    
    op_A = float(42592)
    op_B = float(15.993)
    op_C = float(0.007782)
    op_D = float(0.000977)

    res_float16 = np.float16(op_D + np.float16(op_C + np.float16(op_B + op_A)))
    res_float32 = np.float16(np.float32(op_D) + np.float32(op_C + np.float32(op_B + op_A)))
    res_float64 = np.float16(np.float64(op_D) + np.float64(op_C + np.float64(op_B + op_A)))

    print(f"Result in FP16: {res_float16}")
    print(f"Result in FP32: {res_float32}")
    print(f"Result in FP64: {res_float64}")