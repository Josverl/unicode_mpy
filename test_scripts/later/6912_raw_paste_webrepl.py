"""
Issue #6912: Raw paste mode can't be used with WebREPL
https://github.com/micropython/micropython/issues/6912

Description:
Raw paste mode doesn't work properly with WebREPL, particularly when
pasting code that contains non-ASCII characters.

Raw paste mode is used to paste multi-line code into the REPL.
The issue manifests when Unicode characters are in the pasted content.
"""


def test_raw_paste_mode_unicode():
    """
    Demonstrate issues with raw paste mode and Unicode.

    Raw paste mode protocol:
    1. Send Ctrl-E to enter paste mode
    2. Send Ctrl-F to enter raw paste mode
    3. Send data
    4. Send Ctrl-D to execute

    The issue is that Unicode in pasted content isn't handled correctly.
    """

    print("Testing raw paste mode with Unicode content...\n")

    # Example code snippets that would be pasted
    test_snippets = [
        # Simple ASCII
        """print("Hello, World!")""",
        # Latin with accents
        """name = "café"
print(f"Welcome to {name}")""",
        # Chinese characters
        """message = "你好世界"
print(message)""",
        # Emoji
        """status = "✓ Success 😀"
print(status)""",
        # Mixed Unicode in comments
        """# Привет - Russian greeting
# 你好 - Chinese greeting  
# مرحبا - Arabic greeting
print("Multilingual code")""",
        # Unicode in string literals and identifiers
        """café_price = 3.50  # Variable name with accent
print(f"Café costs ${café_price}")""",
    ]

    print("=== Test snippets for raw paste mode ===\n")

    for i, snippet in enumerate(test_snippets, 1):
        print(f"Snippet {i}:")
        print("-" * 60)
        print(snippet)
        print("-" * 60)

        # Show the raw bytes that would be transmitted
        encoded = snippet.encode("utf-8")
        print(f"Size: {len(encoded)} bytes (UTF-8)")
        print(f"Characters: {len(snippet)}")

        # Check for non-ASCII
        has_non_ascii = any(b >= 128 for b in encoded)
        if has_non_ascii:
            print(f"NOTE: Contains non-ASCII bytes")
            non_ascii_bytes = [f"{b:#04x}" for b in encoded if b >= 128]
            print(f"   Non-ASCII bytes: {', '.join(non_ascii_bytes)}")
        else:
            print(f"Pure ASCII")

        print()

    print("=" * 60)
    print("WEBREPL TEST PROTOCOL:")
    print("=" * 60)
    print("""
To test with actual WebREPL:

1. Connect to device via WebREPL
2. Press Ctrl-E to enter paste mode
3. Press Ctrl-F to enter raw paste mode (if supported)
4. Paste code with non-ASCII characters (e.g., snippet 2 above)
5. Press Ctrl-D to execute

Expected: Code should execute correctly
Bug: Non-ASCII characters may be corrupted or cause errors

Common symptoms:
- UnicodeDecodeError when pasting
- Characters appear as � (replacement character)
- Code fails to execute
- Silent corruption of string literals

The issue is likely in:
- WebREPL's WebSocket message encoding/decoding
- Raw paste mode's handling of multi-byte UTF-8 sequences
- Buffering that splits UTF-8 sequences across packets
    """)

    print("\n=== Binary protocol simulation ===")
    # Simulate how the data would be transmitted
    snippet = test_snippets[1]  # The café example

    print(f"Simulating transmission of: {snippet[:30]!r}...")
    print(f"\nRaw paste mode sequence:")
    print(f"  1. Send: \\x05 (Ctrl-E) - enter paste mode")
    print(f"  2. Send: \\x06 (Ctrl-F) - enter raw paste mode")
    print(f"  3. Send data length: {len(snippet.encode('utf-8'))} bytes")
    print(f"  4. Send data: {snippet.encode('utf-8')!r}")
    print(f"  5. Send: \\x04 (Ctrl-D) - execute")

    # Check if data could be split incorrectly
    encoded = snippet.encode("utf-8")
    print(f"\nNOTE: Potential issue:")
    print(f"  If WebSocket splits at byte boundaries,")
    print(f"  multi-byte UTF-8 sequences could be broken!")


if __name__ == "__main__":
    test_raw_paste_mode_unicode()
