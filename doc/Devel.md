# Development: building and modifying the App

How to build, modify, test and install `lock_in+pid_harmonic_hf` v2.3.15 (branch `master`). The
project is a copy of `rp_lock-in_pid_h` (`lock_in+pid_harmonic` 2.3.24) with the HF modulation generator; the
differences are listed in [App.md](App.md#what-is-different-from-lock_inpid_harmonic). The internal
structure is explained in [Structure.md](Structure.md) and the registers in [FPGA.md](FPGA.md).

- [Source tree](#source-tree)
- [Software requirements](#software-requirements)
- [Building everything](#building-everything)
- [Makefiles and targets](#makefiles-and-targets)
- [C controller (`controllerhf.so`)](#c-controller-controllerhfso)
- [Tools of `c/` (`lock`, `osc`, streaming)](#tools-of-c-lock-osc-streaming)
- [FPGA (Vivado 2020.1)](#fpga-vivado-20201)
- [Web interface (`index.html`)](#web-interface-indexhtml)
- [Registers and `config_tool.py`](#registers-and-config_toolpy)
- [Simulations and tests (`test/`)](#simulations-and-tests-test)
- [Installing on the board](#installing-on-the-board)
- [Versioning and packages](#versioning-and-packages)

## Source tree

```
rp_lock-in_pid_h_hf/
├── Makefile                 # all = App build + zip + tar into archive/
├── settings.sh              # environment for the C build (Vivado 2015.2 + Linaro)
├── _build_number            # BUILD_NUMBER=N (incremented by make clean_*), not versioned
├── README.md  CHANGELOG.md  LICENSE (GPL-3.0)  TODO.md
├── doc/                     # this documentation
├── archive/                 # built packages (*.zip, *.tar.gz), not versioned
├── resources/
│   ├── config_tool.py       # register table -> code generator (see below)
│   ├── doc_tool.py
│   ├── remote_control/http_version/   # control_finn.py, example_usage.py (HTTP API client)
│   ├── remote_control/shh_version/    # SSH client (deprecated)
│   ├── streaming/           # TCP receiver for the streaming (server.c, read_bin.py)
│   ├── process_web_download/, rp_cmds/, code_helpers/ (muxer generator, gen_sin_cos.py: tables of T = 120)
│   └── README.md            # streaming and remote control notes
└── lock_in+pid_harmonic_hf/    # the App (this folder is what is installed on the board)
    ├── Makefile             # controller, c tools, FPGA, target/, zip, tar, upload
    ├── index.html           # web interface (HTML + JS in one file)
    ├── css/  js/            # styles, jquery.mousewheel, js.cookie
    ├── info/info.json       # name and version shown by the Ecosystem; icon.png
    ├── nginx.conf           # extra HTTP endpoints (Lua): /lock, /osc, /streaming, ...
    ├── fpga.sh              # Ecosystem 2.0: loads fpga.bit.bin with fpgautil when the App starts
    ├── fpga.conf            # path of the .bit (Ecosystem 0.9x)
    ├── fpga.bit.bin, red_pitaya.bit, fpga.bit   # FPGA images (built)
    ├── controllerhf.so      # C controller (built, versioned)
    ├── src/                 # C controller sources
    │   ├── main.c / main.h  # parameter table, rp_set_params / rp_get_params / rp_get_signals
    │   ├── worker.c / .h    # scope worker thread, auto-set, measurements
    │   ├── fpga.c / fpga.h  # scope registers (0x40100000)
    │   ├── lock.c / .h, fpga_lock.c / .h   # lock registers (0x40600000)
    │   ├── calib.c, generate.c, fpga_awg.c, pid.c, fpga_pid.c   # from the original scope App
    │   └── Makefile
    ├── c/                   # tools run on the board: lock, osc, streaming, stream_tcp_osc_cmd
    │   ├── *.c, Makefile, lock.txt, osc.txt, load_bit.sh, stream_start.sh
    ├── py/                  # Python scripts run on the board (hugo.py, lock_from_registers.py, ...)
    ├── fpga/                # FPGA project (Vivado 2020.1, RedPitaya-FPGA structure)
    │   ├── Makefile  README.md  red_pitaya_vivado_Z10.tcl  synCheck.sh
    │   ├── rtl/rtl/         # common Red Pitaya RTL (classic/rp_scope_*.v modified by this App)
    │   ├── prj/v0.94/rtl/   # red_pitaya_top.sv, red_pitaya_ps.sv, lock.v, lock/*.v, lock/data_*.dat (HF tables)
    │   ├── prj/v0.94/{ip,sdc}, prj/barebones/ip, sdc/, brd/
    │   └── prj/v0.94/out/   # build products (not versioned)
    ├── doc/                 # design notes: lock_control.md, lock_capture.md (+ Doxygen setup)
    ├── test/                # simulations (xsim, node, native C)
    ├── upload_app.sh        # upload a package to a board through SSH
    └── target/              # staging folder for the packages (built, not versioned)
```

## Software requirements

| Tool | Version | Used for | Path on the development PC |
|---|---|---|---|
| Xilinx Vivado | **2020.1** | FPGA (synthesis, implementation, `bootgen`, xsim) | `/tools/Xilinx/Vivado/2020.1` (`VIVADO_SETTINGS`) |
| Xilinx Vivado (SDK) | 2015.2 (optional) | sourced by `settings.sh` **only if present** (v2.3.10); not needed for the C build | `/opt/Xilinx/Vivado/2015.2` |
| Linaro ARM toolchain | gcc-linaro-4.9-2015.02-3 (or 2014.11) `arm-linux-gnueabihf` | cross compiling the controller and the `c/` tools | `/opt/linaro/` |
| GNU make, zip, tar, sed | — | build and packaging | — |
| node.js | any recent (v22 used) | UI simulations in `test/` | — |
| gcc (PC) | — | `test/auto_set_c_sim` | — |
| Python 3 + numpy | — | `resources/config_tool.py`, remote control | — |

Vivado 2015.2 is not needed: `settings.sh` sources it only if `/opt/Xilinx/Vivado/2015.2/settings64.sh` exists
(as in the 0.3.x series); the C code is compiled with the Linaro toolchain (`CROSS_COMPILE=arm-linux-gnueabihf-`). Installation notes (kept from the README
of the 0.3.x series, tested on Ubuntu 16.04 at the time):

```bash
# development packages
sudo apt-get install make u-boot-tools curl xz-utils nano zip
# Linaro toolchain in /opt/linaro (settings.sh looks for 2015.02-3 or 2014.11)
TOOLCHAIN="http://releases.linaro.org/15.02/components/toolchain/binaries/arm-linux-gnueabihf/gcc-linaro-4.9-2015.02-3-x86_64_arm-linux-gnueabihf.tar.xz"
#TOOLCHAIN="http://releases.linaro.org/14.11/components/toolchain/binaries/arm-linux-gnueabihf/gcc-linaro-4.9-2014.11-x86_64_arm-linux-gnueabihf.tar.xz"
curl -O $TOOLCHAIN
sudo mkdir -p /opt/linaro && sudo chown $USER:$USER /opt/linaro
tar -xpf *linaro*.tar.xz -C /opt/linaro
# Vivado needs a gmake executable
sudo ln -s /usr/bin/make /usr/bin/gmake
# 32-bit libraries needed by old toolchains on 64-bit Ubuntu
sudo apt-get install libc6-dev-i386
```

Vivado 2020.1 is installed from the Xilinx installer; it is needed only for the FPGA. To build only user-space
software (controller, `c/` tools) the Linaro toolchain is enough.

Load the C environment:

```bash
cd rp_lock-in_pid_h_hf
source settings.sh          # sources Vivado 2015.2 if present, adds Linaro to PATH,
                            # exports TOOLCHAIN_PATH and CROSS_COMPILE=arm-linux-gnueabihf-
```

The FPGA Makefile loads Vivado 2020.1 by itself in a clean environment (`env -i`), so it does not matter
whether `settings.sh` was sourced: both environments never mix.

## Building everything

```bash
cd rp_lock-in_pid_h_hf
source settings.sh
LANG=C make
```

This builds the controller, the `c/` tools and, if any FPGA source changed, the FPGA (about 30 min), then
`target/` and the packages `archive/lock_in+pid_harmonic_hf-<version>-<build>-devbuild.{zip,tar.gz}`.

A typical rebuild after changing only C or the web page (as devAgent does, FPGA untouched):

```bash
source settings.sh
make -C lock_in+pid_harmonic_hf clean_app && LANG=C make
```

`clean_app` and `clean_fpga` increment the build number in `_build_number`.

## Makefiles and targets

Root `Makefile`:

| Target | Action |
|---|---|
| `make` / `make all` | `make -C lock_in+pid_harmonic_hf all zip tar` (packages in `archive/`) |
| `make clean` | `make -C lock_in+pid_harmonic_hf clean` |
| `make upload` | `make -C lock_in+pid_harmonic_hf upload` |

`lock_in+pid_harmonic_hf/Makefile`:

| Target | Action |
|---|---|
| `all` | `controllerhf.so` + `c_tools` + `fpga` |
| `app` | `controllerhf.so` + `c_tools` |
| `controllerhf.so` | `make -C src clean && make -C src` (only the App itself; the DEBUG and RELOAD variants and their `sed` edits were removed in v2.3.10) |
| `c_tools` | `make -C c all` (cross compiled `lock`, `osc`, `streaming`, `stream_tcp_osc_cmd`) |
| `fpga` | `red_pitaya.bit` (from `fpga/`), `fpga.bit` (copy) and `fpga.bit.bin` (bootgen) |
| `target/lock_in+pid_harmonic_hf` | staging of the installable folder (also copies `upload_app.sh`, `resources/`, README, CHANGELOG; sets the version in `info.json` and `index.html`; removes `__pycache__`/`*.pyc`) |
| `zip`, `tar` | packages in `../archive/` |
| `clean`, `clean_app`, `clean_fpga`, `clean_target` | clean all / C (`src`, `c`, `*.so`, target) / FPGA / target |
| `upload`, `upload_bit`, `upload_html`, `upload_py` | copy to the board by SSH (needs `RPIP`, on the command line or in `../_settings.env`, see below; `check_rpip` stops if it is empty). Since v2.3.15 they depend only on `target/` (`upload_html` sends the `index.html` of `target/`, with the version), make the file system writable with the `rw` script of the OS (`/opt/redpitaya/sbin/rw` with `PATH_REDPITAYA` exported on 2.0, `/boot/sbin/rw` on 0.9x), `upload` keeps `fpga.sh` at 755 and `upload_bit` also sends `fpga.bit.bin`. Never run by the build (since v2.3.10) |

`lock_in+pid_harmonic_hf/fpga/Makefile`: see [FPGA](#fpga-vivado-20201).

Settings file `_settings.env` (root, not versioned), read by both Makefiles:

```make
RPIP=rp-XXXXXX.local
RPOPTS=-l root -p 22
RPSCP=-P 22
```

## C controller (`controllerhf.so`)

- Sources in `lock_in+pid_harmonic_hf/src/`, `src/Makefile`: `$(CROSS_COMPILE)gcc`, `-Wall -Werror -g -fPIC`,
  linked with `-shared -lm -lpthread`; `VERSION` and `REVISION` come from `info/info.json` and the build
  number through `CFLAGS`.
- Build: `make -C lock_in+pid_harmonic_hf controllerhf.so` (with `settings.sh` loaded).
- To install a new `.so` on a running board: copy it and **stop + start the App**
  (`/bazaar?stop=` then `/bazaar?start=lock_in+pid_harmonic_hf`), so that nginx loads the new library.
- Debug output (`TRACE`) goes to the nginx log when the controller is built with `#define DEBUG 1` in `src/main.h`
  (by hand: the DEBUG flavour is no longer built).
- The phase range is in the parameter table: `lock_gen_mod_phase` max 119 (`src/main.c` l. 361).

## Tools of `c/` (`lock`, `osc`, streaming)

| Tool | Source | Purpose |
|---|---|---|
| `lock` | `c/lock.c` | read/write the lock registers by name (`/lock_in+pid_harmonic_hf/lock`) |
| `osc` | `c/osc.c` | read/write the scope registers by name, `dump` of both buffers (`/lock_in+pid_harmonic_hf/osc`) |
| `streaming` | `c/streaming.c` | waits for `stream_cmd`, launches `stream_tcp_osc_cmd` (`/lock_in+pid_harmonic_hf/streaming`, through `stream_start.sh`) |
| `stream_tcp_osc_cmd` | `c/stream_tcp_osc_cmd.c` | reads the scope buffers continuously and sends them over TCP: `stream_tcp_osc_cmd <host> <port> <send_min_len>` |

**From the development PC (cross compilation, since v2.3.10).** `c/Makefile` uses `$(CROSS_COMPILE)gcc`
with its own flags (`-g -std=gnu11 -fstack-protector-strong`, plus `-Wno-overflow` for `lock`/`osc`), the
same as the original binaries built on the board, independent of the `CFLAGS` of the App Makefile:

```bash
cd rp_lock-in_pid_h_hf
source settings.sh                       # CROSS_COMPILE=arm-linux-gnueabihf-
make -C lock_in+pid_harmonic_hf c_tools     # or: make -C lock_in+pid_harmonic_hf/c all
make -C lock_in+pid_harmonic_hf/c clean
```

`make all`, `make app` and the packages include `c_tools`, so the binaries in `target/` always match their
sources. Extra flags: `make -C lock_in+pid_harmonic_hf/c EXTRA_CFLAGS=-Wall`.

**On the board (as before v2.3.10).** With `CROSS_COMPILE` empty the same Makefile uses the native `gcc`:

```bash
ssh root@rp-XXXXXX.local
export PATH_REDPITAYA=/opt/redpitaya; /opt/redpitaya/sbin/rw     # read-write file system (Ecosystem 2.0)
cd /opt/redpitaya/www/apps/lock_in+pid_harmonic_hf/c
make clean && make all
```

The original binaries were built with gcc 5.4 on a 0.9x board. Whether RedPitaya_OS 2.04 still ships
`gcc` and `make` has **not been checked (a confirmar)**; cross compilation is the supported way.

## FPGA (Vivado 2020.1)

`lock_in+pid_harmonic_hf/fpga/` follows the structure of
[RedPitaya-FPGA](https://github.com/RedPitaya/RedPitaya-FPGA) (project `v0.94`, model `Z10`), with the
`lock` module of the App. Details: `fpga/README.md`.

```bash
cd rp_lock-in_pid_h_hf/lock_in+pid_harmonic_hf/fpga
make            # prj/v0.94/out/red_pitaya.bit + prj/v0.94/out/fpga.bit.bin (bootgen)
make bit        # only the bitstream
make bin        # only fpga.bit.bin from an existing red_pitaya.bit
make project    # create prj/v0.94/build/redpitaya.xpr and open it in the Vivado GUI (no synthesis)
make clean      # remove the build products of PRJ
make help
```

Variables: `VIVADO_SETTINGS` (default `/tools/Xilinx/Vivado/2020.1/settings64.sh`), `PRJ` (`v0.94`),
`MODEL` (`Z10`), `DEFINES`. Any change in `rtl/`, `prj/v0.94/{rtl,ip,sdc}`, `sdc/`, `brd/` or the tcl
rebuilds the bitstream. After a build `synCheck.sh` writes a report (timing, critical warnings) to
`prj/v0.94/out/`; the log is `prj/v0.94/out/vivado.log`.

From the App folder, `make fpga` builds through this Makefile and copies `red_pitaya.bit`, `fpga.bit` and
`fpga.bit.bin` to the App. On Ecosystem 2.0 only `fpga.bit.bin` is used (by `fpga.sh`).

Where to change things:

| What | File |
|---|---|
| Lock module (registers, muxers, lock-in, outputs) | `prj/v0.94/rtl/lock.v` (bus decoder generated by `config_tool.py`) |
| Submodules (PID, filters, generator, ramp, lock control) | `prj/v0.94/rtl/lock/*.v` |
| **HF modulation generator** | `prj/v0.94/rtl/lock/gen_mod_h.v` (`[PERIOD_LEN_PARAM DOCK]`: `mem_large = 120`, `mem_f1 = 30`, `mem_f2 = 15`, `mem_f3 = 10`) and its quarter-period tables `lock/data_sin1.dat`, `data_cos1.dat`, `data_cos2.dat`, `data_cos3.dat` (`data_cos4.dat` is not used); tables made with `resources/code_helpers/gen_sin_cos.py` (`T = 120`, amplitude 4095·cos((n+0.5)·2π/T)). The tcl adds `lock/*.dat` by glob |
| Connections to ADC/DAC/scope/PWM/DIO | `prj/v0.94/rtl/red_pitaya_top.sv` |
| Scope (decimation, `osc_ctrl_i`, bus read) | `rtl/rtl/classic/rp_scope_com.v`, `rp_scope_cfg.v`, `rp_decim.v` |
| Constraints | `sdc/red_pitaya.xdc`, `prj/v0.94/sdc/` |

Known: timing almost closes since v2.3.13 (WNS −0.945 ns, TNS −213 ns, 714 endpoints; v2.3.14 −0.897 ns, `devAgent.md`):
pipeline registers in the long chains of the loop ([`lock_latency.md`](../lock_in+pid_harmonic_hf/doc/lock_latency.md)).
The rest of this paragraph is the state of v2.3.11. v2.3.11: WNS −9.281 ns, TNS −7166 ns
(4146 of 27726 endpoints; v2.3.10: −9.637 / −9327); the worst paths are the long combinational paths of the
loop (PID → scope muxes −9.281, DAC −8.698, `_rd` copies −8.205); the bus read of the lock module meets timing
(`sys_rdata` +3.138 ns) with the 2-cycle multicycle constraint of `prj/v0.94/sdc/red_pitaya.xdc` l. 82-83. In
`lock_ctrl` the registered trigger inputs left 15 failing endpoints (45 in v2.3.10): **14 `signal_now_reg` at
−6.010 ns**, coming from the DSP of the lock-in chain (`i_mult_dps_cos_ref`), and `ramp_trigger_r` −0.799 ns; the
state machine, counter and comparators meet timing (+0.084 ns). Whether those 14 paths can make the Level trigger
fail in practice is **a confirmar** (it worked in all the board tests) (`devAgent.md` 2026-10-10 14:39 and 19:02). If you add a register to the read
mux of `lock.v`, keep it a register of `adc_clk` held during `sys_ren` (as the `*_rd` copies), or the multicycle
constraint is no longer valid ([FPGA.md](FPGA.md#lock-module-0x40600000)). Simulations of `lock_ctrl.v` and of
the bus reads: see [test/](#simulations-and-tests-test).

## Web interface (`index.html`)

- Everything (HTML, CSS overrides, JavaScript) is in `index.html`; it uses jQuery, Bootstrap and Flot from
  the Ecosystem (`../assets/`) and `js/jquery.mousewheel.js`, `js/js.cookie.min.js` of the App.
- The version shown in the title is set when packaging (`var app_version = 'VERSION'` is replaced in
  `target/`): test with the file from `target/`, not from the source folder.
- To try a change on the board without rebuilding the rest, copy `index.html` (and `js/`, `css/`) to
  `/opt/redpitaya/www/apps/lock_in+pid_harmonic_hf/` (`upload_app.sh -w <host>` does it) and reload the page;
  `nginx.conf` serves `index.html` with `Cache-Control: no-cache`.
- Syntax check: extract the scripts and run `node --check` (as devAgent does), and run the node
  simulations of `test/`, which load the functions of `index.html`.
- Blocks marked with comments like `[LOCK CAPTURE BEGIN]` / `[TRIG FROM GRAPH BEGIN]` are used by the
  simulations; keep the markers.

## Registers and `config_tool.py`

`resources/config_tool.py` keeps the list of the lock registers (name, width, sign, reset value,
description, UI widget) and of the scope registers, and regenerates the code between "dock" markers:

| Output | Docks |
|---|---|
| `fpga/prj/v0.94/rtl/lock.v` | `[WIREREG DOCK]`, `[FPGA MEMORY DOCK]` |
| `src/fpga_lock.h`, `src/lock.c`, `src/main.c`, `src/main.h` | register struct, `[FPGAUPDATE DOCK]`, `[MAINDEFH DOCK]`, parameter table |
| `index.html` | fields and selectors |
| `c/lock.c`, `c/osc.c`, `c/lock.txt`, `c/osc.txt` | `[LOCKREGS DOCK]`, `[OSCREGS DOCK]`, CSV files |
| `py/hugo.py` | register tables |

Usage (from inside `rp_lock-in_pid_h_hf/`): `python3 resources/config_tool.py` (verilog, main, html, py), or
with arguments `verilog|fpga`, `main`, `html`, `py`, `rp_c`, `all`, `clean`. Each run moves the modified
files to `name_YYYYMMDD_HHmmss.ext` backups. Hand-written blocks inside a dock (e.g. the `c_block` of
`lock_control` in `[FPGAUPDATE DOCK]`) are kept in the table of the tool; review the diff after running it.
In this App it has `PERIOD_LEN = 120` fixed (l. 73; `_h` selects 48/480/1680/2520 with the arguments `period48`, `period480`, `period1680`)
and `gen_mod_phase` max 119. Changes taken from `_h`: the v0.94 tree (v2.3.13), `index=` of each register (for
`TrgUnlock`, index 37 of the scope) and the ranges of `lock.txt`/`osc.txt` (v2.3.15); the generated read mux of `lock.v` uses the `*_rd` copies
and loads `sys_rdata` only on reads. **The `html` output is out of date** (its `input_buttons` list is the one of
v2.3.13 of `_h`): `index.html` has been edited by hand since then, do not regenerate it (`devAgent.md`, 2026-10-09 12:14).

After adding or changing a register: run the tool, rebuild FPGA + controller + tools, and update
[FPGA.md](FPGA.md).

## Simulations and tests (`test/`)

| Test | Command | What it checks |
|---|---|---|
| `lock_ctrl_tb.v` | `test/lock_ctrl_sim.sh [work_dir]` (Vivado 2020.1 xsim) | the lock state machine `lock_ctrl.v` with registered trigger inputs (the TB of `lock_in+pid` 2.2.6: compares `sig_trig_now/last`, level+time window 850..854); prints `TB RESULT: PASS` |
| `lock_ctrl_ui_sim.js` | `node test/lock_ctrl_ui_sim.js` | UI ↔ controller ↔ FPGA model of the lock control (`_h` v2.3.13) |
| `lock_capture_ui_sim.js` | `node test/lock_capture_ui_sim.js` | Capture Lock, Fire on click, restore, AUTO (`_h` v2.3.14) |
| `trig_from_graph_sim.js` | `node test/trig_from_graph_sim.js` | click → time conversion of *Choose from graph* (`_h` v2.3.12) |
| `trig_input_units_sim.js` | `node test/trig_input_units_sim.js [--old]` | Time / Level trigger fields with units, empty fields not sent as 0 (`_h` v2.3.16) |
| `lock_bus_read_tb.sv` | `test/lock_bus_read_sim.sh [work_dir [lock.v]]` (Vivado 2020.1 xsim) | bus reads of `lock.v` through `sys_bus_cdc` with asynchronous clocks: `sys_rdata` stable when the PS takes it (`_h` v2.3.17); prints `TB RESULT: PASS` |
| `config_load_window_sim.js` | `node test/config_load_window_sim.js [--old]` | Config → load of the time window: conversion, and the real chunked send of `index.html` against a model of `rp_set_params()` (forceX handshake) plus a GET poll (`_h` v2.3.17) |
| `last_config_sim.js` | `node test/last_config_sim.js [index.html]` | "Load last config on init" (default checked, localStorage), restore of the last config / defaults on init, hold of the last config, Load last config / Reset to defaults, Restart and recoveries restore the tab state, Lock Control below Outputs (v2.3.17, 35 checks) |
| `config_load_block_sim.js` | `node test/config_load_block_sim.js [index.html]` | the option "Don't turn on PIDs and Ramp on config loading": unchecked by default, Config → load and Restart restore ramp / Scan enable / PIDs as saved, checked keeps them off, lock requests always 0 (v2.3.16, 10 checks) |
| `auto_set_c_sim/` | `test/auto_set_c_sim/run.sh [src dir]` | the real C controller compiled for the PC with fake `/dev/mem` (`fake_hw.h`, `harness.c`): AUTO after a capture, forceX; since v2.3.14 also a model of the circular scope buffer and of the lock pulse (slow windows, Capture Lock with history, time trigger after a stopped ramp); since v2.3.16 section 10: Auto waits for the trigger, forced after its time limit (`SIM_AUTO=1` runs only it) |
| `lock_latency_tb.sv` | `test/lock_latency_sim.sh [work_dir [old_ref]]` (Vivado 2020.1 xsim) | `lock.v` of the working tree side by side with the one of v2.3.12: every signal is the old one delayed by the latency of [`lock_latency.md`](../lock_in+pid_harmonic_hf/doc/lock_latency.md) (v2.3.13); prints `TB RESULT: PASS` |
| `minor_ui_sim.js` | `node test/minor_ui_sim.js [index.html]` | wheel → τ/f text, X+ up to 68.72 s, labels (v2.3.12) |
| `ramp_mod_period_tb.v` | `test/ramp_mod_period_sim.sh [work_dir]` (Vivado 2020.1 xsim) | periods of the ramp floor/ceil triggers and of the HF modulation trigger (120·(hp+1)) on the RTL, the formulas used by Reset zoom (v2.3.14); prints `TB RESULT: PASS` |
| `reset_zoom_sim.js` | `node test/reset_zoom_sim.js [index.html] [--old]` | the real `resetZoom()` against a model of the time range code of `src/main.c` (v2.3.14, 120-point period) |
| `plot_wheel_sim.js` | `node test/plot_wheel_sim.js [index.html]` | mouse wheel on the plot: no key / SHIFT / ALT, limits, debounce, Capture Lock (v2.3.14) |
| `osc_presets_sim.js` | `node test/osc_presets_sim.js [index.html]` | the OscA\|OscB presets, the `usr` dialog and the Ext Trig → Trigger panel rule (v2.3.15) |

Run them from `lock_in+pid_harmonic_hf/`. All exit with code 1 on failure. `--old` runs a check against the code of
the previous version (it must fail). `lock_ctrl_tb.v` covers 32-bit time triggers ≥ 2³¹ (cases 14-15). Results of
v2.3.11 (`devAgent.md` 2026-10-10 19:02, `build_logs/rp_lock-in_pid_h_hf_20261010_1902_v2311_sim.txt`):
`lock_ctrl_sim` 35/35 (Time trigger 302 clocks after the floor, level+time 854), `lock_bus_read_sim` PASS,
`lock_ctrl_ui_sim` 28/28, `lock_capture_ui_sim` 63/63, `trig_input_units_sim` 38/38, `trig_from_graph_sim` 0
failures, `config_load_window_sim` 21/21; `auto_set_c_sim` 14/14. The generator was simulated in xsim in v2.3.10
(not in `test/`): period of `harmonic_trig` 120/240/1200 clocks with hp 0/1/9, `cos_ref` ±4093, `cos_2f`/`cos_3f`
at 2×/3×. Counts reported in the CHANGELOG for later versions: `lock_latency_sim` 406 checks (v2.3.13); `reset_zoom_sim` 30,
`plot_wheel_sim` 59, `ramp_mod_period_sim` 11, `lock_capture_ui_sim` 79, `auto_set_c_sim` 44, `lock_ctrl_sim` 46
(v2.3.14); `osc_presets_sim` 37 (v2.3.15). Node tests run by devAgent on 2.3.15 (`build_logs/rp_lock-in_pid_h_hf_20261016_1635_v2315_sim.txt`):
`osc_presets` 37/37, `config_load_window` 21/21, `lock_capture_ui` 79/79, `lock_ctrl_ui` 28/28, `minor_ui` 7/7,
`plot_wheel` 59/59, `reset_zoom` 30/30, `trig_input_units` 38/38, `trig_from_graph` 0 failures (the xsim tests and
`auto_set_c_sim` were not rerun on 2.3.15, which only changed the web page).

The Python client `control_finn.py` was tested by devAgent against a fake HTTP server of the board (Lua argument
order, `c/lock`/`c/osc`, 2.0 scope with trigger lock, a model of the C worker, `/data` that only answers a body
sent with the headers). Those scripts are not in the repository (devAgent scratchpad; for this App with `PERIOD_LEN` 120: `test_finn.py`
48/48, `set_freq_hz(10k)` → hp 103); the board tests are in `reportes/lock-in_pid_h_hf.md`.

On the board the reference test is the LOCK MODE procedure of `test_files/lock_test.md` (Apps root),
with `dummy_simulator` on a second board and the HF configs `test_files/lock_in+pid_harmonic_hf__lock_mode.json`
(49.6 kHz) and `…__lock_mode_100k.json` (104.2 kHz); reports in `reportes/lock-in_pid_h_hf_lock_test/`.

## Installing on the board

From a package (`archive/*.tar.gz` or `.zip`, or a GitHub release):

```bash
tar -xzf lock_in+pid_harmonic_hf-2.3.15-<build>-devbuild.tar.gz
./upload_app.sh rp-XXXXXX.local          # -p <ssh port>; -w uploads only index.html, js, css
```

`upload_app.sh` installs an SSH key if needed, makes the file system writable (`/boot/sbin/rw`), replaces
`/opt/redpitaya/www/apps/lock_in+pid_harmonic_hf/` and copies the App. By hand: copy the folder
`lock_in+pid_harmonic_hf/` of the package (not the source folder) to `/opt/redpitaya/www/apps/` with the
file system in read-write mode, keeping `fpga.sh` executable (755).

After installing: open the App page, or stop + start it (`/bazaar?stop=`, `/bazaar?start=lock_in+pid_harmonic_hf`)
if an older version was running. If `nginx.conf` changed, restart nginx
(`systemctl restart redpitaya_nginx`). On Ecosystem 2.0 `reload_fpga` is not supported: restarting the App
reloads the FPGA.

Notes for Ecosystem 2.0 (`testAgent.md`):

- In a non-interactive SSH, `rw` needs `PATH_REDPITAYA`: `export PATH_REDPITAYA=/opt/redpitaya; /opt/redpitaya/sbin/rw`.
  The `upload*` targets of the Makefile do so since v2.3.10, and `upload_app.sh` since v2.3.12 (l. 117-119:
  `/opt/redpitaya/sbin/rw` on Ecosystem 2.0, `/boot/sbin/rw` on 0.9x).
- Each `POST /data` (page, `curl`, `control_finn.py`) leaves an open connection in the nginx of the board; after
  long test sessions restart it with `systemctl restart redpitaya_nginx` (then start the App again)
  ([Remote.md](Remote.md#known-issue-of-the-ecosystem-post-data-leaves-connections-open)).
- Close any browser tab with the main menu of the board before testing: it can relaunch the main menu and
  unload the App.

## Versioning and packages

- Version: `lock_in+pid_harmonic_hf/info/info.json` (`"version": "2.3.15-BUILD_NUMBER"`, name "Harmonic Lock-in+PID HF"),
  `CHANGELOG.md`, `README.md` ("Current version"). Since v2.3.13 the build writes the version of `info.json` in `<title>`
  and in the page title of `target/…/index.html`; the title in the source `index.html` does not matter. Build number: `_build_number`.
  Revision: `REVISION` (default `devbuild`).
- Package name: `lock_in+pid_harmonic_hf-<VER>-<BUILD_NUMBER>-<REVISION>.{zip,tar.gz}` in `archive/`.
- Branches: since 2026-10-15 `master` is the 2.3.x line (FPGA Vivado 2020.1, Ecosystem 2.0); the 0.3.x series
  (FPGA Vivado 2015.2, 0.9x / 1.0 ecosystems) stays in the tags `v0.3` .. `v0.3.9`. Tags `v2.3.10` .. `v2.3.15`.
  `devel2.0` is left as it was and is no longer used. Version numbers of this App do not follow those of
  `lock_in+pid_harmonic`: HF 2.3.10 = `_h` 2.3.10-2.3.11 (+ bus fix of 2.3.17), HF 2.3.11 = `_h` 2.3.12-2.3.17,
  2.3.12 = 2.3.18, 2.3.13 = 2.3.19 (+ the reference delay of 2.3.20), 2.3.14 = 2.3.21-2.3.23, 2.3.15 = 2.3.24.
  The "v2.3.12".."v2.3.24" in the comments of the sources are versions of `_h`.
