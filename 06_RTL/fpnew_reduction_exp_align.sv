module fpnew_reduction_exp_align #(
    parameter int unsigned           Width              = 64, 
    parameter fpnew_pkg::fp_format_e fp_format          = fpnew_pkg::fp_format_e'('d2),
    parameter int unsigned           EXP_BITS           = fpnew_pkg::exp_bits(fp_format), // Number of bits in the exponent
    parameter int unsigned           NUM_OPERANDS       = fpnew_pkg::num_lanes(Width, fp_format, 1'b1),
    parameter int unsigned           SHIFT_AMOUNT_WIDTH = $clog2(fpnew_pkg::max_exp_dif(fp_format)) // Max shift possible with FP16 is 30
) (
    input  logic [NUM_OPERANDS-1:0][EXP_BITS-1:0]           exponents_i, // Biased exponents
    output logic [NUM_OPERANDS-1:0][SHIFT_AMOUNT_WIDTH-1:0] shifts_o,    // Alignment amounts
    output logic [EXP_BITS-1:0]                             max_exp_o
);

  // Result format: {carry_out, difference}
  
  logic c01, c02, c03, c12, c13, c23;
  logic [EXP_BITS-1:0] d01, d02, d03, d12, d13, d23;
  logic [3:0] is_max;
  
  assign {c01, d01} = {1'b0, exponents_i[0]} - {1'b0, exponents_i[1]};
  assign {c02, d02} = {1'b0, exponents_i[0]} - {1'b0, exponents_i[2]};
  assign {c03, d03} = {1'b0, exponents_i[0]} - {1'b0, exponents_i[3]};
  assign {c12, d12} = {1'b0, exponents_i[1]} - {1'b0, exponents_i[2]};
  assign {c13, d13} = {1'b0, exponents_i[1]} - {1'b0, exponents_i[3]};
  assign {c23, d23} = {1'b0, exponents_i[2]} - {1'b0, exponents_i[3]};
  
  
  // Lane 0 wins if it is >= 1, 2, and 3
  // for example, if exp[0] > exp[1], then exp[0] - exp[1] > 0, then c01 = 0
  assign is_max[0] = !c01 & !c02 & !c03;
  
  // Lane 1 wins if it is > 0 (so c01), and >= 2, 3
  assign is_max[1] = c01 & !c12 & !c13;
  
  // Lane 2 wins if > 0, 1, and >= 3
  assign is_max[2] = c02 & c12 & !c23;
  
  // Lane 3 wins if > 0, 1, 2
  assign is_max[3] = c03 & c13 & c23;

  // For each lane, we select the shift based on who is max.
  
  always_comb begin
    unique case (is_max)
      4'b0001: begin
        shifts_o[0] = 0;
        shifts_o[1] = d01;
        shifts_o[2] = d02;
        shifts_o[3] = d03;

        max_exp_o = exponents_i[0];
      end

      4'b0010: begin
        shifts_o[0] = -d01;
        shifts_o[1] = 0;
        shifts_o[2] = d12;
        shifts_o[3] = d13;

        max_exp_o = exponents_i[1];
      end

      4'b0100: begin
        shifts_o[0] = -d02;
        shifts_o[1] = -d12;
        shifts_o[2] = 0;
        shifts_o[3] = d23;

        max_exp_o = exponents_i[2];
      end

      4'b1000: begin
        shifts_o[0] = -d03;
        shifts_o[1] = -d13;
        shifts_o[2] = -d23;
        shifts_o[3] = 0;

        max_exp_o = exponents_i[3];
      end
      
      default: begin
        $display("WARNING: no max found during exp alingment");
        shifts_o = '0;
      end
    endcase
  end
endmodule

// maxima diferencia acotada por cantidad de bits de exp, diseñamos bus de shifteo teniendo eso en cuenta
