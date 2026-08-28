from pathlib import Path
import sys

SIMULATIONS_ROOT = Path(__file__).resolve().parents[1]
if str(SIMULATIONS_ROOT) not in sys.path:
    sys.path.insert(0, str(SIMULATIONS_ROOT))

from adder_model.run_model import adder_model
from adder_golden_model.run_golden_model import adder_golden_model
from adder_tb.gen_adder_inputs import main as gen_inputs_fun

ABS_PATH_INP_DIR    = "/home/fran/tesis/ThesisNotes/05_Simulations/adder_tb"
ABS_PATH_INP_VEC    = "/home/fran/tesis/ThesisNotes/05_Simulations/adder_tb/adder_FP16_inputs.txt"
ABS_PATH_VEC_CASES  = "/home/fran/tesis/ThesisNotes/05_Simulations/adder_tb/adder_FP16_inputs_cases.txt"

ABS_PATH_MOD_OUT    = "/home/fran/tesis/ThesisNotes/05_Simulations/adder_tb/adata_output.txt"
ABS_PATH_F16_OUT    = "/home/fran/tesis/ThesisNotes/05_Simulations/adder_tb/fp16_ref.txt"
ABS_PATH_F32_OUT    = "/home/fran/tesis/ThesisNotes/05_Simulations/adder_tb/fp32_ref.txt"
ABS_PATH_F64_OUT    = "/home/fran/tesis/ThesisNotes/05_Simulations/adder_tb/fp64_ref.txt"

def load_vectors(file_path):
    try:
        with open(file_path, 'r') as f:
            return [line.strip() for line in f.readlines()]
    except FileNotFoundError:
        print(f"Error: File not found - {file_path}")
        raise ValueError(f"File not found: {file_path}")
    except Exception as e:
        print(f"Error reading file {file_path} - {e}")
        raise ValueError(f"Error reading file: {file_path}: {e}")

def main():
    num_test_vectors = 100
    out_fn = "bench_result.txt"

    gen_inputs_fun      (     num_test_vectors   )
    adder_model         (    ABS_PATH_INP_VEC    )
    adder_golden_model  (    ABS_PATH_INP_VEC    )

    mod_results = load_vectors(     ABS_PATH_MOD_OUT    )
    f16_results = load_vectors(     ABS_PATH_F16_OUT    )
    f32_results = load_vectors(     ABS_PATH_F32_OUT    )
    f64_results = load_vectors(     ABS_PATH_F64_OUT    )
    cases       = load_vectors(     ABS_PATH_VEC_CASES  )

    # Compare results
    

if __name__ == "__main__":
    main()