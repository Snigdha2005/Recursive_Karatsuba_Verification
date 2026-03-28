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
        always @(posedge clk) begin
            out <= x * y;
        end
    end else begin : recurse

        localparam fh = num_bits / 2;
        localparam sh = num_bits - fh;

        wire [fh-1:0] x0 = x[fh-1:0];
        wire [sh-1:0] x1 = x[num_bits-1:fh];
        wire [fh-1:0] y0 = y[fh-1:0];
        wire [sh-1:0] y1 = y[num_bits-1:fh];

        wire [sh:0] x0_ext = {{(sh - fh + 1){1'b0}}, x0};
        wire [sh:0] y0_ext = {{(sh - fh + 1){1'b0}}, y0};

        wire [sh:0] sum_x = x1 + x0_ext;
        wire [sh:0] sum_y = y1 + y0_ext;

        wire [2*fh-1:0] out_p1;
        reg  [2*fh-1:0] out_p1_reg;

        wire [2*sh-1:0] out_p2;
        reg  [2*sh-1:0] out_p2_reg;

        wire [2*(sh+1)-1:0] out_p3;
        reg  [2*(sh+1)-1:0] out_p3_reg;

        karatsuba_recursive #(fh, base_mult) p1 (.clk(clk), .start(start), .x(x0),    .y(y0),    .out(out_p1));
        karatsuba_recursive #(sh, base_mult) p2 (.clk(clk), .start(start), .x(x1),    .y(y1),    .out(out_p2));
        karatsuba_recursive #(sh+1, base_mult) p3 (.clk(clk), .start(start), .x(sum_x), .y(sum_y), .out(out_p3));

        always @(posedge clk) begin
            out_p1_reg <= out_p1;
            out_p2_reg <= out_p2;
            out_p3_reg <= out_p3;
        end

        wire [2*(sh+1)-1:0] p2_ext = {{(2*(sh+1)-2*sh){1'b0}}, out_p2_reg};
        wire [2*(sh+1)-1:0] p1_ext = {{(2*(sh+1)-2*fh){1'b0}}, out_p1_reg};

        wire [2*(sh+1)-1:0] middle = out_p3_reg - p2_ext - p1_ext;

        wire [2*num_bits-1:0] part1 = {{(2*num_bits - 2*sh){1'b0}}, out_p2_reg} << (2*fh);
        wire [2*num_bits-1:0] part2 = {{(2*num_bits - 2*(sh+1)){1'b0}}, middle} << fh;
        wire [2*num_bits-1:0] part3 = {{(2*num_bits - 2*fh){1'b0}}, out_p1_reg};

        always @(posedge clk) begin
            out <= part1 + part2 + part3;
        end
    end
endgenerate

endmodule

module karatsuba_axi #(
    parameter num_bits = 64,
    parameter base_mult = 32,
    parameter LATENCY = 40
)(
    input wire clk,
    input wire rst,

    // AXI Slave
    input wire s_axis_valid,
    output wire s_axis_ready,
    input wire [2*num_bits-1:0] s_axis_data,

    // AXI Master
    output reg m_axis_valid,
    input wire m_axis_ready,
    output reg [2*num_bits-1:0] m_axis_data
);

    reg start;
    reg busy;

    reg [num_bits-1:0] x_reg, y_reg;
    wire [2*num_bits-1:0] out;

    karatsuba_recursive #(num_bits, base_mult) dut (
        .clk(clk),
        .start(start),
        .x(x_reg),
        .y(y_reg),
        .out(out)
    );

    assign s_axis_ready = !busy;

    // Input handshake
    always @(posedge clk) begin
        if (rst) begin
            start <= 0;
            busy  <= 0;
        end else begin
            start <= 0;

            if (s_axis_valid && s_axis_ready) begin
                x_reg <= s_axis_data[2*num_bits-1:num_bits];
                y_reg <= s_axis_data[num_bits-1:0];
                start <= 1;
                busy  <= 1;
            end else if (valid_pipe[LATENCY-1]) begin
                busy <= 0;
            end
        end
    end

    // Valid pipeline
    reg [LATENCY-1:0] valid_pipe;

    always @(posedge clk) begin
        if (rst)
            valid_pipe <= 0;
        else
            valid_pipe <= {valid_pipe[LATENCY-2:0], start};
    end

    // Output
    always @(posedge clk) begin
        if (rst) begin
            m_axis_valid <= 0;
            m_axis_data  <= 0;
        end else begin
            m_axis_valid <= valid_pipe[LATENCY-1];

            if (valid_pipe[LATENCY-1]) begin
                m_axis_data <= out;
            end
        end
    end

endmodule