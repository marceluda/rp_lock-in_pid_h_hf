# Red Pitaya Lock-in+PID Application with HARMONIC High Frequency modulation

This started being a striped version of [lock-in+PID](https://github.com/marceluda/rp_lock-in_pid) project. Now it incorporated some new features that make it another App.

This High Frequency version is a copy of [Lock-in+PID Harmonic](https://github.com/marceluda/rp_lock-in_pid_h) with only one change: **The harmonic motulation signal frequencies can be set from 60 Hz to 1 MHz**.

[![Example of usage](http://img.youtube.com/vi/330eYE75MYQ/0.jpg)](http://www.youtube.com/watch?v=330eYE75MYQ "Fast demosatration of usage")


## Features

- Lock-in amplifier
- in-phase and quadrature Demodulation
  - Demodulation for arbitrary phase
  - Demodulatión for double and triple frequency
- Two PID filters, for loop back stabilization
- Ramp/Scan controller for response analysis
- Lock control for automatic scan-stop / PID start
- Streaming system for continued acquisition of two channels
- Remote control through HTTP API
 

**New Interface for lock-in R & Phase** :


[![New iface](http://img.youtube.com/vi/DzSK8IQkUE4/0.jpg)](http://www.youtube.com/watch?v=DzSK8IQkUE4 "New R-phase interphase")


## Lock-in and PID application for RedPitaya environment

This is an application built for the [Red Pitaya STEMlab 125-14](https://www.redpitaya.com/) board (RP).
The board is closed-hardware and open-software. You can buy the board and build your own software.

If you have a RP board you can install the **Lock-in+PID** application
by copying the `lock_in+pid_harmonic_hf` folder (that comes with this tar/zip file) to the
`/opt/redpitaya/www/apps` folder (inside the RP).

For more information about installing procedure, refer to:
https://marceluda.github.io/rp_lock-in_pid/TheApp/install/


## Version 2.3.x (Ecosystem 2.0)

Current version: **2.3.10** (branch `devel2.0`).

This version is **based on the 0.3.x series (v0.3.9), with the FPGA design built in Vivado 2020.1**,
using the project structure of [RedPitaya-FPGA](https://github.com/RedPitaya/RedPitaya-FPGA)
(project `v0.94`, model `Z10`), the same port done in
[rp_lock-in_pid_h](https://github.com/marceluda/rp_lock-in_pid_h) v2.3.x (its v2.3.10 and v2.3.11, plus
the bus read fix of its v2.3.17). It is intended for the Red Pitaya **Ecosystem 2.0** (e.g. `RedPitaya_OS_2.04`).
The 0.3.x series (branch `master`, FPGA with Vivado 2015.2) is the version for the 0.9x / 1.0 ecosystems.

- HF: the harmonic modulation has a period of 120 table points (lock_in+pid_harmonic: 2520), so its
  frequency is 125 MHz / (120 * (`gen_mod_hp` + 1)) = 1.04 MHz .. 63.6 Hz, and `gen_mod_phase` is 0..119.
- FPGA: `lock_in+pid_harmonic_hf/fpga/` (Vivado 2020.1, see
  [lock_in+pid_harmonic_hf/fpga/README.md](lock_in+pid_harmonic_hf/fpga/README.md)). Oscilloscope of the
  Ecosystem 2.0 (trigger lock, decimation widened to 20 bits), bus reads of the lock module held during the
  read. Registers of the lock module unchanged.
- Only the App itself is packaged (the `_DEBUG` and `_RELOAD` flavours were removed).
- See the [CHANGELOG](CHANGELOG.md).


# Development

To build of modify the App you need a linux development environment with:
  - Vivado 2020.1 (FPGA and `bootgen`; `lock_in+pid_harmonic_hf/fpga/Makefile` loads
    `/tools/Xilinx/Vivado/2020.1/settings64.sh` by itself, override with `VIVADO_SETTINGS=...`)
  - gcc-linaro-4.9-2015.02-3-x86_64_arm-linux-gnueabihf (installed on `/opt/linaro/gcc-linaro-4.9-2015.02-3-x86_64_arm-linux-gnueabihf/`)
  - (the 0.3.x series, branch `master`, used Vivado 2015.2)


Run on terminal:

```bash
source settings.sh
make
```

Or form App folder `lock_in_mtm` :

```bash
source ../settings.sh
```


and then...

For web controller building:

```bash
make app
```

For FPGA implementation:

```bash
make fpga
```


For tar.gz packaging

```bash
make tar
```

For cleaning:

```bash
make clean       # clean all
make clean_app   # clean only C objects
make clean_fpga  # clean only FPGA implementation temp files and .bin
```


# Upload App to Red Pitaya device

UnZip / UnTar the App folder. Execute from terminal:

```bash
./upload_app.sh rp-XXXXXX.local
```

Replace `rp-XXXXXX.local` by your RP localname or IP address

Or, from the App folder of the sources (builds `target/` first):

```bash
make upload RPIP=rp-XXXXXX.local        # whole App
make upload_html RPIP=rp-XXXXXX.local   # only index.html, js, css
```

Then stop and start the App (or open it from the menu) so that the new controller and FPGA are loaded.

Also, you can use your own SSH client and upload the lock_in+pid_harmonic_hf folder the the
RedPiaya folder: `/opt/redpitaya/www/apps`
