#!/usr/bin/env python3
"""
Minimal test to verify if sys.stdout.buffer.flush() hangs on Windows console
with Unicode content.

This tests the hypothesis that mpremote hangs due to:
    sys.stdout.buffer.write(b)
    sys.stdout.buffer.flush()  # <-- Allegedly hangs here

Run this script directly in PowerShell (NOT piped) to test:
    python test_stdout_flush.py

If this script completes without hanging, then the issue is NOT in
CPython's stdout.buffer.flush() but somewhere else in mpremote.
"""

import sys
import os

# The Nepali test file content (UTF-8 encoded)
NEPALI_CONTENT = """# नेपाली नाम - Nepali Name

This file tests Nepali/Devanagari characters.

## Script: Devanagari
Characters: क ख ग घ ङ च छ ज झ ञ ट ठ ड ढ ण त थ द ध न प फ ब भ म य र ल व श ष स ह

## Vowels
अ आ इ ई उ ऊ ऋ ए ऐ ओ औ

## Sample Text
नमस्ते, मेरो नाम नेपाली हो।
(Namaste, mero naam Nepali ho.)
Translation: Hello, my name is Nepali.
""".encode("utf-8")


def test_stdout_buffer():
    """Test if stdout.buffer.write + flush hangs."""
    print("=" * 60)
    print("Testing sys.stdout.buffer.write() + flush()")
    print("=" * 60)
    print(f"Python version: {sys.version}")
    print(f"Platform: {sys.platform}")
    print(f"stdout.encoding: {sys.stdout.encoding}")
    print(f"stdout.isatty(): {sys.stdout.isatty()}")
    print()

    print("Writing Nepali content to sys.stdout.buffer...")
    print("-" * 40)

    # This is exactly what mpremote does in transport.py
    sys.stdout.buffer.write(NEPALI_CONTENT)
    sys.stdout.buffer.flush()  # <-- Does this hang?

    print()
    print("-" * 40)
    print("SUCCESS: stdout.buffer.flush() did NOT hang!")
    print()
    print("If you see this message, the issue is NOT in CPython's")
    print("stdout.buffer implementation, but somewhere else in mpremote.")


def test_with_explicit_bytes():
    """Test with various Unicode byte sequences."""
    print()
    print("=" * 60)
    print("Testing specific Unicode byte sequences")
    print("=" * 60)

    test_cases = [
        ("ASCII", b"Hello World\n"),
        ("Latin-1", "Séamus Ó Murchú\n".encode("utf-8")),
        ("Cyrillic", "Владимир Петров\n".encode("utf-8")),
        ("CJK", "王明 李华\n".encode("utf-8")),
        ("Nepali", "नेपाली नाम\n".encode("utf-8")),
        ("Emoji", "😀 🎉 🚀\n".encode("utf-8")),
        ("Mixed", "Hello 世界 Мир नमस्ते 🌍\n".encode("utf-8")),
    ]

    for name, data in test_cases:
        print(f"\n[{name}] Writing {len(data)} bytes: ", end="")
        sys.stdout.flush()

        sys.stdout.buffer.write(data)
        sys.stdout.buffer.flush()

        print(f"  <- OK")


if __name__ == "__main__":
    print()
    print("*" * 60)
    print("* STANDALONE TEST: sys.stdout.buffer.flush() on Windows  *")
    print("*" * 60)
    print()
    print("IMPORTANT: Run this directly in PowerShell, NOT piped!")
    print("  Good: python test_stdout_flush.py")
    print("  Bad:  python test_stdout_flush.py | Out-String")
    print()

    test_stdout_buffer()
    test_with_explicit_bytes()

    print()
    print("=" * 60)
    print("ALL TESTS COMPLETED - No hangs detected!")
    print("=" * 60)
