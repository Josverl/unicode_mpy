# Bug Report: mpremote REPL and mount issues with socket:// and RFC2217 connections

## Port, board and/or hardware

Any platform - affects `mpremote` tool when connecting via `socket://` or RFC2217 (telnet-based serial) connections to MicroPython devices.

Common use cases:
- Connecting to MicroPython Unix port via socket
- Using network-based serial adapters (RFC2217)
- Remote debugging setups

## MicroPython version

- mpremote 1.27.0
- Tested against MicroPython unix port 1.27.0 via 
  - socket://localhost:port
  - rfc2217://localhost:2217

The issues are in `mpremote` itself, not in MicroPython firmware.

## Summary

There are **four related issues** affecting socket-based connections in mpremote:

1. **Missing `in_waiting` property** - `SerialIntercept` class only implements `inWaiting()` method, not the `in_waiting` property, causing mount operations to fail
2. **REPL newline "staircase" effect** - Unix port sends only `\n`, but terminal output flags disable NL→CR-NL translation
3. **`waitchar()` fails with socket connections** - The function assumes serial ports have a `.fd` attribute, which socket-based connections don't have
4. **RFC2217 race condition** - Background thread processing causes `inWaiting()` to return 0 even when data is available

---

## Issue 1: Missing `in_waiting` property in SerialIntercept

### Reproduction

```bash
mpremote connect socket://localhost:2218 mount .
```

### Error

```
AttributeError: 'SerialIntercept' object has no attribute 'in_waiting'
```

### Root Cause

The `SerialIntercept` class in `transport_serial.py` implements `inWaiting()` method but not the `in_waiting` property. Modern pyserial code uses the property form.

### Fix

Add the property to `SerialIntercept`:
```python
@property
def in_waiting(self):
    return self.inWaiting()
```

---

## Issue 2: REPL newline "staircase" effect

### Reproduction

1. Connect to MicroPython Unix port:
   ```bash
   mpremote connect socket://localhost:2218 repl
   ```

2. Type commands and observe output appears like:
   ```
   >>> print("hello")
                      hello
                            >>>
   ```

### Root Cause

In `console.py`, the terminal output flags are set to 0:
```python
attr[1] = 0  # Disables ALL output processing
```

The MicroPython Unix port sends only `\n` (not `\r\n`). With output processing disabled, the terminal doesn't translate `\n` to `\r\n`, causing each line to start where the previous one ended (staircase effect).

### Fix

Keep `OPOST` and `ONLCR` flags for proper newline handling:
```python
attr[1] = termios.OPOST | termios.ONLCR  # Keep NL -> CR-NL translation
```

---

## Issue 3: `waitchar()` fails with socket connections

### Reproduction

```bash
mpremote connect socket://localhost:2218 repl
# REPL may fail to respond or hang
```

### Root Cause

The `waitchar()` function in `console.py` assumes the serial object has a `.fd` attribute:
```python
select.select([self.infd, pyb_serial.fd], [], [])  # Fails for sockets
```

Socket-based connections (especially RFC2217) don't have a `.fd` attribute. RFC2217 uses `._socket` internally.

### Fix

Try multiple methods to get the file descriptor:
```python
def waitchar(self, pyb_serial):
    try:
        serial_fd = pyb_serial.fileno()
    except Exception:
        # RFC2217 doesn't implement fileno(), use internal socket
        serial_fd = pyb_serial._socket.fileno() if hasattr(pyb_serial, "_socket") else None

    if serial_fd is not None:
        select.select([self.infd, serial_fd], [], [])
    else:
        # Fallback: poll with timeout
        while not pyb_serial.in_waiting:
            res = select.select([self.infd], [], [], 0.01)
            if res[0]:
                break
```

---

## Issue 4: RFC2217 race condition in REPL loop

### Reproduction

```bash
mpremote connect socket://localhost:2218 repl
# Output may be delayed, laggy, or appear in bursts
```

### Root Cause

pyserial's RFC2217 implementation uses a background thread to process telnet data from the socket into an internal buffer. When mpremote's REPL loop uses `select()` on the socket, it signals "ready" when data arrives, but `inWaiting()` returns 0 because the background thread hasn't processed the data yet.

**Race condition sequence:**
1. `select()` returns because socket has data
2. `inWaiting()` returns 0 (background thread hasn't processed yet)
3. REPL loop skips reading
4. Next iteration: `select()` returns, now `inWaiting() > 0`
5. Finally reads the data

This causes noticeable lag and stuttering in the REPL.

### Fix

For RFC2217 connections, do a non-blocking read to trigger buffer processing:
```python
n = state.transport.serial.inWaiting()
if n == 0 and _is_rfc2217(state.transport.serial):
    # Non-blocking read triggers buffer processing
    dev_data_in = state.transport.serial.read(1)
    if dev_data_in:
        n = state.transport.serial.inWaiting()
        if n > 0:
            dev_data_in += state.transport.serial.read(n)
```

---

## Expected behaviour

`mpremote` should work correctly with socket-based connections (`socket://`, RFC2217), providing:
- Functional mount operations
- Proper newline handling in REPL output
- Responsive REPL without lag or race conditions

## Observed behaviour

Without these fixes:
- Mount operations fail with `AttributeError`
- REPL output has "staircase" effect (misaligned lines)
- REPL may hang or fail to get input from socket connections
- REPL output is laggy/stuttering with RFC2217 connections

## Additional Information

### Affected Files

- `tools/mpremote/mpremote/transport_serial.py` - Issue 1
- `tools/mpremote/mpremote/console.py` - Issues 2, 3
- `tools/mpremote/mpremote/repl.py` - Issue 4

### Test Environment

- **OS:** Linux/macOS/Windows
- **Python:** 3.11+
- **mpremote:** 1.27.0
- **MicroPython:** Unix port via socket://localhost:port

### Related Commits (fixes)

- `aeb1ce6` - Add `in_waiting` property to SerialIntercept class
- `2d46d52` - Fix REPL newline handling
- `7f0abfd` - Improve `waitchar()` wrt socket connections
- `1ff555c` - Fix REPL race conditions with RFC2217

## Code of Conduct

- Yes, I agree
