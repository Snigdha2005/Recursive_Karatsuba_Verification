import cocotb
from cocotb.triggers import Timer
import random

from cocotb_coverage.coverage import CoverPoint, CoverCross, coverage_db

from adder_model import karatsuba_model


# ============================================================
# 🔹 COVERAGE SAMPLING FUNCTION (CORRECT METHOD)
# ============================================================

@CoverPoint("karatsuba.x_size",
            xf=lambda x, y: x.bit_length(),
            bins=[0, 4, 8, 12, 16])

@CoverPoint("karatsuba.y_size",
            xf=lambda x, y: y.bit_length(),
            bins=[0, 4, 8, 12, 16])

@CoverPoint("karatsuba.special",
            xf=lambda x, y: (x, y),
            bins=[
                (0, 0),
                (0, 1),
                (1, 0),
                (1, 1),
                (2**16 - 1, 2**16 - 1)
            ])

@CoverPoint("karatsuba.pattern",
            xf=lambda x, y: (
                "all_zeros" if x == 0 else
                "all_ones" if x == (2**16 - 1) else
                "random"
            ),
            bins=["all_zeros", "all_ones", "random"])

@CoverCross("karatsuba.cross_xy_size",
            items=["karatsuba.x_size", "karatsuba.y_size"])

def sample_coverage(x, y):
    """This function triggers ALL coverage sampling"""
    pass


# ============================================================
# 🔹 BASIC TEST
# ============================================================

@cocotb.test()
async def test_basic(dut):
    """Simple deterministic test"""

    dut.start.value = 0

    x = 5
    y = 10

    dut.x.value = x
    dut.y.value = y

    await Timer(2, units="ns")

    expected = karatsuba_model(x, y)

    sample_coverage(x, y)   # ✅ coverage here too

    assert int(dut.out.value) == expected, \
        f"Mismatch: {int(dut.out.value)} != {expected}"


# ============================================================
# 🔹 RANDOM + COVERAGE TEST
# ============================================================

@cocotb.test()
async def test_random_with_coverage(dut):
    """Randomized test with functional coverage"""

    dut.start.value = 0

    for i in range(20000):

        # --------------------------------------------
        # Directed + random stimulus
        # --------------------------------------------
        if i < 500:
            x = 0
            y = random.randint(0, 2**16 - 1)

        elif i < 1000:
            x = 2**16 - 1
            y = 2**16 - 1

        elif i < 1500:
            x = 1
            y = random.randint(0, 2**16 - 1)

        else:
            x = random.randint(0, 2**16 - 1)
            y = random.randint(0, 2**16 - 1)

        # Apply inputs
        dut.x.value = x
        dut.y.value = y

        await Timer(2, units="ns")

        # Expected output
        expected = karatsuba_model(x, y)

        # --------------------------------------------
        # ✅ COVERAGE SAMPLING (CORRECT WAY)
        # --------------------------------------------
        sample_coverage(x, y)

        # --------------------------------------------
        # Check
        # --------------------------------------------
        assert int(dut.out.value) == expected, \
            f"FAIL: {x} * {y} = {int(dut.out.value)}, expected {expected}"


# ============================================================
# 🔹 COVERAGE REPORT
# ============================================================

@cocotb.test()
async def report_coverage(dut):
    """Print functional coverage report"""

    dut._log.info("========== COVERAGE REPORT ==========")
    coverage_db.report_coverage(cocotb.log.info)