#!/usr/bin/env python3
"""
Comprehensive Unicode filename test for mpremote.
Tests copy, read-back, and console output behavior.

Usage:
    python unicode_test.py                         # Use auto-detect
    python unicode_test.py -t COM27                # Use specific COM port
    python unicode_test.py -t socket://localhost:2218  # Use socket
    python unicode_test.py --interactive           # Test console output (detects hangs)
    python unicode_test.py --skip-copy             # Skip copy, just test read/interactive
"""

import argparse
import os
import subprocess
import sys
import unicodedata
from pathlib import Path

# Global settings (set by parse_args)
CONN = "auto"
DEST_BASE = "/remote_data"
TEST_DIR = Path("test_data")
RESULTS_FILE = "unicode_test_results.txt"
INTERACTIVE_TIMEOUT = 5


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Test Unicode filename handling with mpremote",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python unicode_test.py -t auto
    python unicode_test.py -t COM27
    python unicode_test.py -t socket://localhost:2218
    python unicode_test.py --interactive      # Test real console behavior
    python unicode_test.py --skip-copy        # Only test reading (files already copied)
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
        help="Test with real console output (not piped). Detects console hang issues.",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=5,
        help="Timeout in seconds for interactive mode (default: 5).",
    )
    parser.add_argument(
        "--skip-copy",
        action="store_true",
        help="Skip copy test, only run read/interactive tests on already-copied files.",
    )
    return parser.parse_args()


def run_mpremote(*args) -> tuple[int, str, str]:
    """Run mpremote command and return (returncode, stdout, stderr)."""
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
    """Run mpremote with real console output (not piped).

    Returns (returncode, error_type) where error_type is:
    - "" for success
    - "TIMEOUT" if command hangs
    - "ENCODING" if UnicodeEncodeError
    - "ERROR" for other errors
    """
    if CONN == "auto":
        cmd = ["mpremote"] + list(args)
    else:
        cmd = ["mpremote", "connect", CONN] + list(args)

    try:
        proc = subprocess.Popen(cmd, text=True)
        try:
            returncode = proc.wait(timeout=INTERACTIVE_TIMEOUT)
            return returncode, ""
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait()
            return -1, "TIMEOUT (console hang)"
    except Exception as e:
        err_str = str(e)
        if "UnicodeEncodeError" in err_str:
            return -1, "ENCODING"
        return -1, f"ERROR: {err_str[:50]}"


def analyze_filename(filename: str) -> dict:
    """Analyze a filename for potentially problematic characters."""
    info = {
        "filename": filename,
        "length": len(filename),
        "codepoints": [],
        "categories": set(),
        "potential_issues": [],
    }

    for char in filename:
        cp = ord(char)
        try:
            name = unicodedata.name(char, f"U+{cp:04X}")
            category = unicodedata.category(char)
        except:
            name = f"U+{cp:04X}"
            category = "??"

        info["codepoints"].append(
            {
                "char": char,
                "codepoint": f"U+{cp:04X}",
                "name": name,
                "category": category,
            }
        )
        info["categories"].add(category)

        # Flag potential issues
        if cp > 0xFFFF:
            info["potential_issues"].append(f"Outside BMP: {char} (U+{cp:04X})")
        if category.startswith("M"):
            info["potential_issues"].append(f"Combining mark: {char} (U+{cp:04X})")
        if category == "Cf":
            info["potential_issues"].append(f"Format char: U+{cp:04X}")
        if category == "Co":
            info["potential_issues"].append(f"Private use: U+{cp:04X}")
        if char in "\x00\x01\x02\x03\x04\x05\x06\x07\x08\x0b\x0c\x0e\x0f":
            info["potential_issues"].append(f"Control char: U+{cp:04X}")

    return info


def collect_test_files() -> tuple[list[Path], set[str]]:
    """Collect all test files and subdirectories."""
    all_files = []
    subdirs = set()

    for root, dirs, files in os.walk(TEST_DIR):
        dirs[:] = [d for d in dirs if not d.startswith(".")]
        for d in dirs:
            subdir = (Path(root) / d).relative_to(TEST_DIR)
            subdirs.add(subdir.as_posix())
        for f in files:
            if f.endswith(".py") or f.endswith(".md"):
                continue
            filepath = Path(root) / f
            all_files.append(filepath)

    return all_files, subdirs


def setup_remote_dirs(subdirs: set[str]):
    """Create base and subdirectories on remote."""
    run_mpremote("mkdir", f":{DEST_BASE}")
    for subdir in sorted(subdirs):
        run_mpremote("mkdir", f":{DEST_BASE}/{subdir}")


