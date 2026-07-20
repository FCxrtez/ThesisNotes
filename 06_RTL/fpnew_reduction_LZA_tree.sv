`timescale 1ns / 1ps
//////////////////////////////////////////////////////////////////////////////////
// Company: 
// Engineer: 
// 
// Create Date: 07/02/2026 05:47:57 PM
// Design Name: 
// Module Name: fpnew_reduction_LZA_tree
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

module fpnew_reduction_LZA_tree #(
    parameter int  WIDTH = 37,
    parameter type String_type = logic
)(
    input  String_type g_string_i,
    output Tree_node_t root_o
);

    /// Tree depth and width
    localparam int PADDED_INPUTS = 1 <<($clog2(WIDTH));
    localparam int NUM_STAGES = $clog2(PADDED_INPUTS)+1;

    Tree_node_t tree_grid [NUM_STAGES][PADDED_INPUTS];

    always_comb begin : tree_initializing
        // Input driven nodes
        // i [=< \ <] WIDTH+1?
        for(int i = 0 ; i < WIDTH ; i = i + 1) begin
            tree_grid[0][i].z = g_string_i.z[i];
            tree_grid[0][i].p = g_string_i.p[i];
            tree_grid[0][i].n = g_string_i.n[i];
            tree_grid[0][i].y = 0;
        end
        
        // Neutral nodes
        for(int i = WIDTH ; i < PADDED_INPUTS ; i++) begin
            tree_grid[0][i].z = 1;
            tree_grid[0][i].p = 0;
            tree_grid[0][i].n = 0;
            tree_grid[0][i].y = 0;
        end        
    end

    genvar stage, node;
    generate
        for(stage = 1; stage < NUM_STAGES; stage++) begin : stage_reduction_loop
            localparam  int NODES_IN_STAGE = PADDED_INPUTS >> stage;

            for(node = 0; node < NODES_IN_STAGE; node++) begin
                always_comb begin
                    tree_grid[stage][node] = gen_next_node(
                        tree_grid[stage-1][2*node+1], // left parent
                        tree_grid[stage-1][2*node  ]  // right parent
                    );
                end
            end
        end
    endgenerate

    assign root_o = tree_grid[NUM_STAGES-1][0];

endmodule
