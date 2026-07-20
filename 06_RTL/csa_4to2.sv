module csa_4to2_tree #(
    // parameter int unsigned  = 11
    parameter int unsigned WIDTH = 36
    ) (
    input  logic [3:0][WIDTH-1:0] operands_i,
    output logic [WIDTH-1:0]      save_o,
    output logic [WIDTH-1:0]      carry_o
    );

    function automatic void csa_3to2 (
        input  logic [WIDTH-1:0] a_i, b_i, c_i,
        output logic [WIDTH-1:0] save,
        output logic [WIDTH-1:0] carry
    );
        save = a_i ^ b_i ^ c_i;

        // We shift left bc the carry at bit i belongs to position i+1
        carry = ((a_i & b_i) | (b_i & c_i) | (a_i & c_i)) << 1;
    endfunction

    logic [WIDTH-1:0] S1, C1;

    always_comb begin
        // stage 1: s1,c1 = a + b + c  
        csa_3to2(operands_i[3], operands_i[1], operands_i[2], S1, C1);

        // stage 2: save_o, carry_o = s1 + c1 + d
        csa_3to2(operands_i[0], S1, C1, save_o, carry_o);
    end
endmodule
