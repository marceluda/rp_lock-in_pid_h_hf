# RP Lock-in+PID Harmonic HF — documentation

Documentation of `lock_in+pid_harmonic_hf` **v2.3.11** (branch `devel2.0`, Ecosystem 2.0, FPGA built with
Vivado 2020.1): the App `lock_in+pid_harmonic` 2.3.17 with a harmonic modulation of 63.6 Hz to 1.04 MHz.
Back to the [project README](../README.md) · [CHANGELOG](../CHANGELOG.md).

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
