from pathlib import Path
import sys
import matplotlib.pyplot as plt
import numpy as np

SIMULATIONS_ROOT = Path(__file__).resolve().parents[1]
if str(SIMULATIONS_ROOT) not in sys.path:
    sys.path.insert(0, str(SIMULATIONS_ROOT))

from adder_model.run_model import adder_model
from adder_golden_model.run_golden_model import adder_golden_model
from adder_tb.gen_adder_inputs import main as gen_inputs_fun
from adder_model.pp_functions import bits_to_float

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


def str_to_bin_float(str_list):

    bin_list   = np.array([  int(s, base=2)      for s in str_list ], dtype=np.uint16)
    float_list = np.array([  bits_to_float(i)    for i in bin_list ], dtype=np.float16)

    return bin_list, float_list

def compute_ulp_diff(test_bits, golden_bits):
    """
    Vectorized computation of ULP difference between two arrays of FP16 bitstrings
    """

    test_bits_float32   = test_bits  .astype(np.int32)
    golden_bits_float32 = golden_bits.astype(np.int32)

    sign_test       = ( test_bits >> 15 ) & 0x1
    sign_golden     = ( golden_bits >> 15 ) & 0x1

    magnitude_test      = test_bits_float32 & 0x7FFF
    magnitude_golden    = golden_bits_float32 & 0x7FFF

    same_sign   = ( sign_test == sign_golden )
    both_zero   = ( magnitude_test == 0 ) & ( magnitude_golden == 0 )

    difference_same_sign        = np.abs(magnitude_test - magnitude_golden)
    difference_different_sign   =        magnitude_test + magnitude_golden

    #                  same_sign ? difference_same_sign : difference_different_sign
    ulp_arr = np.where( same_sign, difference_same_sign,  difference_different_sign )

    ulp_arr_zero = np.where( both_zero, 0, ulp_arr )

    return ulp_arr_zero

def main(num_test_vectors=1000, quiet=False):
    out_fn = "bench_result.txt"

    gen_inputs_fun      (    num_test_vectors, verbose = quiet    )
    adder_model         (    ABS_PATH_INP_VEC    )
    adder_golden_model  (    ABS_PATH_INP_VEC    )

    mod_str = load_vectors(     ABS_PATH_MOD_OUT    )
    f16_str = load_vectors(     ABS_PATH_F16_OUT    )
    f32_str = load_vectors(     ABS_PATH_F32_OUT    )
    f64_str = load_vectors(     ABS_PATH_F64_OUT    )
    cases   = load_vectors(     ABS_PATH_VEC_CASES  )

    if not (len(mod_str) == len(f16_str) == len(f32_str) == len(f64_str) == len(cases)):
        print(f"Error: Mismatched lengths - mod: {len(mod_str)}, f16: {len(f16_str)}, f32: {len(f32_str)}, f64: {len(f64_str)}, cases: {len(cases)}")
        raise ValueError("All result lists must have the same length.")
    
    mod_binary   , mod_float    = str_to_bin_float(mod_str)
    f16_binary   , f16_float    = str_to_bin_float(f16_str)
    f32_binary   , f32_float    = str_to_bin_float(f32_str)
    golden_binary, golden_float = str_to_bin_float(f64_str)

    x_axis = np.arange(start=0, stop=num_test_vectors, step=1)

    # Prepare data structures for the analysis
    models  = ['mod', 'f16', 'f32']
    metrics = { m: {} for m in models }

    print("\n\n[INFO] Starting Analysis computations...\n                                                                                                                                                                       ")    

    test_binary  =  {   'mod': mod_binary,  'f16': f16_binary,  'f32': f32_binary }
    test_float   =  {   'mod': mod_float,   'f16': f16_float,   'f32': f32_float  }

    for m in models:
        metrics[m]['exact_match'] = (test_binary[m] == golden_binary)

        metrics[m]['ulp_error'] = compute_ulp_diff(test_binary[m], golden_binary)

        with np.errstate(divide='ignore', invalid= 'ignore'):
            standard_rel = np.abs( ( test_float[m] - golden_float ) / golden_float )

        is_golden_zero = golden_float  == 0
        is_test_zero   = test_float[m] == 0

        # If GT=0 and Test=0 -> 0.0
        # If GT=0 and Test!=0 -> inf
        # Otherwise -> standard relative error
        rel_error_arr = np.where(
            is_golden_zero & is_test_zero, 0.0,
            np.where(is_golden_zero, np.inf, standard_rel)
        )
        
        metrics[m]['rel_error'] = rel_error_arr

    # end for model

    # =====================================================================
    # PHASE A: MACRO-LEVEL ANALYSIS (Overall Performance)
    # =====================================================================
    print("\n" + "="*60)
    print(" PHASE A: OVERALL MACRO ANALYSIS (vs FP64 GT)")
    print("="*60)

    for m in models:
        exact_pct = metrics[m]['exact_match'].mean() * 100
        max_ulp   = metrics[m]['ulp_error'].max()
        mean_ulp  = metrics[m]['ulp_error'].mean()
        
        # Calculate mean relative error ignoring infinities
        valid_rel = metrics[m]['rel_error'][metrics[m]['rel_error'] != np.inf]
        mean_rel  = np.nanmean(valid_rel) if len(valid_rel) > 0 else 0.0
        
        print(f"--- Model: {m.upper()} ---")
        print(f"  Exact Match Rate  :   {exact_pct:6.2f}%")
        print(f"  Max ULP Error     :   {max_ulp}")
        print(f"  Average ULP Error :   {mean_ulp:6.4f}")
        print(f"  Avg Rel Error     :   {mean_rel:.2e}")

    # =====================================================================
    # PHASE B: MICRO-LEVEL ANALYSIS (Per-Category Behavior)
    # =====================================================================
    print("\n" + "="*60)
    print(" PHASE B: CATEGORICAL MICRO ANALYSIS")
    print("="*60)

    unique_cases = np.unique(cases)
    cases_array  = np.array(cases, dtype=str)

    for case in unique_cases:
        mask = (cases_array == case)
        count = np.sum(mask)
        
        print(f"\n[{case.upper()}] - {count} vectors")
        
        for m in models:
            case_exact_pct = metrics[m]['exact_match'][mask].mean() * 100
            case_max_ulp   = metrics[m]['ulp_error'][mask].max()
            case_mean_ulp  = metrics[m]['ulp_error'][mask].mean()
            
            valid_rel = metrics[m]['rel_error'][mask]
            valid_rel = valid_rel[valid_rel != np.inf] 
            case_max_rel = valid_rel.max() if len(valid_rel) > 0 else np.nan
            
            print(f"  {m.upper():<3} | Match: {case_exact_pct:>6.2f}% | Max ULP: {case_max_ulp:>4} | Mean ULP: {case_mean_ulp:>6.2f} | Max RelErr: {case_max_rel:.2e}")


    # =====================================================================
    # PHASE C: ERROR ANALYSIS (Per-Category Behavior)
    # =====================================================================
    print("\n" + "="*60)
    print(" PHASE C: CATEGORICAL ERROR ANALYSIS")
    print("="*60)

    mod_exact_match_error_mask = ~ metrics['mod']['exact_match']
    index_error_vectors = np.nonzero(mod_exact_match_error_mask)[0]

    error_vectors_per_case = {}

    for i, c in zip(index_error_vectors, cases_array[index_error_vectors]):
        if c == case:
            if case not in error_vectors_per_case:
                error_vectors_per_case[case] = []
            error_vectors_per_case[case].append(i)



if __name__ == "__main__":
    main()