import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge
import random


async def reset(dut):
    dut.rst.value = 1
    dut.s_axis_valid.value = 0
    dut.m_axis_ready.value = 1

    for _ in range(5):
        await RisingEdge(dut.clk)

    dut.rst.value = 0


async def send_transaction(dut, x, y):
    WIDTH = len(dut.s_axis_data) // 2
    data = (x << WIDTH) | y

    dut.s_axis_data.value = data
    dut.s_axis_valid.value = 1

    while not dut.s_axis_ready.value:
        await RisingEdge(dut.clk)

    await RisingEdge(dut.clk)
    dut.s_axis_valid.value = 0


async def receive_output(dut):
    while not dut.m_axis_valid.value:
        await RisingEdge(dut.clk)

    # wait 1 extra cycle (important)
    await RisingEdge(dut.clk)

    return dut.m_axis_data.value.to_unsigned()


@cocotb.test()
async def test_basic(dut):

    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())
    await reset(dut)

    vectors = [(3, 5), (10, 20), (1234, 5678)]

    for x, y in vectors:
        await send_transaction(dut, x, y)
        result = await receive_output(dut)

        assert result == x * y, \
            f"FAILED: {x} * {y} = {x*y}, got {result}"


@cocotb.test()
async def test_random(dut):

    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())
    await reset(dut)

    for _ in range(5000):
        x = random.getrandbits(64)
        y = random.getrandbits(64)

        await send_transaction(dut, x, y)
        result = await receive_output(dut)

        assert result == x * y, \
            f"FAILED: {x} * {y}"