def test_copy_files(all_files: list[Path]) -> tuple[list[Path], list[tuple[Path, str]]]:
    """Test copying files to remote. Returns (passed, failed)."""
    print("=" * 70)
    print("TEST: Copying Files with 'mpremote cp'")
    print("=" * 70)
    print(f"Connection: {CONN}")
    print(f"Destination: {DEST_BASE}")
    print(f"Testing {len(all_files)} files...\n")

    passed = []
    failed = []

    for i, filepath in enumerate(sorted(all_files), 1):
        filename = filepath.name
        rel_path = filepath.relative_to(TEST_DIR)
        folder = filepath.parent.name if filepath.parent != TEST_DIR else ""
        dest = f":{DEST_BASE}/{rel_path.as_posix()}"

        print(f"[{i:3}/{len(all_files)}] {folder}/{filename}", end=" ")
        sys.stdout.flush()

        code, out, err = run_mpremote("cp", str(filepath), dest)

        if code == 0:
            print("PASS")
            passed.append(filepath)
        else:
            error_type = categorize_error(err)
            print(f"FAIL: {error_type}")
            failed.append((filepath, err.strip()[:200]))

    print_copy_summary(passed, failed)
    return passed, failed


def test_read_files(files_to_read: list[Path]):
    """Test reading back files using mpremote cat."""
    print("\n" + "=" * 70)
    print("TEST: Reading Files with 'mpremote cat'")
    print("=" * 70)
    print(f"Testing {len(files_to_read)} files...\n")

    if not files_to_read:
        print("No files to read.")
        return

    passed = []
    failed = []

    for i, filepath in enumerate(sorted(files_to_read), 1):
        filename = filepath.name
        rel_path = filepath.relative_to(TEST_DIR)
        folder = filepath.parent.name if filepath.parent != TEST_DIR else ""
        remote_path = f":{DEST_BASE}/{rel_path.as_posix()}"

        print(f"[{i:3}/{len(files_to_read)}] cat {folder}/{filename}", end=" ")
        sys.stdout.flush()

        code, out, err = run_mpremote("cat", remote_path)

        if code == 0 and len(out) > 0:
            print("PASS")
            passed.append(filepath)
        else:
            error_type = categorize_error(err) if err else "EMPTY"
            print(f"FAIL: {error_type}")
            failed.append((filepath, err.strip()[:100] if err else "Empty response"))

    # Summary
    print("\n" + "-" * 70)
    print(f"Read test: {len(passed)} passed, {len(failed)} failed")


def test_console_output(all_files: list[Path]):
    """Test mpremote cat with real console output to detect hang issues."""
    print("\n" + "=" * 70)
    print("TEST: Console Output (Interactive Mode)")
    print("=" * 70)
    print(f"Timeout: {INTERACTIVE_TIMEOUT}s per file")
    print(f"Testing {len(all_files)} files...\n")

    passed = []
    failed_timeout = []
    failed_other = []

    for i, filepath in enumerate(sorted(all_files), 1):
        rel_path = filepath.relative_to(TEST_DIR)
        remote_path = f":{DEST_BASE}/{rel_path.as_posix()}"

        print(f"[{i:3}/{len(all_files)}] cat {rel_path.as_posix()}", end=" ")
        sys.stdout.flush()

        code, err = run_mpremote_interactive("cat", remote_path)

        if code == 0:
            print("PASS")
            passed.append(filepath)
        elif "TIMEOUT" in err:
            print("FAIL: CONSOLE HANG")
            failed_timeout.append((filepath, err))
        else:
            print(f"FAIL: {err[:30]}")
            failed_other.append((filepath, err))

    # Summary
    print("\n" + "-" * 70)
    print("CONSOLE OUTPUT SUMMARY")
    print("-" * 70)
    print(f"Passed:       {len(passed)}")
    print(f"Console hang: {len(failed_timeout)}")
    print(f"Other errors: {len(failed_other)}")

    if failed_timeout:
        print("\nFiles causing console hangs:")
        for filepath, _ in failed_timeout[:10]:
            print(f"  - {filepath.relative_to(TEST_DIR)}")
        if len(failed_timeout) > 10:
            print(f"  ... and {len(failed_timeout) - 10} more")


