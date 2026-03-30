TOPLEVEL_LANG ?= verilog

PWD=$(shell pwd)

export PYTHONPATH := $(PWD)/model:$(PYTHONPATH)

ifeq ($(TOPLEVEL_LANG),verilog)
    VERILOG_SOURCES = $(PWD)/karatsuba.sv
else ifeq ($(TOPLEVEL_LANG),vhdl)
    VHDL_SOURCES = $(PWD)/adder.vhdl
    ifneq ($(filter $(SIM),ius xcelium),)
        COMPILE_ARGS += -v93
    endif
else
    $(error A valid value (verilog or vhdl) was not provided for TOPLEVEL_LANG=$(TOPLEVEL_LANG))
endif

TOPLEVEL     := karatsuba_recursive
MODULE := test_karatsuba_func_rec_coverage

include $(shell cocotb-config --makefiles)/Makefile.sim
