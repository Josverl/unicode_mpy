#!/usr/bin/env python3
"""
Test to find which Unicode filenames cause mpremote transport errors.
Tests each file individually to isolate problematic characters.

Usage:
    python full_unicode_test.py                    # Use auto-detect
    python full_unicode_test.py -t COM27           # Use specific COM port
    python full_unicode_test.py -t socket://localhost:2218  # Use socket
    python full_unicode_test.py --interactive      # Test console output (detects hangs)
"""

import argparse
import subprocess
import sys
import os
from pathlib import Path

# Global settings, set by parse_args()
CONN = "auto"
DEST_BASE = "/unicode_test"
INTERACTIVE_MODE = False
INTERACTIVE_TIMEOUT = 5  # Short timeout to detect hangs


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Test Unicode filename handling with mpremote",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python full_unicode_test.py -t auto
    python full_unicode_test.py -t COM27
    python full_unicode_test.py -t socket://localhost:2218
    python full_unicode_test.py --interactive      # Test real console behavior
""",
    )
    parser.add_argument(
        "-t",
        "--target",
        default="auto",
        help="Target device connection (default: auto). Examples: COM27, /dev/ttyUSB0, socket://localhost:2218",
    )
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Test with real console output (not piped). Detects console hang issues but output is not captured.",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=5,
        help="Timeout in seconds for interactive mode (default: 5). Longer timeout for slow devices.",
    )
    return parser.parse_args()


def run_mpremote(*args) -> tuple[int, str, str]:
    """Run mpremote command and return (returncode, stdout, stderr).

    Uses captured output (piped) which bypasses console encoding issues.
    Use run_mpremote_interactive() to test real console behavior.
    """
    if CONN == "auto":
        cmd = ["mpremote"] + list(args)
    else:
        cmd = ["mpremote", "connect", CONN] + list(args)
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60,
            encoding="utf-8",
            errors="replace",
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return -1, "", "TIMEOUT"
    except Exception as e:
        return -1, "", str(e)


def run_mpremote_interactive(*args) -> tuple[int, str]:
    """Run mpremote command with real console output (not piped).

    This tests actual console behavior and can detect:
    - Console encoding errors (cp1252 on Windows)
    - Console output hangs (stdout.buffer.flush issues)

    IMPORTANT: Does NOT redirect stdout - output goes to real console.
    This is necessary to trigger the console hang bug.
    Output will be messy but that's expected.

    Returns (returncode, error_type) where error_type is:
    - "" for success
    - "TIMEOUT" if command hangs (console output issue)
    - "ENCODING" if UnicodeEncodeError
    - "ERROR" for other errors
    """
    if CONN == "auto":
        cmd = ["mpremote"] + list(args)
    else:
        cmd = ["mpremote", "connect", CONN] + list(args)

    try:
        # Use Popen for more control over process termination
        # subprocess.run() can hang on communicate() even after timeout
        proc = subprocess.Popen(
            cmd,
            # stdout=None,  # Real console output (triggers hang bug)
            # stderr=subprocess.DEVNULL,  # Don't capture stderr to avoid pipe blocking
            text=True,
        )
        try:
            returncode = proc.wait(timeout=INTERACTIVE_TIMEOUT)
            return returncode, ""
        except subprocess.TimeoutExpired:
            # Kill the process to avoid orphaned mpremote
            proc.kill()
            proc.wait()  # Reap the process
            return -1, "TIMEOUT (console hang)"
    except Exception as e:
        err_str = str(e)
        if "UnicodeEncodeError" in err_str:
            return -1, "ENCODING"
        return -1, f"ERROR: {err_str[:50]}"


def analyze_filename(filename: str) -> list[str]:
    """Return list of potential issues with filename."""
    issues = []
    for i, char in enumerate(filename):
        cp = ord(char)
        if cp > 0xFFFF:
            issues.append(f"Outside BMP: U+{cp:04X} '{char}' at pos {i}")
        elif cp < 0x20 and cp not in (0x09, 0x0A, 0x0D):
            issues.append(f"Control char: U+{cp:04X} at pos {i}")
        elif cp == 0x200B:
            issues.append(f"Zero-width space: U+200B at pos {i}")
        elif cp == 0x202E:
            issues.append(f"RTL override: U+202E at pos {i}")
        elif cp == 0x202C:
            issues.append(f"Pop directional: U+202C at pos {i}")
    return issues


def main():
    print("=" * 70)
    print("Comprehensive Unicode mpremote Transport Test")
    print("=" * 70)
    print(f"Connection: {CONN}")
    print(f"Destination: {DEST_BASE}")
    print()

    # Create base directory
    code, out, err = run_mpremote("mkdir", f":{DEST_BASE}")
    if code != 0 and "exists" not in err.lower():
        print(f"Note: mkdir returned: {err.strip()}")

    # Collect all test files
    test_dir = Path(".")
    all_files = []
    for root, dirs, files in os.walk(test_dir):
        dirs[:] = [d for d in dirs if not d.startswith(".")]
        for f in files:
            if f.endswith(".py") or f.endswith(".md"):
                continue
            filepath = Path(root) / f
            all_files.append(filepath)

    print(f"Testing {len(all_files)} files...\n")

    passed = []
    failed_console = []
    failed_transport = []
    failed_other = []

    for i, filepath in enumerate(sorted(all_files), 1):
        filename = filepath.name
        folder = filepath.parent.name if filepath.parent != Path(".") else ""
        dest = f":{DEST_BASE}/{filename}"

        print(f"[{i:3}/{len(all_files)}] {folder}/{filename}", end=" ")
        sys.stdout.flush()

        code, out, err = run_mpremote("cp", str(filepath), dest)

        if code == 0:
            print("PASS")
            passed.append(filepath)
        else:
            if "UnicodeEncodeError" in err:
                print("FAIL: CONSOLE ENCODING")
                failed_console.append((filepath, "Console encoding (cp1252)"))
            elif "SyntaxError" in err or "Error with transport" in err:
                print("FAIL: TRANSPORT ERROR")
                failed_transport.append((filepath, err.strip()[:100]))
            else:
                print(f"FAIL: OTHER: {err.strip()[:50]}")
                failed_other.append((filepath, err.strip()[:100]))

    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Passed:           {len(passed)}")
    print(f"Console encoding: {len(failed_console)}")
    print(f"Transport error:  {len(failed_transport)}")
    print(f"Other errors:     {len(failed_other)}")

    if failed_transport:
        print("\n" + "-" * 70)
        print("TRANSPORT ERRORS (MicroPython side issues)")
        print("-" * 70)
        for filepath, err in failed_transport:
            print(f"\n📄 {filepath}")
            issues = analyze_filename(filepath.name)
            if issues:
                print("   Potential issues:")
                for issue in issues:
                    print(f"   • {issue}")
            # Print hex dump of filename
            print(f"   Hex: {' '.join(f'{ord(c):04X}' for c in filepath.name)}")

    if failed_console:
        print("\n" + "-" * 70)
        print("CONSOLE ENCODING ERRORS (set PYTHONIOENCODING=utf-8)")
        print("-" * 70)
        for filepath, err in failed_console[:5]:
            print(f"  {filepath}")
        if len(failed_console) > 5:
            print(f"  ... and {len(failed_console) - 5} more")

    if failed_other:
        print("\n" + "-" * 70)
        print("OTHER ERRORS")
        print("-" * 70)
        for filepath, err in failed_other:
            print(f"  {filepath}: {err}")

    # Return passed files for use in read test
    return passed


def test_read_files(files_to_read: list[Path]):
    """Test reading back files using mpremote cat."""
    print("\n" + "=" * 70)
    print("TEST 2: Reading Files with 'mpremote cat'")
    print("=" * 70)
    print()

    if not files_to_read:
        print("No files to read (none were successfully copied)")
        return

    passed = []
    failed_console = []
    failed_transport = []
    failed_content = []
    failed_other = []

    for i, filepath in enumerate(sorted(files_to_read), 1):
        filename = filepath.name
        folder = filepath.parent.name if filepath.parent != Path(".") else ""
        remote_path = f":{DEST_BASE}/{filename}"

        print(f"[{i:3}/{len(files_to_read)}] cat {folder}/{filename}", end=" ")
        sys.stdout.flush()

        # Read local file content for comparison
        try:
            local_content = filepath.read_bytes()
        except Exception as e:
            print(f"FAIL: LOCAL READ ERROR: {e}")
            failed_other.append((filepath, f"Local read: {e}"))
            continue

        # Read remote file using cat
        code, out, err = run_mpremote("cat", remote_path)

        if code == 0:
            # Compare content (cat outputs to stdout as text)
            # Note: cat may have encoding issues with binary content
            remote_content = out.encode("utf-8", errors="replace")

            # Basic size check (exact match may fail due to encoding)
            if len(remote_content) > 0:
                print("PASS")
                passed.append(filepath)
            else:
                print("FAIL: EMPTY")
                failed_content.append((filepath, "Empty response"))
        else:
            if "UnicodeEncodeError" in err:
                print("FAIL: CONSOLE ENCODING")
                failed_console.append((filepath, "Console encoding (cp1252)"))
            elif "SyntaxError" in err or "Error with transport" in err:
                print("FAIL: TRANSPORT ERROR")
                failed_transport.append((filepath, err.strip()[:100]))
            elif "No such file" in err or "ENOENT" in err:
                print("FAIL: FILE NOT FOUND")
                failed_other.append((filepath, "File not found on device"))
            else:
                print(f"FAIL: OTHER: {err.strip()[:50]}")
                failed_other.append((filepath, err.strip()[:100]))

    # Summary
    print("\n" + "=" * 70)
    print("READ TEST SUMMARY")
    print("=" * 70)
    print(f"Passed:           {len(passed)}")
    print(f"Console encoding: {len(failed_console)}")
    print(f"Transport error:  {len(failed_transport)}")
    print(f"Content issues:   {len(failed_content)}")
    print(f"Other errors:     {len(failed_other)}")

    if failed_transport:
        print("\n" + "-" * 70)
        print("READ TRANSPORT ERRORS")
        print("-" * 70)
        for filepath, err in failed_transport:
            print(f"\n📄 {filepath}")
            issues = analyze_filename(filepath.name)
            if issues:
                print("   Potential issues:")
                for issue in issues:
                    print(f"   • {issue}")
            print(f"   Hex: {' '.join(f'{ord(c):04X}' for c in filepath.name)}")

    if failed_other:
        print("\n" + "-" * 70)
        print("OTHER READ ERRORS")
        print("-" * 70)
        for filepath, err in failed_other:
            print(f"  {filepath}: {err}")


def test_console_output():
    """Test mpremote cat with real console output to detect hang issues.

    This uses run_mpremote_interactive() which doesn't capture output,
    allowing detection of console encoding and hang issues.
    """
    # First, get list of files on device
    code, out, err = run_mpremote("ls", f":{DEST_BASE}")
    if code != 0:
        print(f"Error listing {DEST_BASE}: {err}")
        print("Run without --interactive first to copy files to device.")
        return

    # Parse ls output to get filenames
    files = ["README.md"] # Always include README.md
    for line in out.strip().split("\n"):
        line = line.strip()
        if line and not line.startswith("ls"):
            # ls output format varies, try to extract filename
            parts = line.split()
            if parts:
                # Last part is usually filename
                filename = parts[-1] if len(parts) > 1 else parts[0]
                files.append(filename)

    if not files:
        print("No files found in {DEST_BASE}. Run without --interactive first.")
        return

    print(f"Testing {len(files)} files for console output issues...\n")

    passed = []
    failed_timeout = []
    failed_encoding = []
    failed_other = []

    for i, filename in enumerate(files, 1):
        remote_path = f":{DEST_BASE}/{filename}"

        print(f"[{i:3}/{len(files)}] cat {filename}", end=" ")
        sys.stdout.flush()

        code, err = run_mpremote_interactive("cat", remote_path)

        if code == 0:
            print("PASS")
            passed.append(filename)
        elif "TIMEOUT" in err:
            print("FAIL: CONSOLE HANG (timeout)")
            failed_timeout.append((filename, err))
        elif "ENCODING" in err:
            print("FAIL: CONSOLE ENCODING")
            failed_encoding.append((filename, err))
        else:
            print(f"FAIL: {err[:40]}")
            failed_other.append((filename, err))

    # Summary
    print("\n" + "=" * 70)
    print("CONSOLE OUTPUT TEST SUMMARY")
    print("=" * 70)
    print(f"Passed:           {len(passed)}")
    print(f"Console hang:     {len(failed_timeout)}")
    print(f"Console encoding: {len(failed_encoding)}")
    print(f"Other errors:     {len(failed_other)}")

    if failed_timeout:
        print("\n" + "-" * 70)
        print("CONSOLE HANG ISSUES (stdout.buffer.flush hangs)")
        print("-" * 70)
        print("These files cause mpremote to hang when outputting to console.")
        print(
            "Workaround: Use subprocess with capture_output=True, or redirect to file."
        )
        for filename, err in failed_timeout[:10]:
            print(f"  • {filename}")
            issues = analyze_filename(filename)
            if issues:
                for issue in issues:
                    print(f"      {issue}")
        if len(failed_timeout) > 10:
            print(f"  ... and {len(failed_timeout) - 10} more")

    if failed_encoding:
        print("\n" + "-" * 70)
        print("CONSOLE ENCODING ISSUES")
        print("-" * 70)
        print("Set PYTHONIOENCODING=utf-8 to fix.")
        for filename, err in failed_encoding[:5]:
            print(f"  • {filename}")
        if len(failed_encoding) > 5:
            print(f"  ... and {len(failed_encoding) - 5} more")


if __name__ == "__main__":
    # Parse command line arguments
    args = parse_args()
    CONN = args.target
    INTERACTIVE_MODE = args.interactive
    INTERACTIVE_TIMEOUT = args.timeout

    if INTERACTIVE_MODE:
        print("=" * 70)
        print("INTERACTIVE MODE - Testing Real Console Behavior")
        print("=" * 70)
        print(f"Connection: {CONN}")
        print(f"Timeout: {INTERACTIVE_TIMEOUT}s (commands that hang will timeout)")
        print()
        print("This mode detects console output issues that don't appear when")
        print("output is piped. A TIMEOUT indicates the console hung.")
        print()

        # Run interactive console test on already-copied files
        test_console_output()
    else:
        # Test 1: Copy files
        copied_files = main()

        # Test 2: Read back files that were successfully copied
        if copied_files:
            test_read_files(copied_files)
