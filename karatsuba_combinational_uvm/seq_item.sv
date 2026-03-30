class seq_item extends uvm_sequence_item;
  rand bit [31:0] ip1, ip2;
  bit [63:0] out;
  
  function new(string name = "seq_item");
    super.new(name);
  endfunction
  
  `uvm_object_utils_begin(seq_item)
    `uvm_field_int(ip1,UVM_ALL_ON)
    `uvm_field_int(ip2,UVM_ALL_ON)
  `uvm_object_utils_end
  
  constraint ip_c {ip1 < 10000; ip2 < 10000;}
endclass