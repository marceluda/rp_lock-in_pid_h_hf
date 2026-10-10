
# Devbuild  changes


v0.3.1
- FIXED bug on PID derivative constant label

v0.3.2
- ADDED long time-range signal storing (by local script)

v0.3.3
- ADDED digital pin for ramp_scan externa synchronization

v0.3.4
- ADDED Sawtooth waveform for Ramp intrument
- ADDED larger decimation for Scope instrument: up to 64 seconds time range

v0.3.8
- ADDED support for ecosystem 2.0 of RedPitaya (fpga.sh, fpga.bif, fpga.bit.bin built with bootgen)
- FIXED APP name in the root Makefile (lock_in+pid_harmonic_hf)
- Ecosystem 2.0 fixes, ported from rp_lock-in_pid_h v0.3.10
  - FIXED E3: parameters are sent in chunks of at most 600 B (only changed and finite values, with retries)
  - App status is probed with POST before polling /data; the App is started robustly (stop + 1.5 s + start + verification)
  - ADDED "took control" detection when another client claims the board
  - ADDED save and restore of the App state in the browser
  - FIXED Config -> load; own localStorage key for this App
  - reload_fpga is disabled in Ecosystem 2.0 (nginx returns 501)
  - Cache-Control (no-cache) for index.html in nginx.conf
  - main.c (GUI_XMIN/XMAX from rp_main_params) and Makefile updated for Ecosystem 2.0 (fpga.bit.bin, -lm -lpthread, fpga.sh executable)
- Ported from rp_lock-in_pid_h2 v0.4.1
  - Restart after "took control" restores the saved values when the intruder is the same App
  - ADDED cautious mode: if /get_client_id is slow or fails, /data is not requested until the board answers fast again
- FIXED second of two quick consecutive changes being lost while a POST was in flight
- FIXED indicators (R, X, Y, phase, scope) frozen by the edit timer after leaving a field
- FIXED Enter with an out-of-range value sending two POSTs (Enter is prevented, forms use novalidate)
- FIXED mouse wheel: no longer sends single_btn, and SHIFT + wheel uses the right sign
- FIXED duplicated POST when using the mouse wheel on a focused field

v0.3.9
- FIXED endless loop of POSTs (~15/s, it exhausted the nginx file descriptors) after loading a config of another App
  or an incomplete one: the missing keys left NaN in the parameters, which counted as a change that was never sent
  - Values that are not finite numbers (NaN, undefined, null, Infinity) are never a pending change
  - Config -> load keeps the current value of the keys missing in the config (no empty selectors)
  - The selectors never copy NaN to the parameters
  - Guard in sendParams(): no POST without a real change less than 200 ms after the previous one, and at most
    10 POST/s (a warning is logged in the console)
  - The display tolerates missing values (lock_error_mean, lock_stream_rate)

v2.3.10
- First version of the 2.x series (branch devel2.0): the same changes as lock_in+pid_harmonic v2.3.10 +
  v2.3.11 (see its CHANGELOG for the details of each one), plus the bus read fix of its v2.3.17. Everything
  that makes this App "HF" is kept: harmonic modulation period of 120 table points (gen_mod_h.v with
  data_sin1.dat / data_cos1..3.dat, f = 125 MHz / (120 * (gen_mod_hp + 1)) -> 1.04 MHz .. 63.6 Hz),
  gen_mod_phase 0..119 (C, UI, config_tool.py), PERIOD_LEN = 120 in the UI, saved configs not migrated
  from the shared 'lockConfig' key
- CHANGED the FPGA design is built with Vivado 2020.1 (RedPitaya-FPGA project structure, project v0.94,
  model Z10 = STEMlab 125-14): lock_in+pid_harmonic_hf/fpga is the fpga/ of lock_in+pid_harmonic with the
  HF modulation generator; the Vivado 2015.2 design is kept untracked in lock_in+pid_harmonic_hf/fpga_old_2015.2
- CHANGED the oscilloscope is the RedPitaya 2.0 one: the controller unlocks the trigger (0x94) before
  every acquisition and detects its end with conf bit 4; 20-bit decimation (time range up to ~68 s);
  samples keep the 14 ADC bits (controller, c/osc, c/stream_tcp_osc_cmd, py/hugo.py)
- FIXED corrupt bus reads of live signals (in1, oscA, out1, PID...: a mix of bits of two values, 2-4 % of the
  reads in lock_in+pid_harmonic): lock.v loads sys_rdata only while sys_ren and holds it, the read-only wires
  are read from registered copies (*_rd) and the frozen copies (*_reg) are held during a read; multicycle
  constraint on sys_rdata. config_tool.py generates the new read mux. xsim test/lock_bus_read_sim.sh: PASS
  (v0.3.9: 2000/2000 reads with sys_rdata changing < 8 ns before the PS sampling edge)
- FIXED streaming (c/stream_tcp_osc_cmd segfault, repeated data, first Start without data, E3, leaving the
  App while streaming, corrupt end, check_streaming), c/lock unsigned registers, /lock and /osc `?name`
  without `=`, c/ tools cross compiled by the App Makefile (`make c_tools`), time scale after Restart,
  a Single click made during a POST no longer lost
- ADDED cautious mode v2 (a single slow /get_client_id is retried at once; slow answers overlapping our own
  POST are not measured; checks 1 s apart), the yaxis2 zoom of the R/phase plot (from lock_in+pid_harmonic)
- REMOVED the DEBUG and RELOAD flavours (controllerhf_dbg.so, controllerhf_rld.so, src/main_*.so_.c, the sed
  edits of src/main.h / src/main.c in the Makefile); only the App itself is built and packaged
- CHANGED Makefile upload targets (as lock_in+pid_harmonic v2.3.15): `make upload RPIP=...`, rw of the OS
  (2.0 and 0.9x), check_rpip, fpga.sh keeps its exec bit; settings.sh loads Vivado 2015.2 only if present
