
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

v2.3.11
- Port of the lock / web UI / controller / remote control changes of lock_in+pid_harmonic v2.3.12 to v2.3.17 (see
  its CHANGELOG for the details of each one; the "v2.3.12".."v2.3.17" in the comments of the sources are those of
  lock_in+pid_harmonic). One step, as they were made and tested there. New FPGA image. Kept from v2.3.10: everything
  HF (120-point modulation period, gen_mod_phase 0..119, PERIOD_LEN = 120, configs not migrated)
- CHANGED the lock sequence runs entirely in the FPGA (lock_ctrl.v state machine OFF / ARMED / LOCKED): lock_control
  (0x18) is command + configuration, never rewritten by the FPGA; 0x1C is now lock_status (read only, replaces
  lock_feedback): [0] armed, [1] locked, [4:2] effective ramp / PID A / PID B enables, [15:8] lock counter. The C
  controller writes lock_control only when the user changes it and reads the status on every request; the web UI
  shows OFF / ARMED / LOCKED, Trigger Lock / Lock Now stay pressed while requested and a second click releases.
  See lock_in+pid_harmonic_hf/doc/lock_control.md
- CHANGED lock_ctrl.v registers its trigger inputs for timing (as lock_in+pid v2.2.6): ramp floor trigger (counter
  loaded with 1 one clock later: Time trigger in the same clock as before) and the level / time comparisons (Level
  trigger 1 clock = 8 ns later). The lock-in core (demodulation, filters) is not changed
