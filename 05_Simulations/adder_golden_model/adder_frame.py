import os

import numpy as np
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from adder_model.pp_functions import float_to_bits, pp_bits

class AdderFrame:
    output_dir = '/home/fran/tesis/ThesisNotes/05_Simulations/adder_tb'

    def __init__(self, fn, intermediate_dtype=np.float16):
        self.output_file = fn
        self.intermediate_dtype = intermediate_dtype
        self.add_results = []

    def exec_fused_sum(self, i1, i2, i3, i4):
        """
        Computes the sum of 4 operands using a parametrized intermediate precision,
        then casts the final result back to FP16.
        """

        # Cast to intermediate precision
        round1 = np.add(i1    , i2, dtype=self.intermediate_dtype)
        round2 = np.add(round1, i3, dtype=self.intermediate_dtype)
        round3 = np.add(round2, i4, dtype=self.intermediate_dtype)

        # Cast back to original dtype, "packing" of result 
        packed_result = np.float16(round3)

        self.add_results.append(packed_result)

    def write_to_file(self):
        """
        Writes the expected results to a file.
        Each line contains the results of a test vector.
        """
        filepath = os.path.join(self.output_dir, self.output_file)

        with open(filepath, 'w') as f:
            for result in self.add_results:
                print(f"Writing {result} to file...")
                f.write(f"{pp_bits(float_to_bits(result), 16)}\n")

        print(f"Expected results written to {self.output_file}")