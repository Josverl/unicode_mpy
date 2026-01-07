# Bug Report: mpremote cat hangs on Windows interactive console with Unicode content

## Port, board and/or hardware

Windows (any hardware) - affects `mpremote cat` command when running interactively in PowerShell/cmd with Unicode file content.

## MicroPython version

- mpremote 1.27.0
- Python 3.13.1 (host)
- Tested against MicroPython unix port (socket://localhost:2218) and ESP32

The issue is in `mpremote` itself, not in MicroPython firmware.

## Reproduction

1. On Windows, have a MicroPython device with a file containing Unicode text:
   ```
   /unicode_test/नेपाली_नाम.txt
   ```

2. Run `mpremote cat` interactively in PowerShell (NOT piped or captured):
   ```powershell
   mpremote connect COM3 cat :/unicode_test/नेपाली_नाम.txt
   ```

3. The command hangs indefinitely. Even with `PYTHONIOENCODING=utf-8` set, it still hangs.

4. Press Ctrl-C to interrupt.

### Key Observation

The same command works correctly when:
- Output is piped: `mpremote cat :file.txt > output.txt`
- Output is captured by subprocess: `subprocess.run([...], capture_output=True)`
- Running on Linux (even in WSL2 on the same machine)

The hang ONLY occurs when stdout is a real Windows console (`isatty=True`).

### Expected Output (works on Linux/WSL2)

```bash
$ mpremote connect socket://localhost:2218 cat :/unicode_test/नेपाली_नाम.txt
# Nepali Name - नेपाली नाम

This file tests Nepali (Devanagari) script.

## Script: Devanagari (Nepali variant)
Vowels: अ आ इ ई उ ऊ ऋ ए ऐ ओ औ
Consonants: क ख ग घ ङ च छ ज झ ञ ट ठ ड ढ ण त थ द ध न
...
```

## Expected behaviour

`mpremote cat` should display Unicode file content in the Windows console without hanging, similar to how it works on Linux and when output is piped/captured.

## Observed behaviour

The command hangs indefinitely when run interactively on Windows with Unicode content. Ctrl-C shows the following traceback:

```
Traceback (most recent call last):
  File "...\mpremote\main.py", line 614, in main
    handler_func(state, args)
  File "...\mpremote\commands.py", line 421, in do_filesystem
    state.transport.fs_printfile(path)
  File "...\mpremote\transport.py", line 129, in fs_printfile
    self.exec(cmd, data_consumer=stdout_write_bytes)
  File "...\mpremote\transport_serial.py", line 309, in exec
    ret, ret_err = self.exec_raw(command, data_consumer=data_consumer)
  File "...\mpremote\transport_serial.py", line 296, in exec_raw
    return self.follow(timeout, data_consumer)
  File "...\mpremote\transport_serial.py", line 204, in follow
    data = self.read_until(1, b"\x04", timeout=timeout, data_consumer=data_consumer)
  File "...\mpremote\transport_serial.py", line 146, in read_until
    data_consumer(new_data)
  File "...\mpremote\transport.py", line 36, in stdout_write_bytes
    sys.stdout.buffer.flush()
KeyboardInterrupt
```

### Root Cause Analysis

**Initial hypothesis (DISPROVEN):** The hang was suspected to be in `stdout_write_bytes()`:
```python
def stdout_write_bytes(b):
    sys.stdout.buffer.write(b)
    sys.stdout.buffer.flush()  # <-- Suspected to hang
```

**Test result:** A standalone Python script calling `sys.stdout.buffer.write()` + `flush()` with identical Unicode content does NOT hang.

**Actual cause:** The hang is NOT in CPython's stdout handling. The issue is elsewhere in mpremote, possibly:
- Different code path when `stdout.isatty()` is True vs False
- Threading/synchronization issues between reader/writer threads
- Windows console API interaction issues
- Serial/socket transport blocking behavior

### Possibly Related Issues

- https://github.com/micropython/micropython/issues/15228 - Unable to print unicode characters when running repl with mpremote

## Additional Information

### Workaround

Redirect output to a file or pipe:
```powershell
# Redirect to file
mpremote connect COM3 cat :unicode_test/file.txt > output.txt

# Or use subprocess in a Python script
import subprocess
result = subprocess.run(
    ["mpremote", "connect", "COM3", "cat", ":file.txt"],
    capture_output=True,
    text=True,
    encoding='utf-8'
)
print(result.stdout)  # This works!
```

### Investigation Needed

1. Identify what code path differs when `stdout.isatty()` is True vs False in mpremote
2. Check if mpremote has different threading/buffering behavior for console output
3. Look for blocking reads that wait for device response  
4. Investigate Windows console API interactions with Unicode output
5. Check if the issue is related to console mode settings (ENABLE_VIRTUAL_TERMINAL_PROCESSING)

### Test Results

Testing `mpremote cat` in real Windows console (no output piping):

| Result | Count | Details |
|--------|-------|---------|
| HANG | **ALL** | Every file with Unicode causes hang |

The hang affects ALL Unicode content, not specific characters. Even files with just Latin-1 extended characters (accents) can trigger the hang.

### Test Environment

- **OS:** Windows 10/11 (x64)
- **Python:** 3.13.1
- **mpremote:** 1.27.0
- **Terminal:** PowerShell 7.x / Windows Terminal / cmd.exe
- **MicroPython:** unix port via socket, ESP32 via serial

## Code of Conduct

- Yes, I agree
