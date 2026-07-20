import os
import random
import numpy as np
import argparse
import struct

FILE_PATH = "/home/fran/tesis/ThesisNotes/05_Simulations/adder_tb"
FILE_NAME = "adder_FP16_inputs.txt"

def float_to_bits(f):
    """Convierte un número flotante a su representación en bits."""
    return struct.unpack('>H', struct.pack('>e', f))[0]

def fp16_to_hex(f):
    """Convierte un número flotante a su representación hexadecimal de 16 bits."""
    f_b = struct.unpack('>H', struct.pack('>e', f))[0]
    # >e: big-endian _Float16, >H: big-endian unsigned short (16 bits)
    return f"{f_b:04x}"

def gen_file():
    """
    Open a file for writing in FILE_PATH directory with FILE_NAME.
    If the file already exists, print a warning.
    Returns the file descriptor for writing.
    
    Returns:
        file object: Open file descriptor in write mode
    """
    full_path = os.path.join(FILE_PATH, FILE_NAME)
    
    if os.path.exists(full_path):
        print(f"Warning: File '{full_path}' already exists and will be overwritten.")
    
    return open(full_path, 'w')

def gen_inputs(num_inputs=100):
    np.random.seed(2026)
    inputs = np.random.uniform(low=-65504, high=65504, size=num_inputs).astype(np.float16, copy=True)

    bits = inputs.view(dtype=np.uint16)

    hex = [f"{b:04x}" for b in bits]

    return hex

def gen_inputs_uint16(num_inputs=100):
    rng = np.random.default_rng(seed=2026)
    rnd_array = rng.integers(low=0, high=65536, size=num_inputs, dtype=np.uint16)

    #array_as_fp16 = rnd_array.view(dtype=np.float16)

    hex_array = [f"{b:04x}" for b in rnd_array]

    return hex_array


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Generate random inputs for an FP16 adder testbench",
                                      usage="python3 gen_adder_inputs.py [inp0 inp1 inp2 inp3]")
    
    parser.add_argument(
        'inputs',
        nargs='*',
        help="Optional list of inputs to write to the file. If not provided, random inputs will be generated."
    )

    parser.add_argument(
        '--num',
        type=int,
        default=100,
        help="Number of random inputs to generate if no inputs are provided (default: 100)"
    )

    args = parser.parse_args()

    if args.num < 0 or args.num % 4 !=0:
        print("Error: --num must be a positive integer and a multiple of 4")
        exit(1)
    F = gen_file()

    if args.inputs:

        float_inp = [float(x) for x in args.inputs]
        print(f"User provided inputs: {float_inp}")

        np_floats = np.array(float_inp).astype(np.float16)
        np_bits = np_floats.view(dtype=np.uint16)

        hex_inp = [f"{b:04x}" for b in np_bits]
        print(f"Writing {hex_inp} to file...")

        for i, inp in enumerate(hex_inp):
            if (i % 4 == 0) and (i != 0):
                F.write("\n")
            F.write(f"{inp}")
            
    else:
        gen_inp = gen_inputs_uint16(args.num)
        print(f"Writing {len(gen_inp)} random inputs to file...")
        for i, inp in enumerate(gen_inp):
            if (i % 4 == 0) and (i != 0):
                F.write("\n") # 64 bit vectors -> 4 inputs per line
            F.write(f"{inp}")