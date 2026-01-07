# mpremote cp fails with Unicode filenames on Windows

## Bug Summary

There are **four distinct issues** with `mpremote` and Unicode on Windows and some likely on any platform:

1. **Console Encoding Issue** - `print()` fails with non-ASCII characters due to Windows cp1252 encoding (Windows) 
2. **Apostrophe in Filenames** - Files containing `'` break MicroPython REPL string parsing (any platform) 
3. **Equals Sign in Filenames** - Files containing `=` break mpremote's argument parser (any platform) 
4. **Interactive Console Hangs** - `mpremote cat` hangs in interactive PowerShell with Unicode filenames (Windows)

---

## Issue 1: Console Encoding (cp1252)

### Error Message

```
UnicodeEncodeError: 'charmap' codec can't encode characters in position X-Y: character maps to <undefined>
```

### Root Cause

In `mpremote/commands.py` at line 416:
```python
print("{} {} {}".format(command, path, cp_dest))
```

On Windows, `print()` uses the console's default encoding (`cp1252`) which only supports ASCII + Latin-1.

### Workaround for issue 1

```pwsh
$env:PYTHONIOENCODING = "utf-8"
mpremote connect COM3 cp -r . :
```

### Affected Characters

| Type | Example | Status |
|------|---------|--------|
| ASCII | `README.md` | PASS |
| Latin-1 accents | `Séamus_Ó_Murchú.txt` | PASS |
| Cyrillic | `Владимир_Петров.txt` | FAIL |
| CJK | `王明_李华.txt` | FAIL |
| Emoji | `😀_User_🎉.txt` | FAIL |

---

## Issue 2: Apostrophe Breaks REPL String Parsing

### Error Message

```
mpremote: Error with transport:
Traceback (most recent call last):
  File "<stdin>", line 1
SyntaxError: invalid syntax
```

### Reproduction

```powershell
# This fails:
mpremote connect COM3 cp "O'zbek_Ismoilov.txt" ":/O'zbek_Ismoilov.txt"

# This works (no apostrophe in destination):
mpremote connect COM3 cp "O'zbek_Ismoilov.txt" ":/Ozbek_Ismoilov.txt"
```

### Root Cause

