"""
Issue #15129: if uart receives 0xf0 byte then mcu after entering lightsleep never wakes up
https://github.com/micropython/micropython/issues/15129

Description:
When UART receives the byte 0xF0 (which is the start of a 4-byte UTF-8 sequence),
the MCU enters lightsleep and never wakes up.

This appears to be related to Unicode processing in the UART receive path,
where incomplete UTF-8 sequences cause the system to hang.

Note: 0xF0 is the first byte of UTF-8 sequences for characters U+10000 to U+3FFFF
(4-byte sequences, including many emojis)
"""

# MicroPython compatibility
try:
    UnicodeDecodeError
except NameError:
    UnicodeDecodeError = Exception


def test_uart_0xf0_issue():
    """
    Demonstrate the issue with 0xF0 byte in UART.

    This test shows what happens when processing incomplete UTF-8 sequences.
    The actual bug requires hardware UART and lightsleep to reproduce.
    """

    print("Testing UART 0xF0 byte issue (simulated)...\n")

    # 0xF0 starts a 4-byte UTF-8 sequence
    # Valid 4-byte UTF-8 sequences: 0xF0 0x90-0xBF 0x80-0xBF 0x80-0xBF

    test_cases = [
        (b"\xf0", "Incomplete 4-byte sequence (just start byte)"),
        (b"\xf0\x90", "Incomplete 4-byte sequence (2 bytes)"),
        (b"\xf0\x90\x80", "Incomplete 4-byte sequence (3 bytes)"),
        (b"\xf0\x90\x80\x80", "Complete 4-byte sequence (𐀀)"),
        (b"\xf0\x9f\x98\x80", "Complete emoji (😀)"),
        (b"A\xf0B", "0xF0 between ASCII chars"),
        (b"\xf0\xf0", "Two 0xF0 bytes"),
    ]

    print("=== Testing UTF-8 decoding of 0xF0 sequences ===")
    for data, description in test_cases:
        print(f"\n{description}")
        print(f"  Bytes: {data!r}")

        # Try strict decoding
        try:
            decoded = data.decode("utf-8", "strict")
            print(f"  PASS: Strict decode: {decoded!r}")
        except UnicodeDecodeError as e:
            print(f"  FAIL: Strict decode failed: {e}")

        # Try with 'ignore' error handling
        try:
            decoded = data.decode("utf-8", "ignore")
            print(f"  Ignore mode: {decoded!r}")
        except Exception as e:
            print(f"  Ignore mode error: {e}")

    print("\n" + "=" * 60)
    print("HARDWARE TEST REQUIRED:")
    print("=" * 60)
    print("""
To reproduce the actual bug:
1. Set up UART connection to MCU
2. Send 0xF0 byte over UART
3. MCU enters lightsleep
4. MCU should wake up on UART activity, but doesn't

The issue is likely in the UART RX interrupt handler or the
lightsleep wakeup logic when there's an incomplete UTF-8 sequence
in the UART buffer.

Suspected root cause:
- UART RX handler tries to decode UTF-8
- 0xF0 byte indicates 4-byte sequence coming
- Handler waits for remaining bytes
- Lightsleep is entered while handler is waiting
- Wakeup mechanism doesn't trigger properly
    """)


if __name__ == "__main__":
    test_uart_0xf0_issue()
