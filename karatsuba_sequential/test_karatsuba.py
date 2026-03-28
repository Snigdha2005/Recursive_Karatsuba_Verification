import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge

# ================================
# Helper: Apply input transaction
# ================================
async def apply_input(dut, x, y):
    dut.x.value = x
    dut.y.value = y
    dut.start.value = 1

    await RisingEdge(dut.clk)

    dut.start.value = 0


# ================================
# Helper: Wait for pipeline
# ================================
async def wait_latency(dut, cycles=20):
    for _ in range(cycles):
        await RisingEdge(dut.clk)


# ================================
# Basic test
# ================================
@cocotb.test()
async def test_basic(dut):

    # Create clock (10ns period)
    clock = Clock(dut.clk, 10, units="ns")
    cocotb.start_soon(clock.start())

    dut.start.value = 0
    dut.x.value = 0
    dut.y.value = 0

    # Wait few cycles for reset-like stabilization
    for _ in range(5):
        await RisingEdge(dut.clk)

    test_vectors = [
        (3, 5),
        (10, 20),
        (1234, 5678),
        (2**16 - 1, 2**16 - 1)
    ]

    for x, y in test_vectors:
        await apply_input(dut, x, y)

        await wait_latency(dut, cycles=40)

        expected = x * y
        result = dut.out.value.integer

        assert result == expected, \
            f"FAILED: {x} * {y} = {expected}, got {result}"


# ================================
# Random test
# ================================
@cocotb.test()
async def test_random(dut):

    clock = Clock(dut.clk, 10, units="ns")
    cocotb.start_soon(clock.start())

    dut.start.value = 0

    for _ in range(5):
        await RisingEdge(dut.clk)

    import random

    NUM_TESTS = 10000

    for _ in range(NUM_TESTS):

        x = random.getrandbits(len(dut.x))
        y = random.getrandbits(len(dut.y))

        await apply_input(dut, x, y)

        await wait_latency(dut, cycles=40)

        expected = x * y
        result = dut.out.value.integer

        assert result == expected, \
            f"FAILED: {x} * {y} → RTL: {result}, Expected: {expected}"
