# Pipeline registers of v2.3.13 (FPGA timing) — added latencies

Port of the timing work of `lock_in+pid_harmonic` v2.3.19 (its `doc/lock_latency.md` explains the method; the user
allowed adding latency on 2026-10-12). Up to v2.3.12 the FPGA did not meet timing at 125 MHz because of long
combinational chains of the loop (generator ROM → product → LPF / bypass → gain → saturation → PID / scope / lock
control; PID sum → ctrl → out mux → DAC). v2.3.13 registers those chains. **The behaviour is the one of v2.3.12 except
for the latencies below** (checked bit by bit in simulation, `test/lock_latency_sim.sh`).

## Latency of each signal with respect to v2.3.12

| Signal | Added | ns |
|---|---|---|
| Generator outputs (`sin_ref`, `cos_ref`, `cos_1f..3f`, `harmonic_trig`) | +1 | 8 |
| References into the multipliers of the lock-in | +2 (generator + 1) | 16 |
| `Xo`, `Yo`, `F1o..F3o` from the product (register after the first LPF stage + output register; `shift_sat14`) | +2 | 16 |
| `X_28..F3_28` (bus) | +1 | 8 |
| PID outputs (`pidA_out`, `pidB_out`), from the PID input | +1 | 8 |
| `out1`, `out2` (DAC), for everything that goes out (out mux and modulation, both registered before the sum) | +1 | 8 |
| LOCK MODE loop `in1` → Y → PID A → `ctrl_A` → `out1` | +4 | 32 |

**Phase of the lock-in.** Unlike `lock_in+pid_harmonic` v2.3.19, the references reach the lock-in 1 clock later than
the outputs: the generator and the DAC outputs got 1 register each, so the modulation that goes out and comes back
(DAC → system → ADC) is 2 clocks later and the reference too: **the measured phase does not change** (in
`lock_in+pid_harmonic` 2.3.19 it changes by −360° · f · 8 ns, which here would be −3° at 1.04 MHz). In the simulation this is the case "in1 delayed 2
clocks": every lock-in signal is then exactly the old one delayed 2 + its latency.

Blocks rewritten without latency (same values): gain + saturations of `Xo..F3o` (`shift_sat14`), `sat14` (mask instead of barrel shifter), integrator of the PID
(ISR shift in parallel with the saturation), `sum_div` of the second LPF stage in a register (a change of `lpf_*`
reaches it 1 clock later). The PID derivative with `DSR` > 0 samples a delayed input at other points (same behaviour,
other sampling phase).

## Verification

`test/lock_latency_sim.sh` (xsim, the `lock.v` of the working tree side by side with the one of v2.3.12): all checks
bit exact; `test/lock_bus_read_sim.sh` and `test/lock_ctrl_sim.sh` pass.

## Timing (Vivado 2020.1, post-route)

| | v2.3.12 | v2.3.13 |
|---|---|---|
| WNS | -9.281 ns | -0.945 ns |
| TNS | -7165.999 ns | -213.267 ns |
| Failing endpoints | 4146 | 714 |

Worst slack per group (ns):

| Group | v2.3.12 | v2.3.13 |
|---|---|---|
| scope muxes | -9.281 | -0.494 |
| DAC registers | -8.698 | -0.128 |
| adc_dat (digital loop / scope input) | -8.242 | -0.799 |
| bus copies *_rd | -8.424 | -0.339 |
| PID A | -7.782 | -0.945 |
| PID B | -7.257 | -0.871 |
| lock_ctrl | -6.010 | > 0 |
| rest of the lock module | -4.261 | -0.441 |
| LPF | -2.822 | -0.695 |
| ramp | -2.060 | > 0 |
| generator | -0.634 | > 0 |
| oscilloscope | -3.309 | > 0 |
| bus read (sys_rdata) | -2.988 | > 0 |
| other | -1.537 | -0.170 |

What still fails is small: the recursive loops of the LPF and of the PID integrator (they cannot be pipelined
without changing the filter), the input path `in1` → PID mux → set point subtraction → multiplier, quasi-static
configuration registers, and paths of the oscilloscope outside the lock module.
