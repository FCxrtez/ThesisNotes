import os
import random
import argparse
import struct

FILE_PATH = "/home/fran/tesis/ThesisNotes/05_Simulations/adder_tb"
FILE_NAME = "adder_FP16_inputs.txt"

def float_to_bits(f):
    """Convierte un número flotante a su representación en bits."""
    return struct.unpack('>H', struct.pack('>e', f))[0]
    # >e: big-endian _Float16, >H: big-endian unsigned short (16 bits)

def fp16_to_hex(f):
    """Convierte un número flotante a su representación hexadecimal de 16 bits."""
    f_b = float_to_bits(f)
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
    inputs = [random.uniform(-65504, 65504) for _ in range(num_inputs)]
    return [fp16_to_hex(inp) for inp in inputs]


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Generate random inputs for an FP16 adder testbench",
                                      usage="python3 gen_adder_inputs.py [inp0 inp1 inp2 inp3]")
    parser.add_argument('inputs', nargs='*', help="Optional list of inputs to write to the file. If not provided, random inputs will be generated.")
    parser.add_argument('--num', type=int, default=100, help="Number of random inputs to generate if no inputs are provided (default: 100)")
    args = parser.parse_args()
    if args.num < 0 or args.num % 4 !=0:
        print("Error: --num must be a positive integer and a multiple of 4")
        exit(1)
    F = gen_file()

    if args.inputs:
        print(f"User provided inputs: {[float(x) for x in args.inputs]}")
        user_inp = list(map(fp16_to_hex, [float(x) for x in args.inputs]))
        print(f"Writing {user_inp} to file...")
        for i in user_inp:
            F.write(f"{i}")

    else:
        gen_inp = gen_inputs(args.num)
        print(f"Writing {len(gen_inp)} random inputs to file...")
        for i, inp in enumerate(gen_inp):
            if (i % 4 == 0) and (i != 0):
                F.write("\n") # 64 bit vectors -> 4 inputs per line
            F.write(f"{inp}")


## test_cases = [
##     [1.0, 2.0, 3.0, 4.0],
##     [-1.0, 0.5, 12.0, -3.14],
##     # ... generate 100+ random/corner cases here ...
## ]
## with open("python_inputs.txt", "w") as f:
##     # Line 1: Tell SystemVerilog how many tests to expect
##     f.write(f"{len(test_cases)}\n")
##   
##     # Remaining lines: Write the concatenated 64-bit hex words
##     for ops in test_cases:
##         h0 = fp16_to_hex(ops[0])
##         h1 = fp16_to_hex(ops[1])
##         h2 = fp16_to_hex(ops[2])
##         h3 = fp16_to_hex(ops[3])
##       
##         # op0 is at the lowest bits [15:0], so it goes last in the string
##         f.write(f"{h3}{h2}{h1}{h0}\n")