# Bug Report: mpremote cp fails with equals sign (=) in filename

## Port, board and/or hardware

Any platform (Windows, Linux, macOS) - affects `mpremote` tool when copying files with equals sign (`=`) in the filename.

## MicroPython version

- mpremote 1.27.0
- Tested against MicroPython unix port and ESP32

The issue is in `mpremote`'s argument parser, not in MicroPython firmware.

## Reproduction

1. Create a test file with an equals sign in the name:
   ```powershell
   mkdir unicode_test
   echo "test" > "unicode_test\H2O_E=mc2.txt"
   ```

2. Attempt to copy to MicroPython device:
   ```powershell
   mpremote cp "unicode_test\H2O_E=mc2.txt" ":/test.txt"
   ```

3. Observe the error.

### Verified Output

```
PS D:\mypython\unicode_mpy> mpremote cp "unicode_test\H2O_E=mc2.txt" ":/test.txt"
Command cp given unexpected argument unicode_test\H2O_E; signature is:
    cp
```

Note: The filename is truncated at the `=` sign - everything after `H2O_E` is lost.

Note: The filename is truncated at the `=` sign.

## Expected behaviour

`mpremote cp` should successfully copy files with equals signs in filenames. The argument parser should not interpret `=` within filenames as key-value separators.

Filenames with `=` are valid on all major operating systems (Windows, Linux, macOS) and should be supported.

## Observed behaviour

The command fails because mpremote's argument parser interprets the `=` character as a key-value separator, truncating the filename:

- Input: `H₂O_E=mc².txt`
- Parsed as: key=`H₂O_E`, value=`mc².txt`
- Error: "unexpected argument" because the truncated filename doesn't match expected syntax

### Root Cause

mpremote's argument parser (likely in `main.py` or the command dispatch logic) splits arguments on `=` to support key-value style arguments. This incorrectly affects filenames that legitimately contain the `=` character.

### Affected Filenames

Any filename containing:
- Equals sign: `=` (U+003D)

Common examples:
- `E=mc².txt`
- `a=b.log`
- `key=value.json`
- `base64==data.bin`

## Additional Information


### Suggested Fix

Modify the argument parser to not split on `=` within file path arguments. Options include:

1. **Stop splitting on `=` for positional arguments** - Only use `=` splitting for named/keyword arguments
2. **Check if the argument is a valid file path first** - If the argument exists as a file, don't split it
3. **Require `--key=value` syntax** - Only split on `=` when preceded by `--`

### Test Results

Testing 126 files for `mpremote cp` functionality:

| Result | Count | Details |
|--------|-------|---------|
| PASS | 124 | All other files work |
| FAIL | 1 | `H₂O_E=mc².txt` (equals sign) |

### Test Environment

- **OS:** Windows 10/11, also reproducible on Linux
- **Python:** 3.13.1
- **mpremote:** 1.27.0
- **MicroPython:** unix port / ESP32

## Code of Conduct

- Yes, I agree