mpremote sends filenames to MicroPython's REPL as Python string literals. When a filename contains an apostrophe `'`, it breaks the string delimiter:

```python
# What mpremote probably sends:
open('/O'zbek_Ismoilov.txt', 'wb')
#        ^ This closes the string prematurely!
```

### Affected Files

Any filename containing:
- Single quote / apostrophe: `'` (U+0027)
- Possibly other quote characters

---

## Issue 3: Equals Sign Breaks Argument Parser

### Error Message

```
Command cp given unexpected argument Edge_Cases\H₂O_E; signature is:
    cp
```

### Reproduction

```powershell
# This fails:
mpremote connect COM3 cp "H₂O_E=mc².txt" ":/test.txt"

# Error: argument parser splits on '='
```

### Root Cause

mpremote's argument parser interprets `=` as a key-value separator, truncating the filename at the `=` sign.

### Affected Files

Any filename containing:
- Equals sign: `=` (U+003D)

---

## Issue 4: Windows Interactive Console Hangs on Unicode Output

### Symptom

Running `mpremote cat` interactively in PowerShell hangs indefinitely:

```pwsh
mpremote connect socket://localhost:2218 cat :/unicode_test/नेपाली_नाम.txt
# This hangs (even with PYTHONIOENCODING=utf-8):
```

Expected output:

below output on ubuntu in WSL2

```bash
$ mpremote connect socket://localhost:2218 cat :/unicode_test/नेपाली_नाम.txt
# Nepali Name - नेपाली नाम

This file tests Nepali (Devanagari) script.

## Script: Devanagari (Nepali variant)
Vowels: अ आ इ ई उ ऊ ऋ ए ऐ ओ औ
Consonants: क ख ग घ ङ च छ ज झ ञ ट ठ ड ढ ण त थ द ध न

## Sample Words:
- नेपाल (Nepal)
- नमस्ते (Hello)
- धन्यवाद (Thank you)
- काठमाडौं (Kathmandu)
```

Difficult to test autmatically since as the same command works when called from a Python script with `subprocess.run(capture_output=True)`.

### Possibly related issues

- https://github.com/micropython/micropython/issues/15228
  Unable to print unicode characters when running repl with mpremote
  


### Root Cause Analysis

**Initial hypothesis (DISPROVEN):** The hang was suspected to be in `stdout_write_bytes()`:
```python
def stdout_write_bytes(b):
    sys.stdout.buffer.write(b)
    sys.stdout.buffer.flush()  # <-- Suspected to hang
```

**Test result:** A standalone Python script calling `sys.stdout.buffer.write()` + `flush()` with identical Unicode content does NOT hang. See `test_stdout_flush.py`.

**Actual cause:** The hang is NOT in CPython's stdout handling. The issue is elsewhere in mpremote, possibly:
- Serial/socket transport blocking on device response
- REPL communication waiting for device acknowledgment
- Threading issues between reader/writer threads
- Protocol-level blocking (the device may be in a bad state)

**Key observation:** The hang only occurs when stdout is a real console (isatty=True). When output is piped/captured, mpremote works correctly. This suggests the hang may be related to how mpremote handles console vs. pipe output differently.

Ctrl-C Traceback when hanging on Unicode output: 
```
[  5/127] cat 張偉_陳麗.txt # Chinese Name (Traditional) - Traceback (most recent call last):
  File "C:\Users\josverl\AppData\Roaming\uv\tools\micropython-stubber\Lib\site-packages\mpremote\main.py", line 614, in main
    handler_func(state, args)
    ~~~~~~~~~~~~^^^^^^^^^^^^^
  File "C:\Users\josverl\AppData\Roaming\uv\tools\micropython-stubber\Lib\site-packages\mpremote\commands.py", line 421, in do_filesystem
    state.transport.fs_printfile(path)
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~^^^^^^
  File "C:\Users\josverl\AppData\Roaming\uv\tools\micropython-stubber\Lib\site-packages\mpremote\transport.py", line 129, in fs_printfile
    self.exec(cmd, data_consumer=stdout_write_bytes)
    ~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\josverl\AppData\Roaming\uv\tools\micropython-stubber\Lib\site-packages\mpremote\transport_serial.py", line 309, in exec
    ret, ret_err = self.exec_raw(command, data_consumer=data_consumer)
                   ~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\josverl\AppData\Roaming\uv\tools\micropython-stubber\Lib\site-packages\mpremote\transport_serial.py", line 296, in exec_raw
    return self.follow(timeout, data_consumer)
           ~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\josverl\AppData\Roaming\uv\tools\micropython-stubber\Lib\site-packages\mpremote\transport_serial.py", line 204, in follow
    data = self.read_until(1, b"\x04", timeout=timeout, data_consumer=data_consumer)
  File "C:\Users\josverl\AppData\Roaming\uv\tools\micropython-stubber\Lib\site-packages\mpremote\transport_serial.py", line 146, in read_until
    data_consumer(new_data)
    ~~~~~~~~~~~~~^^^^^^^^^^
  File "C:\Users\josverl\AppData\Roaming\uv\tools\micropython-stubber\Lib\site-packages\mpremote\transport.py", line 36, in stdout_write_bytes
    sys.stdout.buffer.flush()
    ~~~~~~~~~~~~~~~~~~~~~~~^^
KeyboardInterrupt

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "<frozen runpy>", line 198, in _run_module_as_main
  File "<frozen runpy>", line 88, in _run_code
  File "c:\users\josverl\.local\bin\mpremote.exe\__main__.py", line 10, in <module>
    sys.exit(main())
             ~~~~^^
  File "C:\Users\josverl\AppData\Roaming\uv\tools\micropython-stubber\Lib\site-packages\mpremote\main.py", line 636, in main
    do_disconnect(state)
    ~~~~~~~~~~~~~^^^^^^^
  File "C:\Users\josverl\AppData\Roaming\uv\tools\micropython-stubber\Lib\site-packages\mpremote\commands.py", line 89, in do_disconnect
    state.transport.close()
    ~~~~~~~~~~~~~~~~~~~~~^^
  File "C:\Users\josverl\AppData\Roaming\uv\tools\micropython-stubber\Lib\site-packages\mpremote\transport_serial.py", line 119, in close
    self.serial.close()
    ~~~~~~~~~~~~~~~~~^^
  File "C:\Users\josverl\AppData\Roaming\uv\tools\micropython-stubber\Lib\site-packages\serial\urlhandler\protocol_socket.py", line 104, in close
    time.sleep(0.3)
    ~~~~~~~~~~^^^^^
KeyboardInterrupt
Exception ignored on flushing sys.stdout:
KeyboardInterrupt:
Traceback (most recent call last):
  File "D:\mypython\unicode_mpy\test_data\unicode_file_test.py", line 453, in <module>
    test_console_output()
  File "D:\mypython\unicode_mpy\test_data\unicode_file_test.py", line 382, in test_console_output
    code, err = run_mpremote_interactive("cat", remote_path)
                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "D:\mypython\unicode_mpy\test_data\unicode_file_test.py", line 117, in run_mpremote_interactive
    returncode = proc.wait(timeout=INTERACTIVE_TIMEOUT)
                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\josverl\.rye\py\cpython@3.11.9\Lib\subprocess.py", line 1264, in wait
    return self._wait(timeout=timeout)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\josverl\.rye\py\cpython@3.11.9\Lib\subprocess.py", line 1590, in _wait
    result = _winapi.WaitForSingleObject(self._handle,
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
KeyboardInterrupt

```


### Workaround for issue 4

Use a Python script with subprocess to capture output instead of running interactively, or redirect output:
```pwsh
mpremote connect COM22 cat :unicode_test/file.txt > output.txt
```

---

## Expected Behavior

`mpremote cp` should successfully copy files regardless of Unicode characters or special ASCII characters in filenames. The tool should:

1. Handle all Unicode characters in console output (use UTF-8)
2. Properly escape apostrophes and quotes when sending filenames to MicroPython REPL
3. Not interpret `=` in filenames as argument separators
4. Not hang on console output with Unicode content

---

## Comprehensive Test Results

### Copy Test (with PYTHONIOENCODING=utf-8)

Testing 126 files for `mpremote cp` functionality:

| Result | Count | Details |
|--------|-------|---------|
| PASS | 124 | All Unicode scripts work |
| FAIL Transport Error | 1 | `O'zbek_Ismoilov.txt` (apostrophe) |
| FAIL Argument Parser | 1 | `H₂O_E=mc².txt` (equals sign) |

### Interactive Console Test (Issue 4)

Testing `mpremote cat` in real Windows console (no output piping):

| Result | Count | Details |
|--------|-------|---------|
| FAIL Console Hang | **ALL** | Every file with Unicode causes hang |

**Note:** Issue 4 appears to affects ALL Unicode content, not specific characters. The console hang occurs on `sys.stdout.buffer.flush()` in mpremote's transport layer.

**Unicode categories that WORK with the encoding workaround:**
- Latin Extended (accents, diacritics)
- Cyrillic, Greek, Armenian, Georgian
- Arabic, Hebrew, Persian
- CJK (Chinese, Japanese, Korean)
- Indic scripts (Hindi, Bengali, Tamil, etc.)
- Southeast Asian (Thai, Lao, Myanmar, Khmer)
- Ancient scripts (Hieroglyphs, Cuneiform, Runes, etc.)
- Emoji and symbols
- Combining marks, zalgo text
- Zero-width characters, RTL override

**Characters that FAIL (regardless of encoding fix):**
- Apostrophe `'` in destination filename
- Equals sign `=` in filename (mpremote argument parser)

---

## Suggested Fixes

### For Issue 1 (Console Encoding)

**Option A: Force UTF-8 in mpremote** (recommended fix in mpremote code)
```python
import sys
import io

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
```

**Option B: User workaround**
```powershell
$env:PYTHONIOENCODING = "utf-8"
```

### For Issue 2 (Apostrophe in Filenames)

Escape quotes when constructing Python commands to send to REPL:
```python
# Instead of:
cmd = f"open('{filename}', 'wb')"

# Use:
escaped_filename = filename.replace("'", "\\'")
cmd = f"open('{escaped_filename}', 'wb')"

# Or use double quotes:
cmd = f'open("{filename}", "wb")'
```

### For Issue 3 (Equals Sign)

Fix the argument parser to not split on `=` within quoted strings or file paths.

### For Issue 4 (Interactive Console Hangs)

**Note:** Testing proved that `sys.stdout.buffer.flush()` does NOT hang on its own (see `test_stdout_flush.py`). The hang is elsewhere in mpremote.

**Investigation needed:**
1. Identify what code path differs when stdout.isatty() is True vs False
2. Check if mpremote has different threading/buffering behavior for console output
3. Look for blocking reads that wait for device response
4. Check if the issue is in serial transport timing when console output is slow

**Possible areas to investigate:**
- `mpremote/transport.py` - serial communication logic
- Reader/writer thread synchronization
- Console vs. pipe detection affecting flow control

---

## Workarounds for Users

### Encoding Issue
```powershell
# Add to PowerShell $PROFILE:
$env:PYTHONIOENCODING = "utf-8"
$env:PYTHONUTF8 = "1"
```

### Apostrophe in Filenames
Rename files to avoid apostrophes before copying, or copy with a different destination name.

### Equals Sign in Filenames
Rename files to avoid `=` character before copying.

---

## Test Environment

- **OS:** Windows 10/11
- **Python:** 3.13.1
- **mpremote:** mpremote 1.27.0
- **MicroPython:** unix port - Connected via socket://localhost:2218

---

## Test Script

```python
#!/usr/bin/env python3
"""Comprehensive Unicode mpremote test."""

import subprocess
import os
from pathlib import Path

CONN = "socket://localhost:2218"
DEST = "/unicode_test"

def test_copy(filepath: Path) -> tuple[bool, str]:
    dest = f":{DEST}/{filepath.name}"
    cmd = ["mpremote", "connect", CONN, "cp", str(filepath), dest]
    result = subprocess.run(cmd, capture_output=True, text=True, 
                           timeout=60, encoding='utf-8', errors='replace')
    if result.returncode == 0:
        return True, ""
    elif "UnicodeEncodeError" in result.stderr:
        return False, "Console encoding"
    elif "SyntaxError" in result.stderr:
        return False, "REPL string parsing"
    elif "unexpected argument" in result.stderr:
        return False, "Argument parser (= in filename)"
    else:
        return False, result.stderr[:50]

# Run on all .txt files in test_data
for f in Path(".").rglob("*.txt"):
    ok, err = test_copy(f)
    status = "PASS" if ok else f"FAIL: {err}"
    print(f"{status}: {f}")
```
