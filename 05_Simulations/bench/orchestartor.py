from pathlib import Path
# from .graphics import graph
import sys
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
ABS_PATH_ERR_DIR    = "/home/fran/tesis/ThesisNotes/05_Simulations/error_logs"


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

def compute_ulp_diff(test_bits, golden_bits, exact_match):
    """
    Vectorized computation of ULP difference between two arrays of FP16 bitstrings
    """
    test_bits_float32   = test_bits  .astype(np.int32)
    golden_bits_float32 = golden_bits.astype(np.int32)

    sign_test       = ( test_bits   >> 15 ) & 0x1
    sign_golden     = ( golden_bits >> 15 ) & 0x1

    # holds exponent and magnitude fields         15 bits
    magnitude_test      = test_bits_float32   & 0x7FFF
    magnitude_golden    = golden_bits_float32 & 0x7FFF

    same_sign   = ( sign_test == sign_golden )
    both_zero   = ( magnitude_test == 0 ) & ( magnitude_golden == 0 )

    difference_same_sign        = magnitude_test - magnitude_golden
    difference_different_sign   = magnitude_test + magnitude_golden
    abs_same_sign               = np.abs(difference_same_sign)

    #                  same_sign ? difference_same_sign : difference_different_sign
    ulp_arr = np.where( same_sign, abs_same_sign,  difference_different_sign )

    ulp_arr_zero        = np.where( both_zero  , 0, ulp_arr      )
    ulp_arr_exact_match = np.where( exact_match, 0, ulp_arr_zero )

    return ulp_arr_exact_match

def main(num_test_vectors=1000, quiet=False):
    out_fn = "bench_result.txt"

    gen_inputs_fun      (    num_test_vectors, verbose = quiet  )
    adder_model         (    ABS_PATH_INP_VEC                   )
    adder_golden_model  (    ABS_PATH_INP_VEC                   )

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

    # Prepare data structures for the analysis
    models  = ['mod', 'f16', 'f32']
    metrics = { m: {} for m in models }

    print("\n\n[INFO] Starting Analysis computations...\n                                                                                                                                                                       ")    

    test_binary  =  {   'mod': mod_binary,  'f16': f16_binary,  'f32': f32_binary }
    test_float   =  {   'mod': mod_float,   'f16': f16_float,   'f32': f32_float  }

    for m in models:
        if m == 'mod':
            golden_is_nan = np.isnan(golden_float)
            model_is_nan  = ( test_binary['mod'] == 0x7E00 ) # our enconding for all NaNs

            exact_match   = (test_binary[m] == golden_binary)
            corrected_exact_match = np.where(golden_is_nan, model_is_nan, exact_match)

            metrics['mod']['exact_match'] = corrected_exact_match
        else:
            metrics[m]['exact_match'] = (test_binary[m] == golden_binary)


        metrics[m]['ulp_error'] = compute_ulp_diff(test_binary[m], golden_binary, metrics[m]['exact_match'])

        with np.errstate(divide='ignore', invalid= 'ignore'):
            standard_rel = np.abs( ( test_float[m] - golden_float ) / golden_float )

        is_golden_zero = ( golden_float  == 0 )
        is_test_zero   = ( test_float[m] == 0 )

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

    test_vectors = np.array(load_vectors(ABS_PATH_INP_VEC))

    mod_exact_match_error_mask = ~ metrics['mod']['exact_match']
    error_data_per_case = {}

    for c in unique_cases:
        case_mask = (c == cases_array)

        case_error_mask = mod_exact_match_error_mask & case_mask
        case_error_index = np.nonzero(case_error_mask)[0]

        if len(case_error_index > 0):

            error_data_per_case[c] = {
                'idx':      case_error_index,
                'inputs':   test_vectors[case_error_index],
                'gt_bin':   golden_binary[case_error_index],
                'mod_bin':  mod_binary[case_error_index],
                'ulp':      metrics['mod']['ulp_error'][case_error_index]
            }

        for case, data in error_data_per_case.items():
            hex_file_path = f"{ABS_PATH_ERR_DIR}/{case}_stimulus.hex"
            log_file_path = f"{ABS_PATH_ERR_DIR}/{case}_debug.log"

            try:
                with open(hex_file_path, 'w+') as f_hex, open(log_file_path, 'w+') as f_log:
                    f_log.write(f"=== DEBUG REPORT: {case.upper()} ===\n\n")

                    # Iterate through the bundled data
                    for i in range(len(data['idx'])):
                        idx    = data['idx'][i]
                        vec    = data['inputs'][i]
                        gt_b   = data['gt_bin'][i]
                        mod_b  = data['mod_bin'][i]
                        ulp    = data['ulp'][i]

                        op_hex_strs = [vec[j:j+4] for j in range(0, 16, 4)]
                        op_floats = [np.uint16(int(h, 16)).view(np.float16) for h in op_hex_strs]

                        float_formatted = f"[{', '.join([f'{f:.4e}' for f in op_floats])}]"
                        gt_f  = np.uint16(gt_b).view(np.float16)
                        mod_f = np.uint16(mod_b).view(np.float16)

                        f_hex.write(f"{vec}\n")

                        f_log.write(f"Vector Index : {idx}\n")
                        f_log.write(f"Inputs (Hex)    : {vec}\n")
                        f_log.write(f"Inputs (Float16): {float_formatted}\n")
                        f_log.write(f"Expected (GT)   : {gt_b:04x}  ({gt_f:.4e})\n")
                        f_log.write(f"Actual (HW)     : {mod_b:04x}  ({mod_f:.4e})\n")
                        f_log.write(f"ULP Error    : {ulp}\n")
                        f_log.write("-" * 40 + "\n")

                print(f"[INFO] Dumped reports for {case}")

            except IOError as e:
                print(f"Error writing files for {case}: {e}")


    # =====================================================================
    # PHASE D: GRAPH GENERATION
    # =====================================================================




if __name__ == "__main__":
    main()