def categorize_error(err: str) -> str:
    """Categorize an error message."""
    if "UnicodeEncodeError" in err:
        return "CONSOLE ENCODING"
    elif "SyntaxError" in err or "Error with transport" in err:
        return "TRANSPORT ERROR"
    elif "No such file" in err or "ENOENT" in err:
        return "FILE NOT FOUND"
    elif "unexpected argument" in err:
        return "ARG PARSER (= in filename)"
    elif "TIMEOUT" in err:
        return "TIMEOUT"
    else:
        return err[:40] if err else "UNKNOWN"


def print_copy_summary(passed: list[Path], failed: list[tuple[Path, str]]):
    """Print copy test summary with detailed analysis of failures."""
    print("\n" + "=" * 70)
    print("COPY TEST SUMMARY")
    print("=" * 70)
    print(f"Passed: {len(passed)}")
    print(f"Failed: {len(failed)}")

    if not failed:
        return

    # Categorize failures
    categories = {"Outside BMP": [], "Combining marks": [], "Format chars": [], "Other": []}

    with open(RESULTS_FILE, "w", encoding="utf-8") as f:
        f.write("Unicode Test Results\n")
        f.write("=" * 70 + "\n\n")

        for filepath, error in failed:
            analysis = analyze_filename(filepath.name)

            # Categorize
            categorized = False
            for issue in analysis["potential_issues"]:
                if "Outside BMP" in issue:
                    categories["Outside BMP"].append(filepath.name)
                    categorized = True
                    break
                elif "Combining" in issue:
                    categories["Combining marks"].append(filepath.name)
                    categorized = True
                    break
                elif "Format char" in issue:
                    categories["Format chars"].append(filepath.name)
                    categorized = True
                    break
            if not categorized:
                categories["Other"].append(filepath.name)

            # Write detailed analysis to file
            f.write(f"\nFile: {filepath.relative_to(TEST_DIR)}\n")
            f.write(f"Error: {error}\n")
            f.write("Codepoints:\n")
            for cp in analysis["codepoints"]:
                f.write(f"  {cp['char']} = {cp['codepoint']} ({cp['name']}) [{cp['category']}]\n")
            if analysis["potential_issues"]:
                f.write("Issues:\n")
                for issue in analysis["potential_issues"]:
                    f.write(f"  - {issue}\n")
            f.write("-" * 40 + "\n")

    # Print categories
    print("\n" + "-" * 70)
    print("FAILURE CATEGORIES")
    print("-" * 70)

    if categories["Outside BMP"]:
        print(f"\nOutside BMP (U+10000+) - {len(categories['Outside BMP'])} files:")
        for name in categories["Outside BMP"][:5]:
            print(f"  - {name}")
        if len(categories["Outside BMP"]) > 5:
            print(f"  ... and {len(categories['Outside BMP']) - 5} more")

    if categories["Combining marks"]:
        print(f"\nCombining marks - {len(categories['Combining marks'])} files:")
        for name in categories["Combining marks"][:5]:
            print(f"  - {name}")

    if categories["Format chars"]:
        print(f"\nFormat characters - {len(categories['Format chars'])} files:")
        for name in categories["Format chars"][:5]:
            print(f"  - {name}")

    if categories["Other"]:
        print(f"\nOther issues - {len(categories['Other'])} files:")
        for name in categories["Other"][:5]:
            print(f"  - {name}")

    print(f"\nDetailed results saved to: {RESULTS_FILE}")


def main():
    args = parse_args()

    global CONN, INTERACTIVE_TIMEOUT
    CONN = args.target
    INTERACTIVE_TIMEOUT = args.timeout

    # Collect test files
    all_files, subdirs = collect_test_files()

    if not all_files:
        print(f"No test files found in {TEST_DIR}")
        sys.exit(1)

    print(f"Found {len(all_files)} files in {len(subdirs)} folders\n")

    if args.interactive:
        # Interactive mode: test console output behavior
        print("=" * 70)
        print("INTERACTIVE MODE - Testing Real Console Behavior")
        print("=" * 70)
        print("This mode detects console output issues that don't appear when")
        print("output is piped. A TIMEOUT indicates the console hung.\n")

        if not args.skip_copy:
            setup_remote_dirs(subdirs)
            passed, _ = test_copy_files(all_files)
            test_console_output(passed if passed else all_files)
        else:
            test_console_output(all_files)
    else:
        # Normal mode: copy and read-back tests
        if args.skip_copy:
            test_read_files(all_files)
        else:
            setup_remote_dirs(subdirs)
            passed, _ = test_copy_files(all_files)
            if passed:
                test_read_files(passed)


if __name__ == "__main__":
    main()
