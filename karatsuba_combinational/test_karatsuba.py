import cocotb
from cocotb.triggers import Timer
import random

from adder_model import karatsuba_model   # rename file ideally


@cocotb.test()
async def test_basic(dut):
    """Simple deterministic test"""

    x = 5
    y = 10

    dut.start.value = 0   # IMPORTANT
    dut.x.value = x
    dut.y.value = y

    await Timer(2, units="ns")

    assert dut.out.value == karatsuba_model(x, y), \
        f"Mismatch: {dut.out.value} != {x*y}"


@cocotb.test()
async def test_random(dut):
    """Randomized multiplier test"""

    dut.start.value = 0

    for _ in range(20000):
        x = random.randint(0, 2**16 - 1)
        y = random.randint(0, 2**16 - 1)

        dut.x.value = x
        dut.y.value = y

        await Timer(2, units="ns")

        expected = karatsuba_model(x, y)

        assert dut.out.value == expected, \
            f"FAIL: {x} * {y} = {dut.out.value}, expected {expected}"