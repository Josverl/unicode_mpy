# Unicode Test Suite for mpremote / MicroPython

Test data and scripts to identify Unicode handling issues in `mpremote` and MicroPython.

## Purpose

This repository helps identify which Unicode characters and filenames cause problems when using `mpremote cp` to copy files to a MicroPython device.

## Test Targets

Tests can be run against:

- **Physical device** - Connect via COM port (Windows) or `/dev/ttyUSB*` (Linux/Mac)
- **MicroPython Unix port with mpbridge** - Connect via socket, no physical hardware needed
  - Run the Unix port directly on your machine, or
  - Use the included `mpbridge_container` Docker container for easy setup

## Known Issues Found

| Issue | Description | Workaround |
|-------|-------------|------------|
| Console Encoding | `print()` fails with non-ASCII on Windows (cp1252) | Set `PYTHONIOENCODING=utf-8` |
| Apostrophe in Filenames | `'` breaks MicroPython REPL string parsing | Rename files to avoid `'` |
| Equals Sign in Filenames | `=` breaks mpremote argument parser | Rename files to avoid `=` |
| Console Hangs | Interactive output hangs on Windows console | Use subprocess with `capture_output=True` |

## Quick Start

```powershell
# Set UTF-8 encoding (Windows)
# Optional workaround for current mpremote issues with console encoding
# $env:PYTHONIOENCODING = "utf-8"

# Run full test (copy + read-back)
python unicode_test.py -t socket://localhost:2218

# Test on a COM port
python unicode_test.py -t COM27

# Test console hang issues
python unicode_test.py -t socket://localhost:2218 --interactive --timeout 2
```

## Test Scripts

| Script | Description |
|--------|-------------|
| `unicode_test.py` | Main test script - copy, read-back, and console tests |
| `quick_test.py` | Quick subset test with representative files |
| `disprove_stdout_flush.py` | Proves console hang is not in CPython's stdout |

## Test Data

The `test_data/` folder contains 125+ files with Unicode filenames across many scripts:

- **Latin Extended** - Accents, diacritics (French, German, Spanish, etc.)
- **Cyrillic** - Russian, Ukrainian, Bulgarian, Serbian
- **CJK** - Chinese, Japanese, Korean
- **Arabic/Hebrew/Persian** - RTL scripts
- **Indic** - Hindi, Bengali, Tamil, Telugu, etc.
- **Southeast Asian** - Thai, Vietnamese, Lao, Myanmar
- **Ancient Scripts** - Hieroglyphs, Cuneiform, Runes, etc.
- **Emoji & Symbols** - Emoji, math symbols, special characters
- **Edge Cases** - Zalgo text, zero-width chars, combining marks

## Usage

### Basic Test

```bash
python unicode_test.py -t <device>
```

Options:
- `-t`, `--target` - Device connection (COM port, socket, or `auto`)
- `--interactive` - Test real console output (detects hangs)
- `--timeout` - Timeout in seconds for interactive mode
- `--skip-copy` - Skip copy, only test reading existing files

### Using Docker (MicroPython Unix Port)

```bash
# Start the mpbridge container
docker compose -f mpbridge_container/docker-compose.yml up -d

# Run tests against the container
python unicode_test.py -t socket://localhost:2218
```

## Results

Test results are saved to `unicode_test_results.txt` with detailed codepoint analysis for any failures.

## Cloning This Repository

This repo includes [mpbridge_container](https://github.com/Josverl/mpbridge_container) as a git submodule.

```bash
# Clone with submodule
git clone --recurse-submodules https://github.com/Josverl/unicode_mpy.git

# Or if already cloned, initialize the submodule
git submodule update --init
```

## Related

- [mpbridge_container](https://github.com/Josverl/mpbridge_container) - Docker container for MicroPython Unix port with network bridge (useful for testing)
- [micropython feat/MP_Bridge branch](https://github.com/Josverl/micropython/tree/feat/MP_Bridge) - MicroPython fork with MP_Bridge feature
- [MP_Bridge PR to upstream](https://github.com/micropython/micropython/pull/16292) - Pull request to add mpremote_bridge to MicroPython
- [mpremote documentation](https://docs.micropython.org/en/latest/reference/mpremote.html)
- [MicroPython GitHub](https://github.com/micropython/micropython)
