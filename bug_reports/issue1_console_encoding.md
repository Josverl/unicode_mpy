# Bug Report: mpremote fails with UnicodeEncodeError on Windows legacy consoles

## Port, board and/or hardware

Windows (any hardware) - affects `mpremote` tool when run on Windows with **legacy console** (cp1252 or similar encoding).


## MicroPython version

- mpremote 1.27.0
- Python 3.11.9 (host)
- Tested against MicroPython unix port and ESP32

The issue is in `mpremote` itself, not in MicroPython firmware.

**Note:** This issue does NOT occur in modern terminals like Windows Terminal or VS Code's integrated terminal, which default to UTF-8.
## Reproduction

This issue only occurs with legacy Windows consoles that use cp1252 or similar encodings. Modern terminals (Windows Terminal, VS Code) use UTF-8 by default and are not affected.

**To reproduce, you must use a legacy console:**

1. Open legacy **cmd.exe** (not Windows Terminal) or configure PowerShell to use cp1252:
   ```powershell
   # Force legacy encoding in Python
   $env:PYTHONIOENCODING = "cp1252"
   ```

2. Create test files with non-ASCII characters:
   ```powershell
   mkdir unicode_test
   echo "test" > "unicode_test\Владимир_Петров.txt"
   ```

3. Use mpremote to copy:
   ```powershell
   mpremote cp -rv unicode_test :
   ```

**Alternatively, the issue can be demonstrated with this Python snippet:**
```python
import sys
sys.stdout.reconfigure(encoding='cp1252')
print('Владимир_Петров.txt')  # Raises UnicodeEncodeError
```

### Error Message

```
UnicodeEncodeError: 'charmap' codec can't encode characters in position X-Y: character maps to <undefined>
```

### Root Cause

In `mpremote/commands.py` at line 416:
```python
print("{} {} {}".format(command, path, cp_dest))
```

On Windows, `print()` uses the console's default encoding (`cp1252`) which only supports ASCII + Latin-1 characters. Any character outside this range causes the error.

### Affected Characters

| Type | Example | Status |
|------|---------|--------|
| ASCII | `README.md` | ✅ PASS |
| Latin-1 accents | `Séamus_Ó_Murchú.txt` | ✅ PASS |
| Cyrillic | `Владимир_Петров.txt` | ❌ FAIL |
| CJK | `王明_李华.txt` | ❌ FAIL |
| Emoji | `😀_User_🎉.txt` | ❌ FAIL |
| Greek | `Αλέξανδρος.txt` | ❌ FAIL |
| Arabic | `محمد_أحمد.txt` | ❌ FAIL |

## Expected behaviour

`mpremote cp` should successfully copy files with Unicode characters in filenames on Windows. The tool should handle all Unicode characters in console output without raising encoding errors.

CPython's `print()` should use UTF-8 or properly handle the console encoding.

## Observed behaviour

The command fails immediately with:
```
UnicodeEncodeError: 'charmap' codec can't encode characters in position X-Y: character maps to <undefined>
```

The file is not copied.

## Additional Information

### Workaround

Set the `PYTHONIOENCODING` environment variable before running mpremote:

```powershell
$env:PYTHONIOENCODING = "utf-8"
mpremote connect COM3 cp -r . :
```

Or add to PowerShell `$PROFILE` for persistence:
```powershell
$env:PYTHONIOENCODING = "utf-8"
$env:PYTHONUTF8 = "1"
```

### Suggested Fix

Force UTF-8 encoding in mpremote on Windows:

```python
import sys
import io

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
```

This would be a minimal change in the mpremote initialization code.

### Test Environment

- **OS:** Windows 10/11
- **Python:** 3.11.9
- **mpremote:** 1.27.0
- **Console:** Legacy cmd.exe or PowerShell with cp1252 encoding

**Not affected:** Windows Terminal, VS Code integrated terminal (these use UTF-8 by default)

## Code of Conduct

- Yes, I agree
