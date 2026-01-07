# Bug Report: mpremote cp fails with apostrophe in destination filename

## Port, board and/or hardware

Any platform (Windows, Linux, macOS) - affects `mpremote` tool when copying files with apostrophe (`'`) in the filename.

## MicroPython version

- mpremote 1.27.0
- Tested against MicroPython unix port and ESP32

The issue is in `mpremote` itself, not in MicroPython firmware.

## Reproduction

1. Create a test file with an apostrophe in the name:
   ```powershell
   mkdir unicode_test
   echo "test" > "unicode_test\O'zbek_Ismoilov.txt"
   ```

2. Attempt to copy to MicroPython device with the same destination name:
   ```powershell
   mpremote cp "unicode_test\O'zbek_Ismoilov.txt" ":/O'zbek_Ismoilov.txt"
   ```

3. Observe the error.

### Verified Output

```
PS D:\mypython\unicode_mpy> mpremote cp "unicode_test\O'zbek_Ismoilov.txt" ":/O'zbek_Ismoilov.txt"
cp unicode_test\O'zbek_Ismoilov.txt :/O'zbek_Ismoilov.txt
mpremote: Error with transport:
Traceback (most recent call last):
  File "<stdin>", line 1
SyntaxError: invalid syntax
```

### Verification that the issue is in the destination path:

```powershell
# This FAILS (apostrophe in destination):
mpremote cp "unicode_test\O'zbek_Ismoilov.txt" ":/O'zbek_Ismoilov.txt"

# This WORKS (no apostrophe in destination):
mpremote cp "unicode_test\O'zbek_Ismoilov.txt" ":/Ozbek_Ismoilov.txt"
```

## Expected behaviour

`mpremote cp` should successfully copy files with apostrophes in filenames. The apostrophe should be properly escaped when constructing Python commands to send to the MicroPython REPL.

## Observed behaviour

The command fails with a `SyntaxError` because the apostrophe breaks the Python string literal sent to the REPL.

### Root Cause

mpremote sends filenames to MicroPython's REPL as Python string literals using single quotes. When a filename contains an apostrophe `'`, it prematurely closes the string:

```python
# What mpremote probably sends:
open('/O'zbek_Ismoilov.txt', 'wb')
#        ^ This closes the string prematurely!

# Result is invalid Python syntax
```

### Affected Characters

Any filename containing:
- Single quote / apostrophe: `'` (U+0027)
- Possibly other quote-like characters that need escaping

## Additional Information
### Suggested Fix

Properly escape quotes when constructing Python commands to send to the REPL:

**Option A: Escape single quotes**
```python
# Instead of:
cmd = f"open('{filename}', 'wb')"

# Use:
escaped_filename = filename.replace("\\", "\\\\").replace("'", "\\'")
cmd = f"open('{escaped_filename}', 'wb')"
```

**Option B: Use double quotes for filenames**
```python
cmd = f'open("{filename}", "wb")'
# Note: would then need to escape double quotes in filenames
```

**Option C: Use repr() for proper escaping**
```python
cmd = f"open({repr(filename)}, 'wb')"
```

### Test Results

Testing 126 files for `mpremote cp` functionality (with PYTHONIOENCODING=utf-8):

| Result | Count | Details |
|--------|-------|---------|
| PASS | 124 | All Unicode scripts work |
| FAIL | 1 | `O'zbek_Ismoilov.txt` (apostrophe) |

### Test Environment

- **OS:** Windows 10/11, also reproducible on Linux
- **Python:** 3.13.1
- **mpremote:** 1.27.0
- **MicroPython:** unix port / ESP32

## Code of Conduct

- Yes, I agree
