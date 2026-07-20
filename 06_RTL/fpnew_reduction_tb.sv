`timescale 1ns / 1ps
//////////////////////////////////////////////////////////////////////////////////
// Company: 
// Engineer: 
// 
// Create Date: 06/06/2026 01:21:11 PM
// Design Name: 
// Module Name: fpnew_reduction_tb
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

import tb_pkg::*;

module fpnew_reduction_tb();

  // ---------------------------------------------------------
  // 1. Parameters & Localparams
  // (Adjust these to match your higher hierarchy as needed)
  // ---------------------------------------------------------
  parameter fpnew_pkg::fp_format_e   FpFormat      = fpnew_pkg::fp_format_e'('d2); //FP16
  parameter int unsigned             Width         = 64;
  parameter int unsigned             NumPipeRegs   = 0;
  parameter fpnew_pkg::pipe_config_t PipeConfig    = fpnew_pkg::BEFORE;
  parameter type                     TagType       = logic;
  parameter type                     AuxType       = logic;
  parameter logic                    EnableVectors = 1'b1;

  localparam int unsigned FP_WIDTH       = fpnew_pkg::fp_width(FpFormat);
  localparam int unsigned NUM_LANES      = fpnew_pkg::num_lanes(Width, FpFormat, EnableVectors);
  localparam int unsigned ExtRegEnaWidth = NumPipeRegs == 0 ? 1 : NumPipeRegs;

  // ---------------------------------------------------------
  // 2. Testbench Signals
  // ---------------------------------------------------------
  // Clock and Reset
  logic clk_i;
  logic rst_ni;

  // Stimulus Inputs (Drivers)
  logic [1:0][Width-1:0]     operands_i;
  logic [3:0]                is_boxed_i;
  fpnew_pkg::roundmode_e     rnd_mode_i;
  fpnew_pkg::operation_e     op_i;
  logic                      op_mod_i;
  TagType                    tag_i;
  logic [NUM_LANES-1:0]      mask_i;
  AuxType                    aux_i;
  logic                      in_valid_i;
  logic                      flush_i;
  logic                      out_ready_i;
  logic [ExtRegEnaWidth-1:0] reg_ena_i;

  // Monitored Outputs (Receivers)
  logic                      in_ready_o;
  logic [FP_WIDTH-1:0]       result_o;
  fpnew_pkg::status_t        status_o;
  logic                      extension_bit_o;
  TagType                    tag_o;
  AuxType                    aux_o;
  logic                      out_valid_o;
  logic                      busy_o;
  logic                      early_valid_o;

  // ---------------------------------------------------------
  // 3. DUT Instantiation
  // ---------------------------------------------------------
  fpnew_reduction #(
      .FpFormat      (FpFormat),
      .Width         (Width),
      .NumPipeRegs   (NumPipeRegs),
      .PipeConfig    (PipeConfig),
      .TagType       (TagType),
      .AuxType       (AuxType),
      .EnableVectors (EnableVectors)
  ) dut_reduction (
      .clk_i           (clk_i),
      .rst_ni          (rst_ni),
      .operands_i      (operands_i),
      .is_boxed_i      (is_boxed_i),
      .rnd_mode_i      (rnd_mode_i),
      .op_i            (op_i),
      .op_mod_i        (op_mod_i),
      .tag_i           (tag_i),
      .mask_i          (mask_i),
      .aux_i           (aux_i),
      .in_valid_i      (in_valid_i),
      .in_ready_o      (in_ready_o),
      .flush_i         (flush_i),
      .result_o        (result_o),
      .status_o        (status_o),
      .extension_bit_o (extension_bit_o),
      .tag_o           (tag_o),
      .aux_o           (aux_o),
      .out_valid_o     (out_valid_o),
      .out_ready_i     (out_ready_i),
      .busy_o          (busy_o),
      .reg_ena_i       (reg_ena_i),
      .early_valid_o   (early_valid_o)
  );

  /// ---------------------------------------------------------
  /// Enviroment hanlder
  /// ---------------------------------------------------------

  localparam NUM_TEST_VECTORS = 1;
  TestBenchEnv #(.NUM_TEST_VEC(NUM_TEST_VECTORS)) env;
  
  int curr_tv; // Current test vector counter

  // ---------------------------------------------------------
  // 4. Basic Clock Generation
  // ---------------------------------------------------------
  initial begin : clk_generation
      clk_i = 0;
      // Generates a clock with a period of 10 time units
      forever #5 clk_i = ~clk_i; 
  end

  // ---------------------------------------------------------
  // Object and Signals init
  // ---------------------------------------------------------

  initial begin : signals_driver
      rst_ni              = 0;
      in_valid_i          = 0;
      operands_i          = '0;
      is_boxed_i          = '0;
      rnd_mode_i          = fpnew_pkg::roundmode_e'(0);
      op_i                = fpnew_pkg::operation_e'(0);
      op_mod_i            =  0;
      tag_i               = '0;
      mask_i              = '0;
      aux_i               = '0;
      flush_i             =  0;
      curr_tv             =  0;

      env = new();
      env.load_all_vectors();
      $display("ENV[0] \n\tinput=%b \n\tsigns=%b \n\texponents=%b \n\tmantisas=%b \n\timplicit=%b \n\tshifts=%b \n\tis_max=%b \n\txor_signos=%b \n\taligned=%b \n\tsticky=%b \n\ttwos_comp=%b \n\tsave=%b \n\tcarry=%b \n\tv=%b \n\tlza_F=%b \n\tlza_Gp_p=%b \n\tlza_Gp_n=%b \n\tlza_Gp_z=%b \n\tlza_Gn_p=%b \n\tlza_Gn_n=%b \n\tlza_Gn_z=%b \n\tlza_zero_count=%b \n\tlza_X=%b \n\tlza_Y=%b \n\tmantissa_sum=%b \n\tmantissa_abs=%b \n\tmantissa_normalized=%b \n\tis_sum_negative=%b \n\tfinal_sign=%b \n\tmax_exp=%b \n\tfinal_exp=%b \n\toutput=%b", env.input_vectors.assert_data[0], env.signos_a.assert_data[0], env.exponentes_a.assert_data[0], env.mantisas_a.assert_data[0], env.implicit_mantisas_a.assert_data[0], env.shifts_a.assert_data[0], env.is_max_a.assert_data[0], env.xor_signos_a.assert_data[0], env.aligned_mantisas_a.assert_data[0], env.sticky_bits_a.assert_data[0], env.mantisas_twos_comp_w_ovf_a.assert_data[0], env.save_a.assert_data[0], env.carry_a.assert_data[0], env.v_a.assert_data[0], env.lza_F_a.assert_data[0], env.lza_Gp_p_a.assert_data[0], env.lza_Gp_n_a.assert_data[0], env.lza_Gp_z_a.assert_data[0], env.lza_Gn_p_a.assert_data[0], env.lza_Gn_n_a.assert_data[0], env.lza_Gn_z_a.assert_data[0], env.lza_zero_count_a.assert_data[0], env.lza_X_a.assert_data[0], env.lza_Y_a.assert_data[0], env.mantissa_sum_a.assert_data[0], env.mantissa_abs_a.assert_data[0], env.mantissa_normalized_a.assert_data[0], env.is_sum_negative_a.assert_data[0], env.final_sign_a.assert_data[0], env.max_exp_a.assert_data[0], env.final_exp_a.assert_data[0], env.output_a.assert_data[0]);

      #20;
      rst_ni = 1;
      #10;

      // drive test vectors
      for (int i = 0; i < NUM_TEST_VECTORS; i++) begin : run_test_vectors
          @(posedge clk_i);

          in_valid_i          <= 1;
          operands_i[0]       <= env.input_vectors.assert_data[i];
          is_boxed_i          <= 4'b1111; 
          rnd_mode_i          <= fpnew_pkg::roundmode_e'(0); 
          op_i                <= fpnew_pkg::operation_e'('d16); 
          op_mod_i            <= 0; 
          tag_i               <= i; // Use index as tag for tracking
          mask_i              <= '1; // Enable all lanes for reduction
          aux_i               <= '0; 
          in_valid_i          <= 1;
          curr_tv             <= i;
    
          @(posedge clk_i);
          in_valid_i    <= 0;
      end

      in_valid_i <= 0;
  end

  always @(posedge clk_i) begin : loggin_logic
    if (in_valid_i && in_ready_o) begin
      env.out_log.log_msg("\n\n---------------------------------------------------------------------------------------------------------------");
      env.out_log.log_msg($sformatf("Test Vector Num.%0d: Operands=0x%h, IsBoxed=0b%b, RndMode=%0d, Op=%0d, OpMod=%b, Mask=0b%b, Aux=0x%h",
               tag_i, operands_i, is_boxed_i, rnd_mode_i, op_i, op_mod_i, mask_i, aux_i));
      env.out_log.log_msg("---------------------------------------------------------------------------------------------------------------");
      env.out_log.log_msg("\nInter-module signals:");
      env.out_log.log_msg($sformatf("Unpacked operands:"));
      
      for (int lane = 0; lane < NUM_LANES; lane++) begin
        env.out_log.log_msg($sformatf("Lane %0d:", lane));
        env.out_log.log_msg($sformatf("\t\tSign=%b,", dut_reduction.packed_sign[lane]));
        env.out_log.log_msg($sformatf("\t\tExponent=%b (%0d),", dut_reduction.packed_exp[lane], dut_reduction.packed_exp[lane]));
        env.out_log.log_msg($sformatf("\t\tImplicit mantissa=%b", dut_reduction.packed_implicit_mantissa[lane]));        
        env.out_log.log_msg($sformatf("\t\tis normal: %b\n", dut_reduction.operands_info[lane].is_normal));
      end

      `ASSERT_SIGNAL(env.signos_a,            dut_reduction.packed_sign)
      `ASSERT_SIGNAL(env.exponentes_a,        dut_reduction.packed_exp)
      `ASSERT_SIGNAL(env.implicit_mantisas_a, dut_reduction.packed_implicit_mantissa)

      env.out_log.log_msg($sformatf("Exponent differences and max lane:"));
      env.out_log.log_msg($sformatf("\t\tis_max: [%b]", dut_reduction.i_exp_align.is_max));
      env.out_log.log_msg($sformatf("\t\tshifts:\n\t[%0d, %0d, %0d, %0d]\n", dut_reduction.shifts[0], dut_reduction.shifts[1], dut_reduction.shifts[2], dut_reduction.shifts[3]));

      `ASSERT_SIGNAL(env.shifts_a, dut_reduction.shifts)
      `ASSERT_SIGNAL(env.is_max_a, dut_reduction.i_exp_align.is_max)

      env.out_log.log_msg($sformatf("Mantissa alignment & sticky bits:"));
      for (int lane = 0; lane < NUM_LANES; lane++) begin
          env.out_log.log_msg($sformatf("%0d:\t %b\n\t\tsticky bit:%b\n", lane, dut_reduction.aligned_mantissas[lane], dut_reduction.sticky_before_add[lane]));
      end

      `ASSERT_SIGNAL(env.aligned_mantisas_a, dut_reduction.aligned_mantissas)
      `ASSERT_SIGNAL(env.sticky_bits_a,      dut_reduction.sticky_before_add)

      env.out_log.log_msg($sformatf("\nSign change:"));
      env.out_log.log_msg($sformatf("\t\tanchor sign: %b", dut_reduction.anchor_sign));
      env.out_log.log_msg($sformatf("\t\tmodified signs: [%b]", dut_reduction.inversion_signs));
  
      `ASSERT_SIGNAL(env.xor_signos_a, dut_reduction.inversion_signs)

      env.out_log.log_msg($sformatf("\nSigned mantisas with overflow:"));
      for(int lane = 0; lane<NUM_LANES; lane++) begin
        env.out_log.log_msg($sformatf("%0d:\t %b", lane, dut_reduction.signed_mantissas_w_ovf[lane]));
      end

      `ASSERT_SIGNAL(env.mantisas_twos_comp_w_ovf_a, dut_reduction.signed_mantissas_w_ovf)

      env.out_log.log_msg($sformatf("\nMantissa adition & Leading zero anticipator:"));
      env.out_log.log_msg($sformatf("\tsave: %b", dut_reduction.save));
      env.out_log.log_msg($sformatf("\tcarry: %b", dut_reduction.carry));

      `ASSERT_SIGNAL(env.save_a,  dut_reduction.save)
      `ASSERT_SIGNAL(env.carry_a, dut_reduction.carry)

      if (dut_reduction.V == 1) begin
        env.out_log.log_msg($sformatf("True -> Effective substraction"));
      end else begin
        env.out_log.log_msg($sformatf("False -> Effective Addition"));
      end

      `ASSERT_SIGNAL(env.v_a, dut_reduction.V)
      `ASSERT_SIGNAL(env.lza_F_a, dut_reduction.i_lza.F)

      `ASSERT_SIGNAL(env.lza_Gp_p_a, dut_reduction.i_lza.Gp.p)
      `ASSERT_SIGNAL(env.lza_Gp_n_a, dut_reduction.i_lza.Gp.n)
      `ASSERT_SIGNAL(env.lza_Gp_z_a, dut_reduction.i_lza.Gp.z)

      `ASSERT_SIGNAL(env.lza_Gn_p_a, dut_reduction.i_lza.Gn.p)
      `ASSERT_SIGNAL(env.lza_Gn_n_a, dut_reduction.i_lza.Gn.n)
      `ASSERT_SIGNAL(env.lza_Gn_z_a, dut_reduction.i_lza.Gn.z)
      
      `ASSERT_SIGNAL(env.lza_zero_count_a, dut_reduction.i_lza.lzc_o)
      `ASSERT_SIGNAL(env.lza_Y_a,          dut_reduction.i_lza.Y_o)
      `ASSERT_SIGNAL(env.lza_X_a,          dut_reduction.i_lza.X_o)

      env.out_log.log_msg("LZA signals:");
      env.out_log.log_msg($sformatf("\tF: %b", dut_reduction.i_lza.F));
      env.out_log.log_msg($sformatf("\tzeroes: %b", dut_reduction.i_lza.lzc_o));
      env.out_log.log_msg($sformatf("\tone bit less error: %b", dut_reduction.i_lza.Y_o));
      env.out_log.log_msg($sformatf("\toverflow flag: %b\n", dut_reduction.i_lza.X_o));

      `ASSERT_SIGNAL(env.is_sum_negative_a,     dut_reduction.mantissa_sum[3 * 11 + 2])
      `ASSERT_SIGNAL(env.mantissa_sum_a,        dut_reduction.mantissa_sum)
      `ASSERT_SIGNAL(env.mantissa_abs_a,        dut_reduction.mantissa_abs)

      `ASSERT_SIGNAL(env.mantissa_normalized_a, dut_reduction.mantissa_norm)
      `ASSERT_SIGNAL(env.final_sign_a,          dut_reduction.final_sign)

      env.out_log.log_msg("Mantissa normalization:");
      env.out_log.log_msg($sformatf("\tresult is negative: %b", dut_reduction.mantissa_sum[3 * 11 + 2]));
      env.out_log.log_msg($sformatf("\tfinal sign: %b", dut_reduction.final_sign));
      env.out_log.log_msg($sformatf("\tsigned mantissa: %b", dut_reduction.mantissa_sum));
      env.out_log.log_msg($sformatf("\tabsolute value mantissa: %b", dut_reduction.mantissa_abs));
      
      `ASSERT_SIGNAL(env.max_exp_a,       dut_reduction.max_exp)
      `ASSERT_SIGNAL(env.exp_post_norm_a, dut_reduction.exp_post_norm)
      `ASSERT_SIGNAL(env.enable_flush_a,  dut_reduction.enable_flush)
      
      env.out_log.log_msg("Exponent post-normalization:");
      env.out_log.log_msg($sformatf("\tmax exponent: %b (%d)", dut_reduction.max_exp, dut_reduction.max_exp));
      env.out_log.log_msg($sformatf("\tcorrected lzcounter: %d", dut_reduction.corrected_lzc));
      env.out_log.log_msg($sformatf("\texponent post-normalization: %b (%d)\n", dut_reduction.exp_post_norm, dut_reduction.exp_post_norm));
      env.out_log.log_msg($sformatf("\tFlush to zero signal: %b", dut_reduction.enable_flush));
      env.out_log.log_msg($sformatf("\tnormalized mantissa: %b", dut_reduction.mantissa_norm));

      `ASSERT_SIGNAL(env.abs_rounded_a,  dut_reduction.rounded_mantissa)
      `ASSERT_SIGNAL(env.round_ovf_a,    dut_reduction.round_ovf)
      `ASSERT_SIGNAL(env.rounded_sign_a, dut_reduction.sign_after_round)

      env.out_log.log_msg("Rounding:");
      env.out_log.log_msg($sformatf("\tabs mantissa: %b", dut_reduction.abs_mantissa));
      env.out_log.log_msg($sformatf("\tGround/Sticky bits: %b", dut_reduction.rs_bits));
      env.out_log.log_msg($sformatf("\trounded mantissa: %b (round_ovf: %b)\n", dut_reduction.rounded_mantissa, dut_reduction.round_ovf));
      
      `ASSERT_SIGNAL(env.exact_zero_a,   dut_reduction.exact_zero)
      `ASSERT_SIGNAL(env.final_exp_a,   dut_reduction.final_exp)
      `ASSERT_SIGNAL(env.inf_result_a,   dut_reduction.inf_result)

      env.out_log.log_msg("Post-rounding:");
      env.out_log.log_msg($sformatf("\tsing after round: %b", dut_reduction.sign_after_round));
      env.out_log.log_msg($sformatf("\texact zero signal: %b", dut_reduction.exact_zero));
      env.out_log.log_msg($sformatf("\tfinal exponent: %b", dut_reduction.final_exp));
      env.out_log.log_msg($sformatf("\tresult is Inf: %b", dut_reduction.inf_result));

      `ASSERT_SIGNAL(env.output_a,   dut_reduction.result)

      env.out_log.log_msg("Result packing:");
      env.out_log.log_msg($sformatf("\tsign:     %b", dut_reduction.sign_after_round));
      env.out_log.log_msg($sformatf("\texponent: %b", dut_reduction.final_exp[4:0]));
      env.out_log.log_msg($sformatf("\tmantissa: %b", dut_reduction.rounded_mantissa[9:0]));

    end
  end

endmodule
