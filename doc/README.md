# RP Lock-in+PID Harmonic HF — documentation

Documentation of `lock_in+pid_harmonic_hf` **v2.3.22** (package 2.3.22-27, branch `master`, Ecosystem 2.0, FPGA built
with Vivado 2020.1; the FPGA is the one of v2.3.14 … v2.3.20, v2.3.21 and v2.3.22 change only the web page): the App
`lock_in+pid_harmonic` 2.3.32 with a harmonic modulation of 63.6 Hz to 1.04 MHz.
Back to the [project README](../README.md) · [CHANGELOG](../CHANGELOG.md).

New in v2.3.21 (the Ramp Controller of `lock_in+pid_plus` 2.2.0, as `lock_in+pid_harmonic` 2.3.31): the *Ramp
Controller* of the web page sets the ramp by period (steps, or the whole period in `s` / `ms`) or by frequency /
amplitude / offset, and *Lock osc. screen* shows the rising half of a triangle (one period of a sawtooth) and turns a
time zoom of the scope into new ramp limits: [Usage.md](Usage.md#ramp-controller), formulas in
[App.md](App.md#ramp-generator-scan). *Reset zoom* with Scan floor and a triangle alternates whole period / rising half
([Usage.md](Usage.md#reset-zoom-whole-period--rising-half)); with harmonic mod. it still gives one period of the HF
modulation. The *Force X* of the server is applied once ([Structure.md](Structure.md#time-window-of-the-plot-and-force-x)).

New in v2.3.22 (from `lock_in+pid_plus` 2.2.1): a POST retried after a timeout of nginx no longer undoes a time window
set meanwhile (the second click of *Reset zoom*), the page checks that the server took the window it sent and sends it
again if not, and a value changed back during a POST in flight is kept
([Structure.md](Structure.md#a-post-retried-after-a-timeout-and-a-window-that-the-server-does-not-take-v2322)).

| Document | Contents |
|---|---|
| [App.md](App.md) | The instruments of the App and their technical data: frequencies, filters, gains, ranges, time spans, measured lock performance; what is different from `lock_in+pid_harmonic` |
| [Usage.md](Usage.md) | The web interface panel by panel, the procedures (scan, lock-in, close and check a lock, lock at 104 kHz), configs, HF notes |
| [Structure.md](Structure.md) | How the web page, the server (nginx + `controllerhf.so`) and the FPGA work together; block diagrams of the FPGA |
| [FPGA.md](FPGA.md) | Register map of the lock module and of the oscilloscope, bit fields and selector values |
| [Remote.md](Remote.md) | Remote control over HTTP (`/lock`, `/osc`, `/data`) with Python (`control_finn.py`) examples; known issue of `POST /data`; tools and scripts on the board |
| [Devel.md](Devel.md) | Source tree, requirements, building (C, `c/` tools, FPGA), tests, installation |

Design notes kept with the sources (`lock_in+pid_harmonic_hf/doc/`):

- [`lock_control.md`](../lock_in+pid_harmonic_hf/doc/lock_control.md): the lock control (`lock_control` /
  `lock_status`, state machine in the FPGA, locking from Python).
- [`lock_capture.md`](../lock_in+pid_harmonic_hf/doc/lock_capture.md): *Capture Lock* and *Fire on click*.

Screenshots of the web interface are in the hidden folder `.Usage/`, and the figures of the remote control in
`.Remote/` (names starting with `h_`: taken with `lock_in+pid_harmonic`, identical interface).
