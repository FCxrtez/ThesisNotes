`timescale 1ns / 1ps
//////////////////////////////////////////////////////////////////////////////////
// Company: 
// Engineer: 
// 
// Create Date: 06/15/2026 01:41:50 PM
// Design Name: 
// Module Name: tb_pkg
// Project Name: 
// Target Devices: 
// Tool Versions: 
// Description: 
// 
// Dependencies: 
// 
// Revision:
// Revision 0.01 - File Created
// Additional Comments:
// 
//////////////////////////////////////////////////////////////////////////////////


package tb_pkg;

// Macro definitions
`define ASSERT_SIGNAL(env_obj, dut_sig) \
    assert(env_obj.assert_data[curr_tv] == dut_sig) \
         env.out_log.log_msg($sformatf("Assertion passed for %s", `"dut_sig`")); \
    else env.out_log.log_msg( \
        $sformatf("Assertion failed for %s at cycle %0d:\n\tExpected: %b\n\tResult:   %b", \
                  `"dut_sig`", curr_tv, env_obj.assert_data[curr_tv], dut_sig) \
    );


// Parent class
class VectorLoad;
    string filename;

    function new (input string fn);
        this.filename = fn;
    endfunction

    virtual function void load_data(); endfunction

    virtual function void run_assertion(input logic sim_data, input int curr_vector); endfunction

endclass

// Subclasses
class VectorLoadBus #(parameter WIDTH = 1, parameter NUM_TEST_VEC = 99) extends VectorLoad;
    
    typedef struct packed {
        logic [WIDTH-1:0] op0;
        logic [WIDTH-1:0] op1;
        logic [WIDTH-1:0] op2;
        logic [WIDTH-1:0] op3;
    } operands_bus;

    operands_bus assert_data [0:NUM_TEST_VEC-1];

    function new(input string fn);
        super.new(fn);
    endfunction

    virtual function void load_data();
        $readmemb(this.filename, assert_data);
    endfunction


endclass

class VectorLoadSignal #(parameter WIDTH = 1, parameter NUM_TEST_VEC = 99) extends VectorLoad;

    logic [WIDTH-1:0] assert_data [0:NUM_TEST_VEC-1];

    function new(input string fn);
        super.new(fn);
    endfunction

    virtual function void load_data();
        $readmemb(this.filename, assert_data);
    endfunction

endclass

// Fd handler - Input/Output


class FdHandler;
    string filename;
    int fd;

    function new(); endfunction

    function void open_file();
        this.fd = $fopen(this.filename, "w");
        assert(this.fd != 0);
    endfunction
endclass

// Class to log messages

class OutputHandler extends FdHandler;
    int fd_time;
    string timestamp;

    function new();
        // Super constructor is called by compiler
        string fn;
        int status;
        
        void'($system("date +%Y-%m-%d_%H-%M > sim_start_time.txt"));
        this.fd_time = $fopen("sim_start_time.txt", "r");

        fd_time_assert: assert (this.fd_time != 0)
        else $warning("could not open sim_start_time.txt");

        status = $fscanf(this.fd_time, "%s", this.timestamp);
        $fclose(this.fd_time);
        void'($system("rm sim_start_time.txt"));
        
        if (status > 0) begin
            fn = $sformatf("tb_results_%s.txt", this.timestamp);
        end else begin
            fn = "tb_results_unkown_time.txt";   
        end 
        
        this.filename = fn;
        this.open_file();

        check_output: assert (this.fd != 0)
        else $fatal(0 ,"FATAL: could not open %s", this.filename);

        $display("INFO: Dumping simulation stats to %s", filename);
    endfunction

    function void log_msg(input string msg);
        
        $fdisplay(this.fd, msg);
        $display(msg);
        
    endfunction
endclass

class InputHandler #(parameter int WIDTH = 16, parameter int NUM_TEST_VEC = 1) extends FdHandler;
    logic [WIDTH-1:0] assert_data [0:NUM_TEST_VEC-1];

    function new(input string fn);
        this.filename = fn;
    endfunction

    virtual function void load_data();
        $readmemh(this.filename, assert_data);
    endfunction
endclass

// Enviroment class - tb assertion handler

class TestBenchEnv #(parameter int NUM_TEST_VEC = 1);
    // Instanciate signals to be asserted
    InputHandler     #(.WIDTH(64), .NUM_TEST_VEC(NUM_TEST_VEC)) input_vectors;
    VectorLoadBus    #(.WIDTH(1),  .NUM_TEST_VEC(NUM_TEST_VEC)) signos_a;
    VectorLoadBus    #(.WIDTH(5),  .NUM_TEST_VEC(NUM_TEST_VEC)) exponentes_a;

    VectorLoadBus    #(.WIDTH(10), .NUM_TEST_VEC(NUM_TEST_VEC)) mantisas_a;
    VectorLoadBus    #(.WIDTH(11), .NUM_TEST_VEC(NUM_TEST_VEC)) implicit_mantisas_a;
    VectorLoadBus    #(.WIDTH(5),  .NUM_TEST_VEC(NUM_TEST_VEC)) shifts_a;

    VectorLoadBus    #(.WIDTH(1),  .NUM_TEST_VEC(NUM_TEST_VEC)) is_max_a;
    VectorLoadBus    #(.WIDTH(1),  .NUM_TEST_VEC(NUM_TEST_VEC)) xor_signos_a;
    VectorLoadBus    #(.WIDTH(33), .NUM_TEST_VEC(NUM_TEST_VEC)) aligned_mantisas_a;

    VectorLoadBus    #(.WIDTH(1),  .NUM_TEST_VEC(NUM_TEST_VEC)) sticky_bits_a;
    VectorLoadBus    #(.WIDTH(36), .NUM_TEST_VEC(NUM_TEST_VEC)) mantisas_twos_comp_w_ovf_a;
    VectorLoadSignal #(.WIDTH(36), .NUM_TEST_VEC(NUM_TEST_VEC)) save_a;

    VectorLoadSignal #(.WIDTH(36), .NUM_TEST_VEC(NUM_TEST_VEC)) carry_a;
    VectorLoadSignal #(.WIDTH(1),  .NUM_TEST_VEC(NUM_TEST_VEC)) v_a;
    VectorLoadSignal #(.WIDTH(35), .NUM_TEST_VEC(NUM_TEST_VEC)) lza_F_a;

    VectorLoadSignal #(.WIDTH(37), .NUM_TEST_VEC(NUM_TEST_VEC)) lza_Gp_p_a;
    VectorLoadSignal #(.WIDTH(37), .NUM_TEST_VEC(NUM_TEST_VEC)) lza_Gp_n_a;
    VectorLoadSignal #(.WIDTH(37), .NUM_TEST_VEC(NUM_TEST_VEC)) lza_Gp_z_a;

    VectorLoadSignal #(.WIDTH(37), .NUM_TEST_VEC(NUM_TEST_VEC)) lza_Gn_p_a;
    VectorLoadSignal #(.WIDTH(37), .NUM_TEST_VEC(NUM_TEST_VEC)) lza_Gn_n_a;
    VectorLoadSignal #(.WIDTH(37), .NUM_TEST_VEC(NUM_TEST_VEC)) lza_Gn_z_a;

    VectorLoadSignal #(.WIDTH(6),  .NUM_TEST_VEC(NUM_TEST_VEC)) lza_zero_count_a;
    VectorLoadSignal #(.WIDTH(1),  .NUM_TEST_VEC(NUM_TEST_VEC)) lza_X_a;
    VectorLoadSignal #(.WIDTH(1),  .NUM_TEST_VEC(NUM_TEST_VEC)) lza_Y_a;

    VectorLoadSignal #(.WIDTH(36), .NUM_TEST_VEC(NUM_TEST_VEC)) mantissa_sum_a;
    VectorLoadSignal #(.WIDTH(36), .NUM_TEST_VEC(NUM_TEST_VEC)) mantissa_abs_a;
    VectorLoadSignal #(.WIDTH(36), .NUM_TEST_VEC(NUM_TEST_VEC)) mantissa_normalized_a;

    VectorLoadSignal #(.WIDTH(1),  .NUM_TEST_VEC(NUM_TEST_VEC)) is_sum_negative_a;
    VectorLoadSignal #(.WIDTH(1),  .NUM_TEST_VEC(NUM_TEST_VEC)) final_sign_a;
    VectorLoadSignal #(.WIDTH(5),  .NUM_TEST_VEC(NUM_TEST_VEC)) max_exp_a;

    VectorLoadSignal #(.WIDTH(6),  .NUM_TEST_VEC(NUM_TEST_VEC)) exp_post_norm_a;
    VectorLoadSignal #(.WIDTH(1),  .NUM_TEST_VEC(NUM_TEST_VEC)) enable_flush_a;
    VectorLoadSignal #(.WIDTH(10), .NUM_TEST_VEC(NUM_TEST_VEC)) abs_rounded_a;
    
    VectorLoadSignal #(.WIDTH(1),  .NUM_TEST_VEC(NUM_TEST_VEC)) round_ovf_a;
    VectorLoadSignal #(.WIDTH(1),  .NUM_TEST_VEC(NUM_TEST_VEC)) rounded_sign_a;
    VectorLoadSignal #(.WIDTH(1),  .NUM_TEST_VEC(NUM_TEST_VEC)) exact_zero_a;
    
    VectorLoadSignal #(.WIDTH(6),  .NUM_TEST_VEC(NUM_TEST_VEC)) final_exp_a;
    VectorLoadSignal #(.WIDTH(1),  .NUM_TEST_VEC(NUM_TEST_VEC)) inf_result_a;
    VectorLoadSignal #(.WIDTH(16), .NUM_TEST_VEC(NUM_TEST_VEC)) output_a;

    OutputHandler out_log;

    function new();
        this.input_vectors       = new("adder_FP16_inputs.txt");
        this.signos_a            = new("adata_signos.txt");
        this.exponentes_a        = new("adata_exponentes.txt");

        this.mantisas_a          = new("adata_mantisas.txt");
        this.implicit_mantisas_a = new("adata_implicit_mantisas.txt");
        this.shifts_a            = new("adata_shifts.txt");

        this.is_max_a            = new("adata_is_max.txt");
        this.xor_signos_a        = new("adata_xor_signs.txt");
        this.aligned_mantisas_a  = new("adata_aligned_mantissas.txt");

        this.sticky_bits_a              = new("adata_sticky_bits.txt");
        this.mantisas_twos_comp_w_ovf_a = new("adata_mantisas_twos_comp_w_ovf.txt");
        this.save_a                     = new("adata_save.txt");

        this.carry_a               = new("adata_carry.txt");
        this.v_a                   = new("adata_V.txt");
        this.lza_F_a               = new("adata_LZA_F.txt");
     
        this.lza_Gp_p_a            = new("adata_LZA_Gp_p.txt");
        this.lza_Gp_n_a            = new("adata_LZA_Gp_n.txt");
        this.lza_Gp_z_a            = new("adata_LZA_Gp_z.txt");
     
        this.lza_Gn_p_a            = new("adata_LZA_Gn_p.txt");
        this.lza_Gn_n_a            = new("adata_LZA_Gn_n.txt");
        this.lza_Gn_z_a            = new("adata_LZA_Gn_z.txt");
     
        this.lza_zero_count_a      = new("adata_LZA_zero_count.txt");
        this.lza_X_a               = new("adata_LZA_X.txt");
        this.lza_Y_a               = new("adata_LZA_Y.txt");

        this.mantissa_sum_a        = new("adata_mantisa_sum.txt");
        this.mantissa_abs_a        = new("adata_abs_mantisa.txt");
        this.mantissa_normalized_a = new("adata_mantisa_normalized.txt");

        this.is_sum_negative_a     = new("adata_is_sum_negative.txt");
        this.final_sign_a          = new("adata_final_sign.txt");
        this.max_exp_a             = new("adata_max_exp.txt");
   
        this.exp_post_norm_a       = new("adata_exp_post_norm.txt");
        this.enable_flush_a        = new("adata_FTZ.txt");
        this.inf_result_a          = new("adata_inf_result.txt");
        
        this.abs_rounded_a         = new("adata_abs_rounded.txt");
        this.round_ovf_a           = new("adata_round_ovf.txt");
        this.rounded_sign_a        = new("adata_rounded_sign.txt");
        
        this.exact_zero_a          = new("adata_exact_zero.txt");
        this.output_a              = new("adata_output.txt");
        this.final_exp_a           = new("adata_final_exp.txt");
        this.out_log               = new();
    endfunction

    function void load_all_vectors();
        this.input_vectors.load_data();
        this.signos_a.load_data();
        this.exponentes_a.load_data();

        this.mantisas_a.load_data();
        this.implicit_mantisas_a.load_data();
        this.shifts_a.load_data();

        this.is_max_a.load_data();
        this.xor_signos_a.load_data();
        this.aligned_mantisas_a.load_data();

        this.sticky_bits_a.load_data();
        this.mantisas_twos_comp_w_ovf_a.load_data();
        this.save_a.load_data();

        this.carry_a.load_data();
        this.v_a.load_data();
        this.lza_F_a.load_data();

        this.lza_Gp_p_a.load_data();
        this.lza_Gp_n_a.load_data();
        this.lza_Gp_z_a.load_data();

        this.lza_Gn_p_a.load_data();
        this.lza_Gn_n_a.load_data();
        this.lza_Gn_z_a.load_data();

        this.lza_zero_count_a.load_data();
        this.lza_X_a.load_data();
        this.lza_Y_a.load_data();

        this.mantissa_sum_a.load_data();
        this.mantissa_abs_a.load_data();
        this.mantissa_normalized_a.load_data();

        this.is_sum_negative_a.load_data();
        this.final_sign_a.load_data();
        this.max_exp_a.load_data();

        this.exp_post_norm_a.load_data();
        this.enable_flush_a.load_data();
        this.inf_result_a.load_data();

        this.abs_rounded_a.load_data();
        this.round_ovf_a.load_data();
        this.rounded_sign_a.load_data();

        this.final_exp_a.load_data();
        this.exact_zero_a.load_data();
        this.output_a.load_data();
    endfunction

endclass

// LZA - Error detection definitions
typedef struct packed {
    logic z;
    logic p;
    logic n;
    logic y;
} Tree_node_t;

function Tree_node_t gen_next_node(input Tree_node_t left, input Tree_node_t right);
    logic nxt_z, nxt_p, nxt_n, nxt_y;
    Tree_node_t next;

    nxt_z  = left.z & right.z;
    nxt_p = (left.z & right.p) | (left.p & right.z);
    nxt_n = left.n | (left.z & right.n);
    nxt_y = left.y | (left.z & right.y) | (left.p & right.n);

    next.z = nxt_z;
    next.p = nxt_p;
    next.n = nxt_n;
    next.y = nxt_y;

    return next;
endfunction

endpackage : tb_pkg
