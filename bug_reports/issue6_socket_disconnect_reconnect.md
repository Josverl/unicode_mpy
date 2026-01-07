# Bug Report: mpremote disconnect + auto-reconnect fails with socket:// connections

## Port, board and/or hardware

Any platform - affects `mpremote` tool when using `socket://` connections to MicroPython devices.

## MicroPython version

- mpremote 1.27.0
- Python 3.11+ (host)
- Tested against MicroPython unix port via socket://localhost:2218

The issue is in `mpremote` itself, not in MicroPython firmware.

## Reproduction

1. Connect to a MicroPython device via socket:
   ```bash
   mpremote connect socket://localhost:2218 eval "1+2" disconnect eval "2+3"
   ```

2. Observe the error after disconnect.

### Verified Output

```
$ mpremote connect socket://localhost:2218 eval "1+2" disconnect eval "2+3"
3
mpremote: no device found
```

### Expected Output

```
$ mpremote connect socket://localhost:2218 eval "1+2" disconnect eval "2+3"
3
5
```

## Expected behaviour

After a `disconnect` command, mpremote should auto-reconnect to the same device (or discover a new device) and continue executing subsequent commands.

With serial connections, this works correctly - after disconnect, mpremote auto-reconnects for the next command.

## Observed behaviour

With socket connections (`socket://`), after a `disconnect` command, mpremote fails to reconnect and reports "no device found" instead of reconnecting to the socket and executing the remaining commands.

### Root Cause Analysis

When using serial port connections, mpremote can auto-detect available devices via USB enumeration. However, socket connections don't have auto-detection - the socket address must be explicitly provided.

After `disconnect`:
1. The socket connection is closed
2. mpremote attempts to find a device for the next command
3. Auto-detection doesn't find socket-based devices
4. Error: "no device found"

The issue is that mpremote doesn't remember the socket connection string for auto-reconnect after an explicit disconnect.

## Additional Information

### Test Case

This issue causes `test_resume.sh` to fail when run against socket connections:

```bash
./tests/run-mpremote-tests.sh -t socket://localhost:2218 ./tests/test_resume.sh
# FAIL on line 17: "mpremote: no device found" instead of "5"
```

The failing test line:
```bash
# A disconnect will trigger auto-reconnect.
$MPREMOTE eval "1+2" disconnect eval "2+3"
```

### Possible Fixes

**Option A: Remember connection for reconnect**

Store the connection string (e.g., `socket://localhost:2218`) in the state object so that after disconnect, the next command can reconnect to the same address.

**Option B: Skip auto-reconnect for socket connections**

Document that `disconnect` followed by commands doesn't work with socket connections, and require explicit `connect` after disconnect.

**Option C: Make disconnect a no-op for socket connections**

For socket connections, `disconnect` could be a soft disconnect that doesn't fully close the connection, or immediately reconnects.

### Workaround

Explicitly reconnect after disconnect:
```bash
mpremote connect socket://localhost:2218 eval "1+2" disconnect connect socket://localhost:2218 eval "2+3"
```

Or use separate mpremote invocations:
```bash
mpremote connect socket://localhost:2218 eval "1+2"
mpremote connect socket://localhost:2218 eval "2+3"
```

### Test Environment

- **OS:** Linux (also affects Windows/macOS)
- **Python:** 3.11+
- **mpremote:** 1.27.0
- **MicroPython:** unix port via socket://localhost:port

### Serial Connections Work Correctly

This issue only affects socket connections. The same test passes with serial connections:

```bash
./tests/run-mpremote-tests.sh -t /dev/ttyACM0 ./tests/test_resume.sh
# PASS - auto-reconnect works correctly with serial ports
```

## Code of Conduct

- Yes, I agree
