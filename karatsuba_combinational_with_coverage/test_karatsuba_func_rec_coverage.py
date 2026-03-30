import cocotb
from cocotb.triggers import Timer
import random

from cocotb_coverage.coverage import coverage_db, CoverPoint, CoverCross

# ============================================================
# Reference model (with recursion depth tracking)
# ============================================================

def karatsuba_model(x, y, depth=0):
    # Track recursion depth
    global max_depth
    max_depth = max(max_depth, depth)

    if x < 10 or y < 10:
        return x * y

    n = max(x.bit_length(), y.bit_length())
    half = n // 2

    high1, low1 = x >> half, x & ((1 << half) - 1)
    high2, low2 = y >> half, y & ((1 << half) - 1)

    z0 = karatsuba_model(low1, low2, depth + 1)
    z1 = karatsuba_model((low1 + high1), (low2 + high2), depth + 1)
    z2 = karatsuba_model(high1, high2, depth + 1)

    return (z2 << (2 * half)) + ((z1 - z2 - z0) << half) + z0


# ============================================================
# Coverage Definitions
# ============================================================

def get_size_bin(val):
    if val == 0: return 0
    return min(val.bit_length() // 4, 4)

@CoverPoint("karatsuba.x_size",
            xf=lambda x, y: get_size_bin(x),
            bins=[0,1,2,3,4])
@CoverPoint("karatsuba.y_size",
            xf=lambda x, y: get_size_bin(y),
            bins=[0,1,2,3,4])
@CoverCross("karatsuba.cross_xy_size",
            items=["karatsuba.x_size", "karatsuba.y_size"])
@CoverPoint("karatsuba.special",
            xf=lambda x, y: (x, y),
            bins=[(0,0),(0,1),(1,0),(1,1),(2**16-1,2**16-1)])
@CoverPoint("karatsuba.pattern",
            xf=lambda x, y: "equal" if x==y else "power2" if (x&(x-1)==0) else "random",
            bins=["equal","power2","random"])
def sample_coverage(x, y):
    pass


# ============================================================
# Recursion Depth Coverage (custom)
# ============================================================

recursion_coverage = {
    "shallow": 0,
    "medium": 0,
    "deep": 0
}

def sample_recursion(depth):
    if depth <= 1:
        recursion_coverage["shallow"] += 1
    elif depth <= 3:
        recursion_coverage["medium"] += 1
    else:
        recursion_coverage["deep"] += 1


# ============================================================
# TEST 1: Directed + Random Testing
# ============================================================

@cocotb.test()
async def test_full_coverage(dut):
    global max_depth

    # -------------------------------
    # Directed special cases
    # -------------------------------
    special_cases = [
        (0,0),(0,1),(1,0),(1,1),
        (2**16 - 1, 2**16 - 1)
    ]
    dut.start.value = 0
    for x, y in special_cases:
        max_depth = 0
        dut.x.value = x
        dut.y.value = y

        await Timer(100, units="ns")

        expected = karatsuba_model(x, y)
        sample_coverage(x, y)
        sample_recursion(max_depth)

        assert int(dut.out.value) == expected

    # -------------------------------
    # Cross coverage driven tests
    # -------------------------------
    sizes = [0,4,8,12,16,32,64]

    for xs in sizes:
        for ys in sizes:
            x = random.randint(0, 2**xs - 1) if xs > 0 else 0
            y = random.randint(0, 2**ys - 1) if ys > 0 else 0

            max_depth = 0

            dut.x.value = x
            dut.y.value = y

            await Timer(100, units="ns")

            expected = karatsuba_model(x, y)
            sample_coverage(x, y)
            sample_recursion(max_depth)

            assert int(dut.out.value) == expected

    # -------------------------------
    # Random stress testing
    # -------------------------------
    for _ in range(5000):
        x = random.randint(0, 2**16 - 1)
        y = random.randint(0, 2**16 - 1)

        max_depth = 0

        dut.x.value = x
        dut.y.value = y

        await Timer(100, units="ns")

        expected = karatsuba_model(x, y)
        sample_coverage(x, y)
        sample_recursion(max_depth)

        assert int(dut.out.value) == expected
    # Force missing cross bins
    corner_cases = [
        (0, 2**16 - 1),   # (0,4)
        (1, 0)            # (1,0)
    ]

    for x, y in corner_cases:
        dut.start.value = 0
        dut.x.value = x
        dut.y.value = y

        await Timer(100, units="ns")

        expected = karatsuba_model(x, y)
        sample_coverage(x, y)
        sample_recursion(max_depth)

        assert int(dut.out.value) == expected
    # Force deep recursion
    deep_cases = [
        (2**16 - 1, 2**16 - 1),   # max values
        (2**15, 2**15),           # power of 2
        (2**16 - 1, 1),
        (1, 2**16 - 1)
    ]

    for x, y in deep_cases:
        dut.start.value = 0
        dut.x.value = x
        dut.y.value = y

        await Timer(100, units="ns")

        max_depth = 0
        expected = karatsuba_model(x, y)

        sample_coverage(x, y)
        sample_recursion(max_depth)

        assert int(dut.out.value) == expected

# ============================================================
# TEST 2: Coverage Report
# ============================================================

@cocotb.test()
async def report_coverage(dut):
    dut._log.info("========== FUNCTIONAL COVERAGE ==========")
    coverage_db.report_coverage(dut._log.info, bins=True)

    dut._log.info("========== RECURSION COVERAGE ==========")
    total = sum(recursion_coverage.values())
    for k, v in recursion_coverage.items():
        pct = (v / total * 100) if total else 0
        dut._log.info(f"{k}: {v} hits ({pct:.2f}%)")