- CHANGED lock time trigger: 32 bits end to end (up to 2^32 - 1 ticks = 34.36 s)
- ADDED Capture Lock (each lock request captures the closing of the loop in the scope, Ext Trig = "Lock control
  trig", frozen until Auto / Single) and Fire on click. See lock_in+pid_harmonic_hf/doc/lock_capture.md
- FIXED "Choose from graph" with any zoom / offset / time units; a click sets only the value of the trigger type;
  the "Auto-zoom" option was removed
- ADDED Time trigger / Level trigger fields with units (16.58 ms, 20 s, 0.1 V, 120 mV...); an emptied number field
  is never sent as 0
- FIXED Config -> load applies the scope window in the right units (seen by testAgent on v2.3.10 with the page in us)
  and does not send forcex_flag / time_units / time_range / gui_x* nor the read-only params; the full config is sent
  in chunks with the window applied from the answer of the last one
- FIXED every POST reset the scope (a Single waiting for its trigger was disarmed); AUTO after a lock capture; aborted
  auto-set; zoom-out right after a change of time units
- CHANGED PID integrator divider label "6 us" -> "65 us"; descriptions of X / Y
- ADDED HTTP remote control on Ecosystem 2.0: /osc writes TrgUnlock (0x94) and c/osc addresses registers by index;
  register ranges in config_tool.py / c/lock.txt; resources/remote_control/http_version/control_finn.py of
  lock_in+pid_harmonic v2.3.17 (scope_stop() / scope_auto(): the web scope is stopped before /osc acquisitions,
  minimal POST /data sent in one packet, WebScopeNotStopped, host resolved once / resolve()), with
  PERIOD_LEN = 120: set_freq() / set_freq_hz() / get_freq() / set_phase() use the HF period (1.04 MHz .. 63.6 Hz,
  phase 0..119); example_usage.py with HF values (gen_mod_hp 5367 = 194 Hz, set_freq(20) = 49.6 kHz,
  set_phase(30) = 90 deg) and the ramp of test_files/lock_in+pid_harmonic_hf__lock_mode.json
- ADDED py/lock_from_registers.py (arm / lock now / release / status writing only FPGA registers); py/hugo.py
  lock_status and osc.acq_done(); control_hugo.py launch_lock() / lock_now() / release_lock() / lock_status()
- Tests (lock_in+pid_harmonic_hf/test/): xsim lock_ctrl_sim.sh and lock_bus_read_sim.sh; node lock_ctrl_ui_sim.js,
  lock_capture_ui_sim.js, trig_input_units_sim.js, config_load_window_sim.js, trig_from_graph_sim.js;
  auto_set_c_sim/run.sh (controller C on the PC)

Documentation (after v2.3.11, not a new version)
- ADDED doc/: App.md (instruments, technical data with the HF modulation of 120 points, differences with
  lock_in+pid_harmonic, lock results at 49.6 kHz and 104.2 kHz), Usage.md (web interface, procedures, lock at
  104 kHz, HF notes, screenshots in doc/.Usage/), Structure.md (layers and FPGA block diagrams in Mermaid),
  FPGA.md (register map checked against the RTL), Remote.md (HTTP remote control with control_finn.py, HF notes),
  Devel.md (build, tests, installation). doc/README.md is now the index of doc/. README updated (screenshot in
  .README/, documentation table, installation, build)

v2.3.12
- Port of the minor fixes of lock_in+pid_harmonic v2.3.18 (no FPGA change: the image is the one of v2.3.11, only
  comments of lock.v changed; the "v2.3.18" in the comments of the sources is that of lock_in+pid_harmonic)
- FIXED lock trigger registers written from Python (py/lock_from_registers.py --time/--level/--sw, control_finn.py):
  lock_trig_val / lock_trig_time / lock_trig_sw follow the rule of lock_control: the C writes each one only when its
  parameter changes and copies a value written from outside to the parameter (the page shows it and keeps it; before,
  it was not shown and the page value was written back at the next change of any lock parameter)
- FIXED Config -> load sent read-only parameters of the server (meas_*, lock_X/Y/F1..F3, lock_lock_status,
  lock_lock_control, trig_delay, ...): skipped (server_ro_keys)
- FIXED Single mode made no request at all after its acquisition (a bazaar?stop or another client was not noticed,
  the lock label was not refreshed): 1 s polling in Single; an AGAIN answer starts the fast polling only while a
  Single click waits for its acquisition
- FIXED console "Capture Lock: ended by , scope settings restored" (the reason is given); mouse wheel on Ramp period /
  limits, PID, modulation and lock trigger fields updates the text below them (tau/f...); X+ of the plot range up to
  68.72 s (it stopped at 10 s)
- FIXED py/lock_from_registers.py: --time clamped to 0..2^32-1 ticks with a message (40s gave OverflowError), ns/us
  accepted, --sw 0..15, docstring (--sw is "Signal for trigger", options 6-8 are 0)
- FIXED example_usage.py: the Lock cell restores the lock-in and PID A of lock_in+pid_harmonic_hf__lock_mode.json
  (gen_mod_hp 20, 49.6 kHz; RESTORE_LOCK_MODE = False prints a warning instead), and "save data" ends with
  rp.scope_auto() (the script left the scope of the page in Single)
- FIXED upload_app.sh: rw script of the OS as the Makefile (/opt/redpitaya/sbin/rw or /boot/sbin/rw), -w removed
  {index.html,js.css} (js,css), fpga.sh exec bit
- CHANGED c/streaming.c closes the file descriptors inherited from the nginx worker; its "Finishing streaming"
  message no longer ends with ": Success" (perror with errno 0); c/stream_tcp_osc_cmd runs with nice -10 and
  locked memory (fewer lost samples at decimation 128 with activity on the board; STREAM_NICE=<n> changes it)
- CHANGED AUTO: minimum window 1 us (was 100 ns: with noise only it gave 0...139 ns)
- CHANGED texts: "Signal for trigger" 6-8 "0 (sqXo)"..; ctrl_B = pidB_out + ramp_B (lock.v, fpga_lock.h, main.c,
  config_tool.py); 20-bit decimation in src/fpga.h and fpga/README.md; resources/README.md (read with name= or name);
  doc/lock_control.md and doc/Remote.md (trigger registers written from outside)
- Tests: test/minor_ui_sim.js (new), lock_capture_ui_sim.js part 7 (Single polling), config_load_window_sim.js
  (no read-only key sent), auto_set_c_sim parts 4 and 5

v2.3.13
- FPGA timing (port of lock_in+pid_harmonic v2.3.19, the user allowed adding latency): WNS -9.281 -> -0.945 ns,
  TNS -7166 -> -213 ns, 4146 -> 714 failing endpoints. Pipeline registers in the long combinational chains of the
  loop; same behaviour except for the latencies (bit by bit in simulation against v2.3.12). Details and latency of
  each signal: lock_in+pid_harmonic_hf/doc/lock_latency.md
- CHANGED (FPGA, added latency, 8 ns per clock): generator outputs +1 (gen_mod_h wrapper with registered outputs);
  Xo, Yo, F1o..F3o +2; bus X_28..F3_28 +1; PID outputs +1; out1/out2 +1. LOCK MODE loop +32 ns
- CHANGED (FPGA): the references reach the multipliers of the lock-in 1 clock later than the outputs, so the phase
  measured through DAC -> system -> ADC does not change (without it: -3 deg at 1.04 MHz; lock_in+pid_harmonic 2.3.19
  does not have this compensation)
- CHANGED (FPGA, same values): shift_sat14 (gain + saturations of Xo..F3o), sat14 without barrel shifter, PID
  integrator with the ISR shift in parallel, sum_div of the second LPF stage in a register
- CHANGED page title (h2.page-title) and <title> get the version of info/info.json at build time (Makefile)
- ADDED test/lock_latency_sim.sh + test/lock_latency_tb.sv (xsim, 406 checks against v2.3.12)

v2.3.14
- Port of lock_in+pid_harmonic v2.3.21 (Reset zoom), v2.3.22 (mouse wheel) and v2.3.23 (slow scans, FPGA lock_ctrl.v);
  see its CHANGELOG for the details and the board tests. New FPGA image. "v2.3.2x" in the comments are those of
  lock_in+pid_harmonic.
- ADDED Reset zoom: X from t = 0 to one period of the ramp (Ext Trig = Scan floor / Scan ceil: sawtooth
  (high-low+1)*(step+1), triangle 2*(high-low)*(step+1) ticks), one period of the HF modulation (harmonic mod.:
  120*(hp+1) ticks, PERIOD_LEN) or one whole memory at the current Dec (other Ext Trig); periods >= 1.5 s: 0.98 x the
  period (at least 50 ms before the next trigger). Y to -1..1 V (raw mode -8192..8192). During a lock capture it first
  ends it (as AUTO); the Raw Mode button rescales Y
- CHANGED the "Square mod." Ext Trig is no longer in the trigger menu (not implemented in this App: always 0 in the
  FPGA); also removed from resources/config_tool.py, labelled "0 (Square mod.)" in control_finn.py
- ADDED mouse wheel on the scope: no key zooms both axes, SHIFT only time (cursor ew-resize), ALT only the Y axes
  (cursor ns-resize, no POST); X window 20 ns .. 68.7 s; local zoom during a lock capture; xmin/xmax sent without
  rounding to 2 decimals (a fast zoom from s to ms sent 0/0)
- FIXED slow scans (windows >= 1.5 s): new long-acquisition reader in src/worker.c (rp_osc_long_rd_*: never a sample
  of an older lap of the scope memory or from before the history, adc_we_cnt register 0x2C, OK only when complete,
  ends at the window of the user); Capture Lock holds the lock request until the scope has enabled its trigger
  (lock_request_* in src/lock.c, the POST answers at once); read-only params scope_gen, scope_acq_state,
  scope_acq_gen, sig_gen (PARAMS_NUM 208 -> 212); page: capture recognised by sig_gen, partial traces drawn,
  banners, real "LOCKED but not captured"; Reset zoom clears stale traces
- FIXED (FPGA, lock_ctrl.v): the time trigger counter is valid (cnt_ok) only from a floor of a ramp that has been
  running since then (new input ramp_run = ramp_enable & ~ramp_reset) and it saturates instead of wrapping every
  34.4 s: a time (or level+time) request armed after a stop fires at the next floor + time, never mid-scan. Adapted
  to the registered trigger inputs of this App (v2.3.11): cnt_ok is set with ramp_trigger_r and delayed once for
  level+time; with the ramp running the lock fires in the same clock as before. time_eq is built from lock_trig_time-1
  and two flags in registers (the saturation inside cnt_next would lengthen the comparison path, -0.26 ns in
  lock_in+pid 2.2.9); same value every clock (lock_ctrl_tb.v checks it against cnt_next == lock_trig_time)
- example_usage.py: note about time / timeout for slow ramps
- Tests: new test/reset_zoom_sim.js (30, 120-point period), test/plot_wheel_sim.js (59), test/ramp_mod_period_sim.sh
  (ramps and 120*(hp+1), 11); lock_capture_ui_sim.js section 8 (79), auto_set_c_sim sections 6-9 (44),
  lock_ctrl_tb.v cases 16-19 and the time_eq monitor (46)
