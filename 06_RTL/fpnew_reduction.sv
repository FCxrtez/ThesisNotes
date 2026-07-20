// `include "common_cells/registers.svh" //en caso de necesitar registro usar macros FFL, etc

module fpnew_reduction #(
  parameter fpnew_pkg::fp_format_e   FpFormat      = fpnew_pkg::fp_format_e'('d2),
  parameter int unsigned             Width         = 64,
  parameter int unsigned             NumPipeRegs   = 0,
  parameter fpnew_pkg::pipe_config_t PipeConfig    = fpnew_pkg::BEFORE,
  parameter type                     TagType       = logic,
  parameter type                     AuxType       = logic,
  parameter logic                    EnableVectors = 1'b1,
  // Do not change
  localparam int unsigned FP_WIDTH       = fpnew_pkg::fp_width(FpFormat),
  localparam int unsigned NUM_OPERANDS   = fpnew_pkg::num_lanes(Width, FpFormat, EnableVectors),
  localparam int unsigned ExtRegEnaWidth = NumPipeRegs == 0 ? 1 : NumPipeRegs
) (
  input logic                       clk_i,
  input logic                       rst_ni,
  // Input signals
  input logic [1:0][Width-1:0]      operands_i, // 2 operands full width
  input logic [3:0]                 is_boxed_i, // 4 operands - donde se define? significado explicado en README.m- Pero tengo 4 operandos por bus, capaz deba implementar mi propio classifier
  input fpnew_pkg::roundmode_e      rnd_mode_i,
  input fpnew_pkg::operation_e      op_i,
  input logic                       op_mod_i,
  input TagType                     tag_i,
  input logic [NUM_OPERANDS-1:0]    mask_i, // buscar manera de pasar mascara de bits en este campo
  input AuxType                     aux_i,
  // input logic                       vectorial_op_i, // pasado en aux_i - para que sirve?
  // Input Handshake
  input  logic                      in_valid_i,
  output logic                      in_ready_o,
  input  logic                      flush_i,
  // Output signals
  output logic [FP_WIDTH-1:0]       result_o,
  output fpnew_pkg::status_t        status_o,
  output logic                      extension_bit_o,
  output TagType                    tag_o,
  // output logic                   mask_o, no es relevante para reduccion pues devolvemos un solo valor/status
  output AuxType                    aux_o, // utilizado en fpnew_fma para definir result_is_vector, que luego se utiliza para definir result_o
  // Output handshake      
  output logic                      out_valid_o,
  input  logic                      out_ready_i,
  // Indication of valid data in flight
  output logic                      busy_o,
  // External register enable override
  input  logic [ExtRegEnaWidth-1:0] reg_ena_i,
  output logic                      early_valid_o
);

  // ----------
  // Constants
  // ----------
  localparam int unsigned EXP_BITS           = fpnew_pkg::exp_bits(FpFormat);
  localparam int unsigned MAN_BITS           = fpnew_pkg::man_bits(FpFormat);
  localparam int unsigned BIAS               = fpnew_pkg::bias(FpFormat);
  // including hidden bit
  localparam int unsigned PRECISION_BITS     = MAN_BITS + 1;
  // Segun Tenca es (n-1)* precision + 3
  localparam int unsigned INTERNAL_PRECISION = 3 * PRECISION_BITS + 3; // 1 bit de signo + 2 ovf
  // Maximo shift acotado por precision interna de sumador - puedo limitar por maxima diferencia de exponentes
  localparam int unsigned SHIFT_AMOUNT_WIDTH = $clog2(fpnew_pkg::max_exp_dif(FpFormat));

  // ----------
  // Handshake signals
  // ----------
  logic local_in_ready = '1; // si agregamos registros de pipeline cambiar la manera de asignar este ready
  assign in_ready_o = 1;
  //assign in_ready_o = out_ready_i; // ya que esperamos que se calcule en un ciclo
  assign tag_o = tag_i;

  // ----------------
  // Type definition
  // ----------------
  typedef struct packed {
    logic                sign;
    logic [EXP_BITS-1:0] exponent;
    logic [MAN_BITS-1:0] mantissa;
  } fp_t;

  // ---------------
  // Input processing
  // ---------------
  fp_t                 [NUM_OPERANDS-1:0]                     unpacked_operands;
  fpnew_pkg::fp_info_t [NUM_OPERANDS-1:0]                     operands_info;
  logic                [NUM_OPERANDS-1:0][EXP_BITS-1:0]       packed_exp;
  logic                [NUM_OPERANDS-1:0][PRECISION_BITS-1:0] packed_implicit_mantissa;
  logic                [NUM_OPERANDS-1:0]                     packed_sign;

  fpnew_classifier #(
    .FpFormat    (FpFormat),
    .NumOperands (NUM_OPERANDS)
  ) i_classifier (
    .operands_i  (unpacked_operands),
    .is_boxed_i  (is_boxed_i),
    .info_o      (operands_info)
  );


  always_comb begin : unpack_operands
    unpacked_operands = '0;
    packed_exp = '0;
    packed_implicit_mantissa = '0;
    packed_sign = '0;

    if (in_valid_i && local_in_ready) begin
      for (int i = 0; i < int'(NUM_OPERANDS); i++) begin
        unpacked_operands[i] = fp_t'(operands_i[0][unsigned'(i)*FP_WIDTH +: FP_WIDTH]);
        if (operands_info[i].is_normal) begin
          packed_exp[i] = unpacked_operands[i].exponent;
        end else begin
          packed_exp[i] = 5'b0_0001;
        end
        packed_implicit_mantissa[i] = operands_info[i].is_normal ? {1'b1, unpacked_operands[i].mantissa} : {1'b0, unpacked_operands[i].mantissa};
        packed_sign[i] = unpacked_operands[i].sign;
      end
    end
  end

  // ---------------------
  // Input classification
  // ---------------------
  logic any_operand_inf;
  logic any_operand_nan;
  logic signalling_nan;

  always_comb begin : classification_reduction
    any_operand_inf = '0;
    any_operand_nan = '0;
    signalling_nan = '0;

    for (int i = 0; i < int'(NUM_OPERANDS); i++) begin
      any_operand_inf |= operands_info[i].is_inf;
      any_operand_nan |= operands_info[i].is_nan;
      signalling_nan |= operands_info[i].is_signalling;
    end
  end

  always_comb begin : special_cases
  //  ... Investigar que casos especiales se deben manejar en una reduccion
  // Una valor NaN -> resultado NaN
  // Una valor Inf -> resultado Inf (si hay un NaN, prevalece el NaN)
  // Si todos los operandos son cero -> resultado cero (signo puede depender de la operacion)
  // Si hay Inf y -Inf -> resultado NaN
  end

  // ---------------
  // Exponent difference & mantissa alignment
  // ---------------

  logic        [NUM_OPERANDS-1:0][SHIFT_AMOUNT_WIDTH-1:0]       shifts;
  logic        [NUM_OPERANDS-1:0][3 * PRECISION_BITS - 1:0]     aligned_mantissas;
  logic        [NUM_OPERANDS-1:0][3 * PRECISION_BITS + 3 - 1:0] padded_mantissa;
  logic signed [NUM_OPERANDS-1:0][3 * PRECISION_BITS + 3 - 1:0] signed_mantissas_w_ovf;
  logic        [NUM_OPERANDS-1:0][PRECISION_BITS-1:0]           aligned_mantissas_stk_bits;
  logic        [NUM_OPERANDS-1:0]                               sticky_before_add;
  logic        [EXP_BITS-1:0]                                   max_exp;
  // logic signed [NUM_OPERANDS-1:0][3 * PRECISION_BITS + 5 - 1:0] signed_mantisas; // +1 para signo

  fpnew_reduction_exp_align #(
    .EXP_BITS           (EXP_BITS),
    .NUM_OPERANDS       (NUM_OPERANDS),
    .SHIFT_AMOUNT_WIDTH (SHIFT_AMOUNT_WIDTH)
  ) i_exp_align (
    .exponents_i (packed_exp),
    .shifts_o    (shifts),
    .max_exp_o   (max_exp)
  );

  generate
    for (genvar i = 0; i < int'(NUM_OPERANDS); i++) begin : mantissa_alignment

      // Each addend is right-shifted according to the exponent difference. Up to p bits
      // are shifted out and compressed into a sticky bit.
      // BEFORE THE SHIFT:
      // | packed_implicit_mantissa[i] | 000..000 |
      // <-             p            -> <-  3p  ->
      // AFTER THE SHIFT:
      // | 000..........000 | packed_implicit_mantissa[i] | 000...............0GR |  sticky bits  |
      //  <-   shifts[i]  -> <-            p            -> <-   2p -shifts[i]   -> <-      p    ->

      // 
      assign {aligned_mantissas[i], aligned_mantissas_stk_bits[i]} = (packed_implicit_mantissa[i] << 3 * PRECISION_BITS) >> shifts[i];

      assign sticky_before_add[i] = | aligned_mantissas_stk_bits[i];
    end
  endgenerate

  // ---------------------------------------------
  // Sign change (MSB-side operand as anchor)
  // ---------------------------------------------

  logic [NUM_OPERANDS-1:0] inversion_signs;
  logic                    anchor_sign;
  logic                    final_sign;

  assign anchor_sign = packed_sign[NUM_OPERANDS-1];

  always_comb begin :sign_inverison
    for (int i = 0; i < int'(NUM_OPERANDS); i++) begin
      inversion_signs[i] = packed_sign[i] ^ anchor_sign;

      padded_mantissa[i] = {3'b000, aligned_mantissas[i]};
      if (inversion_signs[i]) begin
        signed_mantissas_w_ovf[i] = signed'(-padded_mantissa[i]);
      end else begin
        signed_mantissas_w_ovf[i] = signed'(padded_mantissa[i]);
      end
    end
  end

  // ---------------------------------------------
  // Mantissa adition & Leading zero anticipator
  // ---------------------------------------------
  // Carry save adder para generar carry y save inputs para LZA

  logic                                   V, X, Y;
  logic unsigned [SHIFT_AMOUNT_WIDTH-1:0] lzc;
  logic unsigned [SHIFT_AMOUNT_WIDTH-1:0] corrected_lzc;


  assign V = !((& packed_sign) || (~| packed_sign)); // todos los signos iguales -> effective addition

  logic        [3 * PRECISION_BITS + 3 - 1:0] save, carry;
  logic        [3 * PRECISION_BITS + 3 - 1:0] mantissa_abs, mantissa_norm;
  logic signed [3 * PRECISION_BITS + 3 - 1:0] mantissa_sum;
  
  csa_4to2_tree #(
    .WIDTH(3 * PRECISION_BITS + 3)
  ) i_csa_tree (
    .operands_i(signed_mantissas_w_ovf),
    .save_o(save),
    .carry_o(carry)
  );

  fpnew_reduction_LZA #(
    .WIDTH(3 * PRECISION_BITS + 3),
    .SHIFT_AMOUNT_WIDTH(SHIFT_AMOUNT_WIDTH)
  ) i_lza (
    .a_i(save),
    .b_i(carry),
    .V_i(V),
    .X_o(X),
    .Y_o(Y),
    .lzc_o(lzc)
  );

  assign mantissa_sum = save + carry;

  assign corrected_lzc = lzc + Y;

  // ---------------
  // Absolute value
  // ---------------

  always_comb begin : absolute_value
    if(mantissa_sum[3 * PRECISION_BITS + 2]) begin : neg_result
      mantissa_abs = -mantissa_sum;
    end else begin
      mantissa_abs = mantissa_sum;
    end
  end

  assign final_sign = mantissa_sum[3 * PRECISION_BITS + 2] ^ anchor_sign;

  // ---------------
  // Mantissa normalization & post normalization exponent
  // ---------------
  logic                                   enable_flush, inf_result;
  logic          [EXP_BITS +1 -1:0]       exp_post_norm, final_exp;
  logic unsigned [SHIFT_AMOUNT_WIDTH-1:0] shift_amount;

  always_comb begin : exponent_cases
    enable_flush = 1'b0;

    if (max_exp == 0) begin : Subnormal_number
      shift_amount = '0;
      exp_post_norm = '0;

    end else if(corrected_lzc < max_exp) begin : Normal_number
      shift_amount = corrected_lzc;
      exp_post_norm = max_exp + 3 - corrected_lzc; // +3 for the sign/ovf bits

    end else begin : Normal_to_Subnormal
      enable_flush = 1'b1;
      shift_amount = '0;
      exp_post_norm = '0;
    end
  end

  assign mantissa_norm = enable_flush ? '0 : (mantissa_abs << shift_amount);
  
  // ---------------
  // Rounding
  // ---------------
  logic                  sign_after_round, exact_zero, round_ovf;
  logic [1:0]            rs_bits;
  logic [MAN_BITS-1:0]   abs_mantissa;
  logic [MAN_BITS+1-1:0] rounded_mantissa;
  
  assign abs_mantissa = mantissa_norm[3*PRECISION_BITS+1 -: MAN_BITS];
  assign rs_bits = mantissa_norm[3*PRECISION_BITS+1-MAN_BITS -: 2];
  // assign {abs_mantissa, rs_bits} = mantissa_norm[3*PRECISION_BITS+1:0];
  assign round_ovf = rounded_mantissa[MAN_BITS];

  fpnew_rounding #(
    .AbsWidth(MAN_BITS+1)
  ) i_rounding (
    .abs_value_i({1'b0,abs_mantissa}),
    .sign_i(final_sign),
    .round_sticky_bits_i(rs_bits),
    .rnd_mode_i(rnd_mode_i),
    .effective_subtraction_i(V),
    .abs_rounded_o(rounded_mantissa),
    .sign_o(sign_after_round),
    .exact_zero_o(exact_zero)
  );

  // ---------------
  // Post-rounding normalization & classification
  // ---------------
  
  always_comb begin : post_round_normalization

    if (round_ovf) begin
      final_exp = exp_post_norm + 1;
    end else begin
      final_exp = exp_post_norm;
    end

    // 30 is max possible exp for FP16, could be parametrized
    inf_result = final_exp > 30 ? 1'b1 : 1'b0;
  end

  // ---------------
  // Special cases handling
  // ---------------
  logic [MAN_BITS+1-1:0] inf_check_mantissa;
  
  always_comb begin : set_to_inf
    if (inf_result) begin
      // set to [+/-]Inf
      inf_check_mantissa = '0; 
    end else begin
      inf_check_mantissa = rounded_mantissa;
    end
  end

  // ---------------
  // Catastrophic cancellation handling
  // ---------------

  // ---------------
  // Result packing
  // ---------------

  logic [FP_WIDTH-1:0] result;

  assign result = {sign_after_round, final_exp[EXP_BITS-1:0], inf_check_mantissa[MAN_BITS-1:0]};
  assign result_o = result;

endmodule
