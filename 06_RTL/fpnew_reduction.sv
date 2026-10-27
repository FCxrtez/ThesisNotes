// `include "common_cells/registers.svh" //en caso de necesitar registro usar macros FFL, etc

module fpnew_reduction #(
  parameter fpnew_pkg::fp_format_e                    FpFormat      = fpnew_pkg::fp_format_e'('d2)                 ,
  parameter int unsigned                              Width         = 64                                           ,
  parameter int unsigned                              NumPipeRegs   = 0                                            ,
  parameter fpnew_pkg::pipe_config_t                  PipeConfig    = fpnew_pkg::BEFORE                            ,
  parameter type                                      TagType       = logic                                        ,
  parameter type                                      AuxType       = logic                                        ,
  parameter logic                                     EnableVectors = 1'b1                                         ,
  parameter int unsigned                              AlignmentPrecision = 3 * (fpnew_pkg::man_bits(FpFormat) + 1) ,
  // Do not change
  localparam int unsigned FP_WIDTH                    = fpnew_pkg::fp_width(FpFormat)                              ,
  localparam int unsigned NUM_OPERANDS                = fpnew_pkg::num_lanes(Width, FpFormat, EnableVectors)       ,
  localparam int unsigned ExtRegEnaWidth              = NumPipeRegs == 0 ? 1 : NumPipeRegs
) (
  input logic                                             clk_i                                                    ,
  input logic                                             rst_ni                                                   ,
  // Input signals
  input logic                   [1 : 0 ][Width  - 1 : 0 ] operands_i                                               , // 2 operands full width
  input logic                   [3 : 0 ]                  is_boxed_i                                               , // 4 operands - donde se define? significado explicado en README.m- Pero tengo 4 operandos por bus, capaz deba implementar mi propio classifier
  input fpnew_pkg::roundmode_e                            rnd_mode_i                                               ,
  input fpnew_pkg::operation_e                            op_i                                                     ,
  input logic                                             op_mod_i                                                 ,
  input TagType                                           tag_i                                                    ,
  input logic                   [NUM_OPERANDS   - 1 : 0 ] mask_i                                                   , // buscar manera de pasar mascara de bits en este campo
  input AuxType                                           aux_i                                                    ,
  // Input Handshake
  input  logic                                            in_valid_i                                               ,
  output logic                                            in_ready_o                                               ,
  input  logic                                            flush_i                                                  ,
  // Output signals
  output logic                  [FP_WIDTH       - 1 : 0 ] result_o                                                 ,
  output fpnew_pkg::status_t                              status_o                                                 ,
  output logic                                            extension_bit_o                                          ,
  output TagType                                          tag_o                                                    ,
  // output logic                                         mask_o                                                   , no es relevante para reduccion pues devolvemos un solo valor/status
  output AuxType                                          aux_o                                                    , // utilizado en fpnew_fma para definir result_is_vector, que luego se utiliza para definir result_o
  // Output handshake 
  output logic                                            out_valid_o                                              ,
  input  logic                                            out_ready_i                                              ,
  // Indication of valid data in flight
  output logic                                            busy_o                                                   ,
  // External register enable override
  input  logic                  [ExtRegEnaWidth - 1 : 0 ] reg_ena_i                                                ,
  output logic                                            early_valid_o
) ;

  // ----------
  // Constants
  // ----------
  localparam int unsigned MAN_BITS            = fpnew_pkg::man_bits(FpFormat)                                                          ;
  localparam int unsigned EXP_BITS            = fpnew_pkg::exp_bits(FpFormat)                                                          ;
  localparam int unsigned BIAS                = fpnew_pkg::bias(FpFormat)                                                              ;
  localparam int unsigned PRECISION_BITS      = MAN_BITS + 1                                                                           ;
  localparam int unsigned STICKY_BITS         = PRECISION_BITS                                                                         ;
  localparam int unsigned SIGN_OVF_BITS       = 3                                                                                      ;
  localparam int unsigned ALIGNMENT_PRECISION = AlignmentPrecision                                                                     ;
  localparam int unsigned INTERNAL_PRECISION  = ALIGNMENT_PRECISION + SIGN_OVF_BITS                                                    ;
  localparam int unsigned ALIGNMENT_WIDTH     = ALIGNMENT_PRECISION + STICKY_BITS                                                      ;
  localparam int unsigned SHIFT_AMOUNT_WIDTH  = $clog2(fpnew_pkg::max_exp_dif(FpFormat))                                               ;
  localparam int unsigned LZC_WIDTH           = $clog2(INTERNAL_PRECISION + 1)                                                         ;
  localparam bit          FTZ_EN               = 1'b0                                                                                  ;

  // ----------
  // Handshake signals
  // ----------
  logic local_in_ready = '1                                                                                                            ; // si agregamos registros de pipeline cambiar la manera de asignar este ready
  assign in_ready_o = 1                                                                                                                ;
  //assign in_ready_o = out_ready_i                                                                                                    ;
  assign tag_o = tag_i                                                                                                                 ;

  // ----------------
  // Type definition
  // ----------------
  typedef struct packed {
    logic                sign                                                                                                          ;
    logic [EXP_BITS-1:0] exponent                                                                                                      ;
    logic [MAN_BITS-1:0] mantissa                                                                                                      ;
  } fp_t                                                                                                                               ;

  // ---------------
  // Input processing
  // ---------------
  fp_t                 [NUM_OPERANDS - 1 : 0 ]                           unpacked_operands                                             ;
  fpnew_pkg::fp_info_t [NUM_OPERANDS - 1 : 0 ]                           operands_info                                                 ;
  logic                [NUM_OPERANDS - 1 : 0 ] [EXP_BITS       - 1 : 0 ] packed_exp                                                    ;
  logic                [NUM_OPERANDS - 1 : 0 ] [PRECISION_BITS - 1 : 0 ] packed_implicit_mantissa                                      ;
  logic                [NUM_OPERANDS - 1 : 0 ]                           packed_sign                                                   ;
  logic                                                                  any_operand_inf                                               ;
  logic                                                                  any_operand_nan                                               ;
  logic                                                                  signalling_nan                                                ;
  logic                                                                  has_pos_inf                                                   ;
  logic                                                                  has_neg_inf                                                   ;

  fpnew_classifier #(
    .FpFormat    (  FpFormat          ),
    .NumOperands (  NUM_OPERANDS      )
  ) i_classifier    (
    .operands_i  (  unpacked_operands ),
    .is_boxed_i  (  is_boxed_i        ),
    .info_o      (  operands_info     )
  )  ;

  always_comb
  begin : unpack_operands
    unpacked_operands         = '0                                                                                                     ;
    packed_exp                = '0                                                                                                     ;
    packed_implicit_mantissa  = '0                                                                                                     ;
    packed_sign               = '0                                                                                                     ;

    if (in_valid_i & local_in_ready)
    begin
      for (int ii = 0 ; ii < int'(NUM_OPERANDS) ; ii++)
      begin
        unpacked_operands[ii]         = fp_t'(operands_i[0][ii*FP_WIDTH +: FP_WIDTH])                                                  ;
        packed_implicit_mantissa[ii]  = {operands_info[ii].is_normal, unpacked_operands[ii].mantissa}                                  ;
        packed_sign[ii]               = unpacked_operands[ii].sign                                                                     ;
        packed_exp[ii]                = (operands_info[ii].is_normal) ? unpacked_operands[ii].exponent
                                                                      : {{EXP_BITS - 1 {1'b0}}, {1'b1}}                                ;
      end
    end
  end

  always_comb
  begin : classification_reduction
    any_operand_inf = 1'b0                                                                                                             ;
    any_operand_nan = 1'b0                                                                                                             ;
    signalling_nan  = 1'b0                                                                                                             ;
    has_neg_inf     = 1'b0                                                                                                             ;
    has_pos_inf     = 1'b0                                                                                                             ;
    
    for (int i = 0 ; i < int'(NUM_OPERANDS) ; i++)
    begin
      any_operand_inf |= operands_info[i].is_inf                                                                                       ;
      any_operand_nan |= operands_info[i].is_nan                                                                                       ;
      signalling_nan  |= operands_info[i].is_signalling                                                                                ;

      has_pos_inf |= ( operands_info[i].is_inf & (~ packed_sign[i]))                                                                   ;
      has_neg_inf |= ( operands_info[i].is_inf &    packed_sign[i] )                                                                   ;
    end
  end

  // ---------------
  // Exponent difference & mantissa alignment
  // ---------------

  logic        [NUM_OPERANDS - 1 : 0] [SHIFT_AMOUNT_WIDTH  - 1 : 0 ] shifts                                                            ;
  logic        [NUM_OPERANDS - 1 : 0] [PRECISION_BITS      - 1 : 0 ] aligned_mantissas_stk_bits                                        ;
  logic        [NUM_OPERANDS - 1 : 0] [ALIGNMENT_PRECISION - 1 : 0 ] aligned_mantissas                                                 ;
  logic        [NUM_OPERANDS - 1 : 0] [INTERNAL_PRECISION  - 1 : 0 ] padded_mantissa                                                   ;
  logic signed [NUM_OPERANDS - 1 : 0] [INTERNAL_PRECISION  - 1 : 0 ] signed_mantissas_w_ovf                                            ;
  logic                               [EXP_BITS             - 1 : 0] max_exp                                                           ;
  logic        [NUM_OPERANDS - 1 : 0]                                sticky_before_add                                                 ;                      
  logic                                                              any_sticky_bit                                                    ;

  fpnew_reduction_exp_align # (
    .EXP_BITS           ( EXP_BITS            ),
    .NUM_OPERANDS       ( NUM_OPERANDS        ),
    .SHIFT_AMOUNT_WIDTH ( SHIFT_AMOUNT_WIDTH  )
  ) i_exp_align               (
    .exponents_i        ( packed_exp          ),
    .shifts_o           ( shifts              ),
    .max_exp_o          ( max_exp             )
  ) ;

  generate
    for (genvar i = 0 ; i < int'(NUM_OPERANDS) ; i++)
    begin : mantissa_alignment
      // Each addend is right-shifted according to the exponent difference. Up to p bits
      // are shifted out and compressed into a sticky bit.
      // BEFORE THE SHIFT:
      // | packed_implicit_mantissa[i] | 000..000 |
      // <-             p            -> <-  3p  ->
      // AFTER THE SHIFT:
      // | 000..........000 | packed_implicit_mantissa[i] | 000...............0GR |  sticky bits  |
      //  <-   shifts[i]  -> <-            p            -> <-   2p -shifts[i]   -> <-      p    ->

      assign {aligned_mantissas[i], aligned_mantissas_stk_bits[i]} = (packed_implicit_mantissa[i] << ALIGNMENT_PRECISION) >> shifts[i] ;

      assign sticky_before_add[i] = | aligned_mantissas_stk_bits[i]                                                                    ;
    end
  endgenerate

  assign any_sticky_bit = | (sticky_before_add)                                                                                        ;

  // ---------------------------------------------
  // Sign change (MSB-side operand as anchor)
  // ---------------------------------------------

  logic [NUM_OPERANDS-1:0] inversion_signs                                                                                             ;
  logic                    anchor_sign                                                                                                 ;
  logic                    final_sign                                                                                                  ;

  assign anchor_sign       = packed_sign[NUM_OPERANDS-1]                                                                               ;

  always_comb 
  begin :sign_inverison
    for (int i = 0 ; i < int'(NUM_OPERANDS) ; i++)
    begin
      inversion_signs[i] = packed_sign[i] ^ anchor_sign                                                                                ;
      padded_mantissa[i] = {{SIGN_OVF_BITS{1'b0}}, aligned_mantissas[i]}                                                               ;

      if (inversion_signs[i])
      begin
        signed_mantissas_w_ovf[i] = signed'(-padded_mantissa[i])                                                                       ;
      end
      else
      begin
        signed_mantissas_w_ovf[i] = signed'(padded_mantissa[i])                                                                        ;
      end
    end
  end

  // ---------------------------------------------
  // Mantissa adition & Leading zero anticipator
  // ---------------------------------------------

  logic                                        V                                                                                       ;
  logic                                        X                                                                                       ;
  logic                                        Y                                                                                       ;
  logic unsigned [LZC_WIDTH          - 1 : 0 ] lzc                                                                                     ;
  logic unsigned [LZC_WIDTH          - 1 : 0 ] corrected_lzc                                                                           ;
  logic          [INTERNAL_PRECISION - 1 : 0 ] save                                                                                    ;
  logic          [INTERNAL_PRECISION - 1 : 0 ] carry                                                                                   ;
  logic   signed [INTERNAL_PRECISION - 1 : 0 ] mantissa_sum                                                                            ;
  logic          [INTERNAL_PRECISION - 1 : 0 ] mantissa_abs                                                                            ;
  logic          [INTERNAL_PRECISION - 1 : 0 ] mantissa_norm                                                                           ;


  assign V = !((& packed_sign) | (~| packed_sign))                                                                                     ;
  
  csa_4to2_tree # (
    .WIDTH        ( INTERNAL_PRECISION        )
  ) i_csa_tree    (
    .operands_i   ( signed_mantissas_w_ovf    ),
    .save_o       ( save                      ),
    .carry_o      ( carry                     )
  ) ;

  fpnew_reduction_LZA # (
    .WIDTH        ( INTERNAL_PRECISION        ),
    .LZC_WIDTH    ( LZC_WIDTH                 )
  ) i_lza               (
    .a_i          ( save                      ),
    .b_i          ( carry                     ),
    .V_i          ( V                         ),
    .X_o          ( X                         ),
    .Y_o          ( Y                         ),
    .lzc_o        ( lzc                       )
  ) ;

  assign mantissa_sum   = save + carry                                                                                                 ;
  assign corrected_lzc  = lzc + Y                                                                                                      ;

  always_comb
  begin : absolute_value
    if(mantissa_sum[ INTERNAL_PRECISION - 1 ])
    begin : negative_result
      mantissa_abs = -mantissa_sum                                                                                                     ;
    end
    else
     begin
      mantissa_abs = mantissa_sum                                                                                                      ;
    end
  end

  assign final_sign = mantissa_sum[ INTERNAL_PRECISION - 1 ] ^ anchor_sign                                                             ;

  // ---------------
  // Mantissa normalization & post normalization exponent
  // ---------------
  logic                                        enable_flush                                                                            ;
  logic                                        inf_result                                                                              ;
  logic          [EXP_BITS           - 1 : 0 ] eff_exp                                                                                 ;
  logic signed   [LZC_WIDTH              : 0 ] tentative_exponent                                                                      ;
  logic          [EXP_BITS +1        - 1 : 0 ] exp_post_norm                                                                           ;
  logic          [EXP_BITS +1        - 1 : 0 ] final_exp                                                                               ;
  logic unsigned [LZC_WIDTH          - 1 : 0 ] shift_amount                                                                            ;

  assign eff_exp            = (max_exp > 0) ? max_exp : {{EXP_BITS - 1{1'b0}}, 1'b1}                                                   ;
  assign tentative_exponent = $signed({1'b0, eff_exp}) + SIGN_OVF_BITS - $signed({1'b0, corrected_lzc})                                ;

  always_comb
  begin : exponent_calculation
    enable_flush = 1'b0                                                                                                                ;

    if (tentative_exponent >= 1 )
    begin : Normal_number
      shift_amount = corrected_lzc                                                                                                     ;
      exp_post_norm = tentative_exponent                                                                                               ;
    end
    else
    begin : Subnormal_number
      exp_post_norm = '0                                                                                                               ;

      if (FTZ_EN)
      begin
        enable_flush = 1'b1                                                                                                            ;
        shift_amount = '0                                                                                                              ;
      end
      else
      begin
        shift_amount = eff_exp + SIGN_OVF_BITS - 1                                                                                     ;
      end
    end
  end

  assign mantissa_norm = enable_flush ? '0 : (mantissa_abs << shift_amount)                                                            ;
  
  // ---------------
  // Rounding
  // ---------------
  logic                         sign_after_round                                                                                       ;
  logic                         exact_zero                                                                                             ;
  logic                         round_ovf                                                                                              ;
  logic [ 1               : 0 ] rs_bits                                                                                                ;
  logic [MAN_BITS     - 1 : 0 ] abs_mantissa                                                                                           ;
  logic [MAN_BITS + 1 - 1 : 0 ] rounded_mantissa                                                                                       ;
  
  assign abs_mantissa =   mantissa_norm[INTERNAL_PRECISION - 2 -: MAN_BITS]                                                            ;
  assign rs_bits      = { mantissa_norm[INTERNAL_PRECISION - 2 - MAN_BITS],
                          (|mantissa_norm[INTERNAL_PRECISION - 3 - MAN_BITS:0]) | any_sticky_bit
                        }                                                                                                              ;
  assign round_ovf    = rounded_mantissa[MAN_BITS]                                                                                     ;

  fpnew_rounding # (
    .AbsWidth                (  MAN_BITS+1          )
  ) i_rounding     (
    .abs_value_i             (  {1'b0,abs_mantissa} ),
    .sign_i                  (  final_sign          ),
    .round_sticky_bits_i     (  rs_bits             ),
    .rnd_mode_i              (  rnd_mode_i          ),
    .effective_subtraction_i (  V                   ),
    .abs_rounded_o           (  rounded_mantissa    ),
    .sign_o                  (  sign_after_round    ),
    .exact_zero_o            (  exact_zero          )
  )                                                                                                                                    ;

  // ---------------
  // Post-rounding normalization & classification
  // ---------------
  
  always_comb
  begin : post_round_normalization
    if (round_ovf)
    begin
      final_exp = exp_post_norm + 1                                                                                                    ;
    end
    else
    begin
      final_exp = exp_post_norm                                                                                                        ;
    end
  end

  assign inf_result = final_exp > 30                                                                                                   ;

  // ---------------
  // Special cases handling
  // ---------------
  
  logic                         result_is_special                                                                                      ;
  logic [MAN_BITS + 1 - 1 : 0 ] inf_check_mantissa                                                                                     ;
  logic [FP_WIDTH     - 1 : 0 ] canonical_qnan_bin  = 16'h7E00                                                                         ;
  logic [FP_WIDTH     - 1 : 0 ] pos_inf             = 16'h7C00                                                                         ;
  logic [FP_WIDTH     - 1 : 0 ] neg_inf             = 16'hFC00                                                                         ;
  
  always_comb
  begin : special_result_detection
    if( any_operand_nan | ( has_neg_inf & has_pos_inf ))
    begin
      result_is_special     = 1'b1                                                                                                     ;
      special_result        = canonical_qnan_bin                                                                                       ;
    end
    else if (( inf_result &  (~ sign_after_round)) | has_pos_inf )
    begin
      result_is_special     = 1'b1                                                                                                     ; 
      special_result        = pos_inf                                                                                                  ; 
    end
    else if (( inf_result & sign_after_round ) | has_neg_inf )
    begin
      result_is_special     = 1'b1                                                                                                     ; 
      special_result        = neg_inf                                                                                                  ; 
    end
    else
      special_result          = 1'b0                                                                                                   ;
  end

  // ---------------
  // Result packing
  // ---------------

  logic [FP_WIDTH - 1 : 0 ] result                                                                                                     ;
  logic [FP_WIDTH - 1 : 0 ] special_result                                                                                             ;

  assign result   = (result_is_special) ? special_result 
                                        : {sign_after_round, final_exp[ EXP_BITS - 1 : 0 ], rounded_mantissa[ MAN_BITS - 1 : 0 ]}      ;
  assign result_o = result                                                                                                             ;

endmodule
