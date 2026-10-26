import tb_pkg::*;

module fpnew_reduction_LZA # (
    parameter int unsigned                      WIDTH       = tb_pkg::TB_INTERNAL_PRECISION,
    parameter int unsigned                      LZC_WIDTH   = tb_pkg::TB_LZC_WIDTH
    ) ( 
    input  logic [ WIDTH              - 1 : 0 ] a_i              ,
    input  logic [ WIDTH              - 1 : 0 ] b_i              ,
    input  logic                                V_i              ,
    output logic                                X_o              ,
    output logic                                Y_o              ,
    output logic [ LZC_WIDTH          - 1 : 0 ] lzc_o
    );

    typedef struct packed {
        logic [ WIDTH + 1 - 1 : 0 ] p;
        logic [ WIDTH + 1 - 1 : 0 ] n;
        logic [ WIDTH + 1 - 1 : 0 ] z;
    } G_struct;

    // Reduction tree parameters
    localparam int PADDED_INPUTS = 1 << $clog2(WIDTH +1)       ;
    localparam int NUM_LAYERS    = $clog2(PADDED_INPUTS) + 1   ;

    logic [ WIDTH                 - 1 : 0 ] T                  ;
    logic [ WIDTH                 - 1 : 0 ] Z                  ;
    logic [ WIDTH                 - 1 : 0 ] G                  ;
    logic [ WIDTH                 - 1 : 0 ] F                  ;
    logic [ WIDTH   +  1          - 1 : 0 ] T_ex               ;
    logic [ WIDTH   +  1          - 1 : 0 ] Z_ex               ;
    logic [ WIDTH   +  1          - 1 : 0 ] G_ex               ;
    logic [ LZC_WIDTH             - 1 : 0 ] lzc                ;
    logic                                   term_V             ;
    logic                                   term_notV          ;
    logic                                   term_T             ;
    logic                                   term_notT          ;
    logic                                   empty_o            ;

    G_struct                                Gp, Gn             ;

    Tree_node_t                             pos_root, neg_root ;

    assign T =   a_i ^ b_i                                     ;
    assign Z = ~(a_i | b_i)                                    ;
    assign G =   a_i & b_i                                     ;

    always_comb
    begin : gen_F
        term_V = 0                                                                          ;

        for (int i = 0; i < WIDTH; i++)
        begin    
            if (i == 0) begin
                F[i] = (T[i+1] & ((G[i] & V_i) | Z[i])) | (~T[i+1] & ((Z[i] & V_i) | G[i])) ;

            end
            else if ( i == WIDTH-1 )
            begin
                term_V      = V_i & ((G[i] & ~Z[i-1]) | (Z[i] & ~G[i-1]))                   ;
                term_notV   = ~V_i & ((Z[i] & ~Z[i-1]) | ~Z[i])                             ;
                F[i]        = term_V | term_notV                                            ;
            end
            else
            begin : general_case
                term_T      =  T[i+1] & ((G[i] & ~Z[i-1]) | (Z[i] & ~G[i-1]))               ;
                term_notT   = ~T[i+1] & ((Z[i] & ~Z[i-1]) | (G[i] & ~G[i-1]))               ;
                F[i]        = term_T | term_notT                                            ;
            end
        end
    end

    lzc # (
        .WIDTH      (   WIDTH   ),
        .MODE       (   1'b1    )
    ) i_reduction_lzc (
        .in_i       (   F       ),
        .cnt_o      (   lzc     ),
        .empty_o    (   empty_o )
    ) ;

    assign lzc_o = ( empty_o ) ? WIDTH : lzc            ;

    // Concurrent error detection

    assign T_ex =  {V_i  , T   }                          ;
    assign Z_ex =  {Z    , 1'b0}                          ;
    assign G_ex =  {G    , 1'b0}                          ;

    assign Gp.p =   G_ex | V_i                          ;
    assign Gp.n =  (Z_ex | {WIDTH-1'b0,~V_i}) & T_ex    ;
    assign Gp.z = ~(Gp.p | Gp.n)                        ;

    assign Gn.p =   Z_ex | 1'b1                         ;
    assign Gn.n =   G_ex & T_ex                         ;
    assign Gn.z = ~(Gn.p | Gn.n)                        ;

    //error detection
    fpnew_reduction_LZA_tree # (
        .WIDTH          (   WIDTH + 1   ),
        .String_type    (   G_struct    )
    ) i_pos_tree               (
        .g_string_i     (   Gp          ),
        .root_o         (   pos_root    )
    ) ;

    fpnew_reduction_LZA_tree # (
        .WIDTH          (   WIDTH       ),
        .String_type    (   G_struct    )
    ) i_neg_tree               (
        .g_string_i     (   Gn          ),
        .root_o         (   neg_root    )
    ) ;

    // one bit less error
    assign Y_o = (V_i & (pos_root.y | pos_root.n)) | (~V_i & (neg_root.n & Z[WIDTH-1]));

    // Overflow flag - not used
    assign X_o = ~V_i & pos_root.p;

endmodule