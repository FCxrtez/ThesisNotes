import os

class SimMonitor:
    def __init__(self, gen_assert):

        self.gen_assert = gen_assert
        self.output_dir = '/home/fran/tesis/ThesisNotes/05_Simulations/adder_tb'
        self.output_file = 'adata_output.txt'

        # Dict: ((signal_name, filename), [data])
        self.a_signal_file_data = {
            ("signos",                   "adata_signos.txt"): [],
            ("exponentes",               "adata_exponentes.txt"): [],
            ("mantisas",                 "adata_mantisas.txt"): [],
            ("implicit_mantisas",        "adata_implicit_mantisas.txt"): [],
            ("shifts",                   "adata_shifts.txt"): [],
            ("is_max",                   "adata_is_max.txt"): [],
            ("xor_signs",                "adata_xor_signs.txt"): [],
            ("aligned_mantisas",         "adata_aligned_mantissas.txt"): [],
            ("sticky_bits",              "adata_sticky_bits.txt"): [],
            ("mantisas_twos_comp_w_ovf", "adata_mantisas_twos_comp_w_ovf.txt"): [],
            ("save",                     "adata_save.txt"): [],
            ("carry",                    "adata_carry.txt"): [],
            ("V",                        "adata_V.txt"): [],
            ("LZA_F",                    "adata_LZA_F.txt"): [],
            ("LZA_Gp_p",                 "adata_LZA_Gp_p.txt"): [],
            ("LZA_Gp_n",                 "adata_LZA_Gp_n.txt"): [],
            ("LZA_Gp_z",                 "adata_LZA_Gp_z.txt"): [],
            ("LZA_Gn_p",                 "adata_LZA_Gn_p.txt"): [],
            ("LZA_Gn_n",                 "adata_LZA_Gn_n.txt"): [],
            ("LZA_Gn_z",                 "adata_LZA_Gn_z.txt"): [],
            ("LZA_zero_count",           "adata_LZA_zero_count.txt"): [],
            ("LZA_X",                    "adata_LZA_X.txt"): [],
            ("LZA_Y",                    "adata_LZA_Y.txt"): [],
            ("mantisa_sum",              "adata_mantisa_sum.txt"): [],
            ("mantisa_abs",              "adata_abs_mantisa.txt"): [],
            ("mantisa_normalized",       "adata_mantisa_normalized.txt"): [],
            ("is_sum_negative",          "adata_is_sum_negative.txt"): [],
            ("final_sign",               "adata_final_sign.txt"): [],
            ("max_exp",                  "adata_max_exp.txt"): [],
            ("exp_post_norm",            "adata_exp_post_norm.txt"): [],
            ("FTZ",                      "adata_FTZ.txt"): [],
            ("inf_result",               "adata_inf_result.txt"): [],
            ("abs_rounded",              "adata_abs_rounded.txt"): [],
            ("round_ovf",                "adata_round_ovf.txt"): [],
            ("rounded_sign",             "adata_rounded_sign.txt"): [],
            ("exact_zero",               "adata_exact_zero.txt"): [],
            ("final_exp",                "adata_final_exp.txt"): [],
            ("output",                   "adata_output.txt"): []
        }



    def record(self, signal, data):
        
        for (signalname, filename) in self.a_signal_file_data.keys():
            if signal == signalname:

                key = (signalname, filename)
                self.a_signal_file_data[key].append(data)

                return
        
    def write_data(self):
        self.assert_data()
        if self.gen_assert:
            for ((_ , filename), data) in self.a_signal_file_data.items():

                filepath = os.path.join(self.output_dir, filename)

                with open(filepath, 'w') as fd:
                    for sim_signal in data:

                        fd.write(f"{sim_signal}\n")

        else: print("INFO: No assertion signals generated\n")

    def assert_data(self):
        
        data_length = len(self.a_signal_file_data[('V', "adata_V.txt")])
        for data in list(self.a_signal_file_data.values()):
            
            assert(data_length == len(data))
