from adder_model import main as adder_model
from adder_golden_model import main as adder_GM
from adder_tb import gen_inputs_fun
import argparse

def gen_inputs(N:int):




def main():
    num_test_vectors = 100
    out_fn = "bench_result.txt"


    gen_inputs_fun(N=num_test_vectors)
    
    

    with open("adder__tn/adder_FP16_inputs.txt", "rw") as f:


if __name__ == "__main__":
    main()