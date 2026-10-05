
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
