import tb_pkg::*;

module fpnew_reduction_tb();

`define ASSERT_SIGNAL(env_obj, dut_sig) \
    assert(env_obj.assert_data[tv] === dut_sig) \
        // env.out_log.log_msg($sformatf("Assertion passed for %s", `"dut_sig`")); \
    else \
    begin \
        env.out_log.log_msg( \
            $sformatf("Assertion failed for %s at cycle %0d:\n\tExpected: %b\n\tResult:   %b", \
                      `"dut_sig`", tv, env_obj.assert_data[tv], dut_sig) \
        ); \
    end

  // ---------------------------------------------------------
  // 1. Parameters & Localparams
  // ---------------------------------------------------------
  parameter fpnew_pkg::fp_format_e   FpFormat         = fpnew_pkg::fp_format_e'('d2)                         ;
  parameter int unsigned             Width            = TB_INPUT_WIDTH                                       ;
  parameter int unsigned             NumPipeRegs      = 0                                                    ;
  parameter fpnew_pkg::pipe_config_t PipeConfig       = fpnew_pkg::BEFORE                                    ;
  parameter type                     TagType          = logic                                                ;
  parameter type                     AuxType          = logic                                                ;
  parameter logic                    EnableVectors    = 1'b1                                                 ;

  localparam int unsigned            FP_WIDTH         = fpnew_pkg::fp_width(FpFormat)                        ;
  localparam int unsigned            NUM_LANES        = fpnew_pkg::num_lanes(Width, FpFormat, EnableVectors) ;
  localparam int unsigned            ExtRegEnaWidth   = (NumPipeRegs == 0) ? 1 : NumPipeRegs                 ;
                     
  parameter int unsigned             NUM_TEST_VECTORS = 10000                                                ; 

  // ---------------------------------------------------------
  // 2. Testbench Signals
  // ---------------------------------------------------------
  logic                                                             clk_i                                    ;
  logic                                                             rst_ni                                   ;
  logic                 [ 1                 : 0 ][ Width - 1 : 0 ]  operands_i                               ;
  logic                 [ 3                 : 0 ]                   is_boxed_i                               ;
  logic                 [ FP_WIDTH      - 1 : 0 ]                   result_o                                 ;
  logic                 [ NUM_LANES     - 1 : 0 ]                   mask_i                                   ;
  logic                 [ExtRegEnaWidth - 1 : 0 ]                   reg_ena_i                                ;
  logic                                                             op_mod_i                                 ;
  logic                                                             in_valid_i                               ;
  logic                                                             flush_i                                  ;
  logic                                                             out_ready_i                              ;
  logic                                                             in_ready_o                               ;
  logic                                                             extension_bit_o                          ;
  logic                                                             out_valid_o                              ;
  logic                                                             busy_o                                   ;
  logic                                                             early_valid_o                            ;
  TagType                                                           tag_i                                    ;
  TagType                                                           tag_o                                    ;
  AuxType                                                           aux_o                                    ;
  AuxType                                                           aux_i                                    ;
  fpnew_pkg::status_t                                               status_o                                 ;
  fpnew_pkg::roundmode_e                                            rnd_mode_i                               ;
  fpnew_pkg::operation_e                                            op_i                                     ;

  int                                                               failed_vectors        = 0                ;
  int                                                               passed_vectors        = 0                ;
  bit                                                               current_vector_failed                    ;

  TestBenchEnv #(.NUM_TEST_VEC(NUM_TEST_VECTORS))                   env                                      ;  

  // ---------------------------------------------------------
  // 3. DUT Instantiation
  // ---------------------------------------------------------
  fpnew_reduction #(
    .FpFormat           ( FpFormat                ),
    .Width              ( Width                   ),
    .NumPipeRegs        ( NumPipeRegs             ),
    .PipeConfig         ( PipeConfig              ),
    .TagType            ( TagType                 ),
    .AuxType            ( AuxType                 ),
    .EnableVectors      ( EnableVectors           ),
    .AlignmentPrecision ( TB_ALIGNMENT_PRECISION  )
  ) dut_reduction (
    .clk_i              ( clk_i                   ),
    .rst_ni             ( rst_ni                  ),
    .operands_i         ( operands_i              ),
    .is_boxed_i         ( is_boxed_i              ),
    .rnd_mode_i         ( rnd_mode_i              ),
    .op_i               ( op_i                    ),
    .op_mod_i           ( op_mod_i                ),
    .tag_i              ( tag_i                   ),
    .mask_i             ( mask_i                  ),
    .aux_i              ( aux_i                   ),
    .in_valid_i         ( in_valid_i              ),
    .in_ready_o         ( in_ready_o              ),
    .flush_i            ( flush_i                 ),
    .result_o           ( result_o                ),
    .status_o           ( status_o                ),
    .extension_bit_o    ( extension_bit_o         ),
    .tag_o              ( tag_o                   ),
    .aux_o              ( aux_o                   ),
    .out_valid_o        ( out_valid_o             ),
    .out_ready_i        ( out_ready_i             ),
    .busy_o             ( busy_o                  ),
    .reg_ena_i          ( reg_ena_i               ),
    .early_valid_o      ( early_valid_o           )
  );

  // Unused clock generator (kept defined for port consistency)
  initial begin
    clk_i = 1'b0;
    forever #5 clk_i = ~clk_i;
  end

  // ---------------------------------------------------------
  // 4. Test Runner & Assertions
  // ---------------------------------------------------------
  initial begin : test_runner
    // Control ties for combinational execution
    rst_ni      = 1'b1;
    in_valid_i  = 1'b1;
    out_ready_i = 1'b1;
    reg_ena_i   = '1;
    flush_i     = 1'b0;

    operands_i  = '0;
    is_boxed_i  = '0;
    rnd_mode_i  = fpnew_pkg::roundmode_e'(0);
    op_i        = fpnew_pkg::operation_e'(0);
    op_mod_i    = 1'b0;
    tag_i       = '0;
    mask_i      = '0;
    aux_i       = '0;

    env = new();
    env.load_all_vectors();

    #10;
    $display("=== STARTING COMBINATIONAL DATAPATH VERIFICATION (%0d VECTORS) ===", NUM_TEST_VECTORS);

    for (int tv = 0; tv < NUM_TEST_VECTORS; tv++) begin
      current_vector_failed = 1'b0;
      
      // 1. Drive inputs
      @(posedge clk_i)                                        ;

      in_valid_i          = 1                                 ;
      operands_i[0]       = env.input_vectors.assert_data[tv] ;
      is_boxed_i          = 4'b1111                           ;
      rnd_mode_i          = fpnew_pkg::roundmode_e'(0)        ; 
      op_i                = fpnew_pkg::operation_e'('d16)     ; 
      op_mod_i            = 0                                 ; 
      tag_i               = tv                                ; // Use index as tag for tracking
      mask_i              = '1                                ; // Enable all lanes for reduction
      aux_i               = '0                                ; 
    
      // 2. Combinational propagation delay
      #10;

      // 3. Run all User-Provided Assertions
      // for (int lane = 0; lane < NUM_LANES; lane++) begin
        // env.out_log.log_msg($sformatf("Lane %0d:", lane));
        // env.out_log.log_msg($sformatf("\t\tSign=%b,", dut_reduction.packed_sign[lane]));
        // env.out_log.log_msg($sformatf("\t\tExponent=%b (%0d),", dut_reduction.packed_exp[lane], dut_reduction.packed_exp[lane]));
        // env.out_log.log_msg($sformatf("\t\tImplicit mantissa=%b", dut_reduction.packed_implicit_mantissa[lane]));        
        // env.out_log.log_msg($sformatf("\t\tis normal: %b\n", dut_reduction.operands_info[lane].is_normal));
      // end

      `ASSERT_SIGNAL(env.signos_a,            dut_reduction.packed_sign)
      `ASSERT_SIGNAL(env.exponentes_a,        dut_reduction.packed_exp)
      `ASSERT_SIGNAL(env.implicit_mantisas_a, dut_reduction.packed_implicit_mantissa)

      // env.out_log.log_msg($sformatf("Exponent differences and max lane:"));
      // env.out_log.log_msg($sformatf("\t\tis_max: [%b]", dut_reduction.i_exp_align.is_max));
      // env.out_log.log_msg($sformatf("\t\tshifts:\n\t[%0d, %0d, %0d, %0d]\n", dut_reduction.shifts[0], dut_reduction.shifts[1], dut_reduction.shifts[2], dut_reduction.shifts[3]));

      `ASSERT_SIGNAL(env.shifts_a, dut_reduction.shifts)
      `ASSERT_SIGNAL(env.is_max_a, dut_reduction.i_exp_align.is_max)

      // env.out_log.log_msg($sformatf("Mantissa alignment & sticky bits:"));
      for (int lane = 0; lane < NUM_LANES; lane++) begin
          // env.out_log.log_msg($sformatf("%0d:\t %b\n\t\tsticky bit:%b\n", lane, dut_reduction.aligned_mantissas[lane], dut_reduction.sticky_before_add[lane]));
      end

      `ASSERT_SIGNAL(env.aligned_mantisas_a, dut_reduction.aligned_mantissas)
      `ASSERT_SIGNAL(env.sticky_bits_a,      dut_reduction.sticky_before_add)

      // env.out_log.log_msg($sformatf("\nSign change:"));
      // env.out_log.log_msg($sformatf("\t\tanchor sign: %b", dut_reduction.anchor_sign));
      // env.out_log.log_msg($sformatf("\t\tmodified signs: [%b]", dut_reduction.inversion_signs));
  
      `ASSERT_SIGNAL(env.xor_signos_a, dut_reduction.inversion_signs)

      // env.out_log.log_msg($sformatf("\nSigned mantisas with overflow:"));
      for(int lane = 0; lane<NUM_LANES; lane++) begin
        // env.out_log.log_msg($sformatf("%0d:\t %b", lane, dut_reduction.signed_mantissas_w_ovf[lane]));
      end

      `ASSERT_SIGNAL(env.mantisas_twos_comp_w_ovf_a, dut_reduction.signed_mantissas_w_ovf)

      // env.out_log.log_msg($sformatf("\nMantissa adition & Leading zero anticipator:"));
      // env.out_log.log_msg($sformatf("\tsave: %b", dut_reduction.save));
      // env.out_log.log_msg($sformatf("\tcarry: %b", dut_reduction.carry));

      `ASSERT_SIGNAL(env.save_a,  dut_reduction.save)
      `ASSERT_SIGNAL(env.carry_a, dut_reduction.carry)

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

      // env.out_log.log_msg("LZA signals:");
      // env.out_log.log_msg($sformatf("\tF: %b", dut_reduction.i_lza.F));
      // env.out_log.log_msg($sformatf("\tzeroes: %b", dut_reduction.i_lza.lzc_o));
      // env.out_log.log_msg($sformatf("\tone bit less error: %b", dut_reduction.i_lza.Y_o));
      // env.out_log.log_msg($sformatf("\toverflow flag: %b\n", dut_reduction.i_lza.X_o));

      `ASSERT_SIGNAL(env.is_sum_negative_a,     dut_reduction.mantissa_sum[dut_reduction.INTERNAL_PRECISION - 1])
      `ASSERT_SIGNAL(env.mantissa_sum_a,        dut_reduction.mantissa_sum)
      `ASSERT_SIGNAL(env.mantissa_abs_a,        dut_reduction.mantissa_abs)

      `ASSERT_SIGNAL(env.mantissa_normalized_a, dut_reduction.mantissa_norm)
      `ASSERT_SIGNAL(env.final_sign_a,          dut_reduction.final_sign)

      // env.out_log.log_msg("Mantissa normalization:");
      // env.out_log.log_msg($sformatf("\tresult is negative: %b", dut_reduction.mantissa_sum[dut_reduction.INTERNAL_PRECISION - 1]));
      // env.out_log.log_msg($sformatf("\tfinal sign: %b", dut_reduction.final_sign));
      // env.out_log.log_msg($sformatf("\tsigned mantissa: %b", dut_reduction.mantissa_sum));
      // env.out_log.log_msg($sformatf("\tabsolute value mantissa: %b", dut_reduction.mantissa_abs));
      
      `ASSERT_SIGNAL(env.max_exp_a,       dut_reduction.max_exp)
      `ASSERT_SIGNAL(env.exp_post_norm_a, dut_reduction.exp_post_norm)
      `ASSERT_SIGNAL(env.enable_flush_a,  dut_reduction.enable_flush)
      
      // env.out_log.log_msg("Exponent post-normalization:");
      // env.out_log.log_msg($sformatf("\tmax exponent: %b (%d)", dut_reduction.max_exp, dut_reduction.max_exp));
      // env.out_log.log_msg($sformatf("\tcorrected lzcounter: %d", dut_reduction.corrected_lzc));
      // env.out_log.log_msg($sformatf("\texponent post-normalization: %b (%d)\n", dut_reduction.exp_post_norm, dut_reduction.exp_post_norm));
      // env.out_log.log_msg($sformatf("\tFlush to zero signal: %b", dut_reduction.enable_flush));
      // env.out_log.log_msg($sformatf("\tnormalized mantissa: %b", dut_reduction.mantissa_norm));

      `ASSERT_SIGNAL(env.abs_rounded_a,  dut_reduction.rounded_mantissa[TB_MAN_BITS-1:0])
      `ASSERT_SIGNAL(env.round_ovf_a,    dut_reduction.round_ovf)
      `ASSERT_SIGNAL(env.rounded_sign_a, dut_reduction.sign_after_round)

      // env.out_log.log_msg("Rounding:");
      // env.out_log.log_msg($sformatf("\tabs mantissa: %b", dut_reduction.abs_mantissa));
      // env.out_log.log_msg($sformatf("\tGround/Sticky bits: %b", dut_reduction.rs_bits));
      // env.out_log.log_msg($sformatf("\trounded mantissa: %b (round_ovf: %b)\n", dut_reduction.rounded_mantissa, dut_reduction.round_ovf));
      
      `ASSERT_SIGNAL(env.exact_zero_a,   dut_reduction.exact_zero)
      `ASSERT_SIGNAL(env.final_exp_a,   dut_reduction.final_exp)
      `ASSERT_SIGNAL(env.inf_result_a,   dut_reduction.inf_result)

      // env.out_log.log_msg("Post-rounding:");
      // env.out_log.log_msg($sformatf("\tsing after round: %b", dut_reduction.sign_after_round));
      // env.out_log.log_msg($sformatf("\texact zero signal: %b", dut_reduction.exact_zero));
      // env.out_log.log_msg($sformatf("\tfinal exponent: %b", dut_reduction.final_exp));
      // env.out_log.log_msg($sformatf("\tresult is Inf: %b", dut_reduction.inf_result));

      `ASSERT_SIGNAL(env.output_a,   dut_reduction.result)
      if (env.output_a.assert_data[tv] !=  dut_reduction.result)
      begin
        current_vector_failed = 1'b1;
      end
        

      // env.out_log.log_msg("Result packing:");
      // env.out_log.log_msg($sformatf("\tsign:     %b", dut_reduction.sign_after_round));
      // env.out_log.log_msg($sformatf("\texponent: %b", dut_reduction.final_exp[TB_EXP_BITS-1:0]));
      // env.out_log.log_msg($sformatf("\tmantissa: %b", dut_reduction.rounded_mantissa[TB_MAN_BITS-1:0]));

      // 4. Track Pass/Fail
      if (current_vector_failed) begin
        failed_vectors++;
      end else begin
        passed_vectors++;
      end
    end

    // ---------------------------------------------------------
    // 5. Verification Summary Report
    // ---------------------------------------------------------
    $display("\n==================================================");
    $display("                SIMULATION SUMMARY                ");
    $display("==================================================");
    $display(" Total Vectors Executed : %0d", NUM_TEST_VECTORS);
    $display(" Passed                 : %0d", passed_vectors);
    $display(" Failed                 : %0d", failed_vectors);
    $display(" Exact Match Rate       : %0f", real'(passed_vectors)/real'(NUM_TEST_VECTORS));
    $display("--------------------------------------------------");
    
    if (failed_vectors == 0) begin
      $display(" STATUS: [ OK ] - All test vectors passed!");
    end else begin
      $display(" STATUS: [ FAILED ] - %0d out of %0d test vectors failed.", 
               failed_vectors, NUM_TEST_VECTORS);
    end
    
    $display("==================================================\n");
    $finish;
  end

endmodule