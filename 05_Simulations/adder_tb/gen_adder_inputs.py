import os
import random
import numpy as np
import argparse
import struct

FILE_PATH = "/home/fran/tesis/ThesisNotes/05_Simulations/adder_tb"
FILE_NAME_TEST_VEC = "adder_FP16_inputs.txt"
FILE_NAME_CASE_VEC = "adder_FP16_inputs_cases.txt"

def float_to_bits(f):
    """Convierte un número flotante a su representación en bits."""
    return struct.unpack('>H', struct.pack('>e', f))[0]


def fp16_to_hex(f):
    """Convierte un número flotante a su representación hexadecimal de 16 bits."""
    f_b = struct.unpack('>H', struct.pack('>e', f))[0]
    # >e: big-endian _Float16, >H: big-endian unsigned short (16 bits)
    return f"{f_b:04x}"


def gen_file(fn):
    """
    Open a file for writing in FILE_PATH directory with FILE_NAME.
    Returns the file descriptor for writing.
    
    Returns:
        file object: Open file descriptor in write mode
    """
    full_path = os.path.join(FILE_PATH, fn)
    
    return open(full_path, 'w')


def gen_align_stress_vec(rng, mode):
    if mode == '1l_3s':
        exp_large   = rng.integers(25, 31, size=1, dtype=np.uint16)
        exp_small   = rng.integers(0,  6,  size=3, dtype=np.uint16)
        exps        = np.concatenate((exp_large, exp_small))

    elif mode == '3l_1s':
        exp_large   = rng.integers(25, 31, size=3, dtype=np.uint16)
        exp_small   = rng.integers(0,   6, size=1, dtype=np.uint16)
        exps        = np.concatenate((exp_large, exp_small))

    rng.shuffle(exps)
    signs    = rng.integers(0,    2, size=4, dtype=np.uint16)
    mantisas = rng.integers(0, 1024, size=4, dtype=np.uint16)

    # Generamos numeros de 16 bits para que bits sea un array de 4 elementos de 16 bits
    bits     = (signs << 15) | (exps << 10) | mantisas
    return bits.view(np.uint16)


def gen_catastrophic_cancellation_vec( rng ):
    large_exp = rng.integers(low=25, high=31, dtype=np.uint16)
    small_exp = rng.integers(low=0,  high=6,  dtype=np.uint16)

    large_mantisa  = rng.integers(low=0, high=1024, size=1, dtype=np.uint16)
    small_mantisas = rng.integers(low=0, high=1024, size=2, dtype=np.uint16)

    cancel_signs = np.array([0, 1], dtype=np.uint16)
    rnd_signs    = rng.integers(low=0, high=2, size=2, dtype=np.uint16)

    cancel_operands = (cancel_signs << 15) | (large_exp << 10) | large_mantisa
    rnd_operands    = (rnd_signs << 15) | (small_exp << 10) | small_mantisas

    return np.concatenate([cancel_operands, rnd_operands]).view(np.uint16)


def gen_transition_vec(rng, mode):
    norm_to_subn_limit = 2**-14

    if mode == 'subn_to_norm':
        vals = rng.uniform(0.3, 0.6, size=4)
        float16_operands = np.array(vals * norm_to_subn_limit, dtype=np.float16)

    else:
        c1, c2, c3 = rng.uniform(1.2, 4.0, size = 3)
        c_target = rng.uniform(5.9e-8, 6e-5)

        c4 = c_target - (c1 + c2 + c3)
        float16_operands = np.array([c1, c2, c3, c4], dtype=np.float16)

    return float16_operands.view(np.uint16)


def gen_test_vectors(N: int, seed=1):
    rng = np.random.default_rng(seed=seed)
    test_suite, test_case = [], []

    if ( N <= 10):
        N = N * 10
        print(f"[INFO] Generating {N} cases, must be at least 10")

    rnd_uniform_p                   =     0.4
    aling_stress_p                  =     0.2
    catastrophic_cancellation_p     =     0.2
    subnormal_transitions_p         =     0.2

    for _ in range(N):
        bucket = rng.choice(
                ['uniform', 'align_stress', 'c_cancel', 'transition'],
            p = [rnd_uniform_p, aling_stress_p, catastrophic_cancellation_p, subnormal_transitions_p]
        )

        match bucket:
            case 'uniform':
                vec = rng.integers(low=0, high=65536, size=4, dtype=np.uint16)

            case 'align_stress':
                if( np.random.random() > 0.5 ):
                    mode = '1l_3s'
                    vec  = gen_align_stress_vec( rng, mode )
                else:
                    mode = '3l_1s'
                    vec  = gen_align_stress_vec( rng, mode )
                bucket = bucket + '_' + mode

            case 'c_cancel':
                vec = gen_catastrophic_cancellation_vec( rng )

            case 'transition':
                if( np.random.random() > 0.5 ):
                    mode = 'subn_to_norm'
                    vec  = gen_transition_vec( rng, mode )
                else:
                    mode = 'norm_to_subn'
                    vec  = gen_transition_vec( rng, mode )
                bucket = bucket + '_' + mode

        print(f"Case: {bucket},")
        for i, v in enumerate(vec):
            print(f"\t{i}th elem: {v:04x} ({v.view(np.float16)})")       

        test_suite.append(vec)
        test_case.append(bucket)

    return np.array(test_suite), test_case


def main(N = None):

    parser = argparse.ArgumentParser(description="Generate random inputs for an FP16 adder testbench",
                                     usage="python3 gen_adder_inputs.py [inp0 inp1 inp2 inp3]")
    
    parser.add_argument('inputs', nargs='*', help="...")
    parser.add_argument('--num', type=int, default=100, help="...")
    
    args = parser.parse_args()

    if N is None:
        i_num = args.num
    else:
        i_num = N

    if i_num is None or i_num < 0:
        print("Error: --num must be a positive integer")
        exit(1)
    
    F      = gen_file(FILE_NAME_TEST_VEC)
    F_case = gen_file(FILE_NAME_CASE_VEC)

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
        generated_inp, generated_cases = gen_test_vectors(i_num)

        print(f"Writing {len(generated_inp)} random inputs to file...")

        for inp, case in zip(generated_inp, generated_cases):
            for val in inp:
                F.write(f"{val:04x}")

            F.write("\n")
            F_case.write(case + "\n")

if __name__ == '__main__':
    main()