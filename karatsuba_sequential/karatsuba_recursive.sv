
module karatsuba_recursive #(
    parameter num_bits = 64,
    parameter base_mult = 32
)(
    input clk,
    input start,
    input  wire [num_bits-1:0] x,
    input  wire [num_bits-1:0] y,
    output reg [2*num_bits-1:0] out
);

generate
    if (num_bits <= base_mult) begin : base_case
        always @(posedge clk)begin
            out <= x * y;
        end
    end else begin : recurse
        localparam fh = num_bits / 2;
        localparam sh = num_bits - fh;

        wire [fh-1:0] x0 = x[fh-1:0];
        wire [sh-1:0] x1 = x[num_bits-1:fh];
        wire [fh-1:0] y0 = y[fh-1:0];
        wire [sh-1:0] y1 = y[num_bits-1:fh];

        // Sign-extend or zero-extend smaller part before addition
        wire [sh:0] x0_ext = {{(sh - fh + 1){1'b0}}, x0};
        wire [sh:0] y0_ext = {{(sh - fh + 1){1'b0}}, y0};

        wire [sh:0] sum_x = x1 + x0_ext;
        wire [sh:0] sum_y = y1 + y0_ext;

        wire [2*fh-1:0] out_p1;
        reg [2*fh-1:0] out_p1_reg;
        wire [2*sh-1:0] out_p2;
        reg [2*sh-1:0] out_p2_reg;
        wire [2*(sh+1)-1:0] out_p3;
        reg [2*(sh+1)-1:0] out_p3_reg;

        karatsuba_recursive #(fh, base_mult) p1(.x(x0), .y(y0), .out(out_p1), .start(start), .clk(clk));
        karatsuba_recursive #(sh, base_mult) p2(.x(x1), .y(y1), .out(out_p2), .start(start), .clk(clk));
        karatsuba_recursive #(sh+1, base_mult) p3(.x(sum_x), .y(sum_y), .out(out_p3), .start(start), .clk(clk));

        always @(posedge clk)begin
            out_p1_reg <= out_p1;
            out_p2_reg <= out_p2;
            out_p3_reg <= out_p3;
        end

        // Promote operands to same width before arithmetic
        wire [2*(sh+1)-1:0] p2_ext = {{(2*(sh+1)-2*sh){1'b0}}, out_p2_reg};
        wire [2*(sh+1)-1:0] p1_ext = {{(2*(sh+1)-2*fh){1'b0}}, out_p1_reg};

        wire [2*(sh+1)-1:0] middle = out_p3_reg - p2_ext - p1_ext;

        wire [2*num_bits-1:0] part1 = {{(2*num_bits - 2*sh){1'b0}}, out_p2_reg} << (2*fh);
        wire [2*num_bits-1:0] part2 = {{(2*num_bits - 2*(sh+1)){1'b0}}, middle} << fh;
        wire [2*num_bits-1:0] part3 = {{(2*num_bits - 2*fh){1'b0}}, out_p1_reg};

        always @(posedge clk)begin
            out <= part1 + part2 + part3;
        end
    end
endgenerate
endmodule

