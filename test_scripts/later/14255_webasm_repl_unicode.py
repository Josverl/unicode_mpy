"""
Issue #14255: [shared] [webassembly] pyexec_event_repl_process_char unable to understand unicode
https://github.com/micropython/micropython/issues/14255

Description:
The pyexec_event_repl_process_char function in the WebAssembly port (and possibly
other ports) doesn't properly handle Unicode characters in the REPL.

This affects interactive input of non-ASCII characters.
"""

# MicroPython compatibility
try:
    UnicodeDecodeError
except NameError:
    UnicodeDecodeError = Exception


def test_repl_unicode_input():
    """
    Test Unicode character handling in REPL-like input processing.

    This simulates what happens when Unicode characters are entered
    character-by-character in the REPL.
    """

    print("Testing REPL Unicode input handling...\n")

    # Test strings with various Unicode characters
    test_inputs = [
        "hello",  # ASCII baseline
        "café",  # Latin with accent (2-byte UTF-8)
        "你好",  # Chinese (3-byte UTF-8 per char)
        "🎉",  # Emoji (4-byte UTF-8)
        "Привет",  # Cyrillic
        "مرحبا",  # Arabic
    ]

    for text in test_inputs:
        print(f"Input text: {text!r}")

        # Show byte-by-byte encoding
        encoded = text.encode("utf-8")
        print(f"  UTF-8 bytes: {encoded!r}")
        print(f"  Byte count: {len(encoded)}")

        # Simulate character-by-character processing
        # This is what pyexec_event_repl_process_char would see
        print(f"  Processing byte-by-byte:")

        buffer = bytearray()
        for i, byte in enumerate(encoded):
            buffer.append(byte)

            # Try to decode after each byte
            try:
                partial = bytes(buffer).decode("utf-8")
                print(f"    Byte {i + 1} ({byte:#04x}): decoded to {partial!r}")
                buffer.clear()
            except UnicodeDecodeError:
                # Incomplete sequence - need more bytes
                print(f"    Byte {i + 1} ({byte:#04x}): incomplete sequence, waiting...")

        if buffer:
            print(f"    ❌ Buffer not empty at end: {bytes(buffer)!r}")

        print()

    print("=" * 60)
    print("INTERACTIVE TEST:")
    print("=" * 60)
    print("""
To test in actual REPL:
1. Start MicroPython REPL (especially WebAssembly port)
2. Try typing: café
3. Try typing: 你好
4. Try typing: 🎉

Expected: Characters should appear correctly
Bug: Non-ASCII characters may not appear or cause errors

The issue is that pyexec_event_repl_process_char likely processes
input as single bytes rather than handling multi-byte UTF-8 sequences.
    """)


if __name__ == "__main__":
    test_repl_unicode_input()
