# Fix: Windows Console UTF-8 Output (Issue #15228)

## Problem

When printing Unicode characters (e.g., Chinese `print("你好")`) via mpremote on Windows, the output would hang or crash with:

```
UnicodeDecodeError: 'utf-8' codec can't decode byte 0xe4 in position 0: unexpected end of data
```

**Root cause**: Serial data is read one byte at a time, but multi-byte UTF-8 characters (3 bytes for CJK, 4 bytes for emoji) get split across reads. When a partial sequence like `\xe4` is immediately decoded, it fails.

## Solution

Two complementary fixes in mpremote:

### 1. `transport.py` — UTF-8 Buffering for `stdout_write_bytes()`

Added a buffer that accumulates bytes and only writes complete UTF-8 sequences:

```python
_stdout_buffer = b""

def stdout_write_bytes(b):
    global _stdout_buffer
    _stdout_buffer += b
    # Only write when buffer contains complete UTF-8 sequences
    # Keep incomplete trailing bytes buffered
```

### 2. `console.py` — Modern Console Detection + Incremental Decoder

- **Modern consoles** (Windows Terminal, VS Code, ConEmu): Write raw bytes directly to `sys.stdout.buffer` like POSIX
- **Legacy consoles**: Use `codecs.getincrementaldecoder("utf-8")` to handle split sequences
- **SetConsoleOutputCP(65001)**: Ensures console interprets output as UTF-8

Detection checks: `WT_SESSION`, `TERM_PROGRAM=vscode`, `ConEmuANSI=ON`, or stdout already UTF-8.

## Files Changed

- `tools/mpremote/mpremote/console.py` — Modern console detection, incremental decoder, SetConsoleOutputCP
- `tools/mpremote/mpremote/transport.py` — UTF-8 buffering in `stdout_write_bytes()`

## Testing

```bash
# Manual test
python -m mpremote unix exec "print('你好')"  # Should output: 你好

# Run unit tests (47 tests)
pytest tests/test_windows_console_utf8.py -v
```

## Related

- GitHub Issue: https://github.com/micropython/micropython/issues/15228
- Complements existing fix `1ab8ba30` (UnicodeEncodeError on Windows legacy consoles)
