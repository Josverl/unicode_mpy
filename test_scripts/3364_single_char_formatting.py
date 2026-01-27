"""
Issue #3364: formatting of single character codes in strings is truncated to 1 byte
https://github.com/micropython/micropython/issues/3364

Description:
When formatting strings with the %c format specifier, character codes >= 128
(non-ASCII Unicode) are truncated to 1 byte instead of being properly encoded
as multi-byte UTF-8 sequences.

This is similar to issue #13084 but specifically about string formatting truncation.
"""


def test_char_formatting_truncation():
    """Test %c formatting with Unicode code points"""

    print("Testing %c formatting with Unicode characters...\n")

    # Test various Unicode code points
    test_cases = [
        (65, "A", "ASCII letter"),
        (127, "\x7f", "DEL (last ASCII)"),
        (128, "\x80", "First non-ASCII (should be \\xc2\\x80 in UTF-8)"),
        (169, "©", "Copyright symbol (should be \\xc2\\xa9)"),
        (255, "ÿ", "y with diaeresis (should be \\xc3\\xbf)"),
        (256, "Ā", "A with macron (should be \\xc4\\x80)"),
        (0x03B1, "α", "Greek alpha (should be \\xce\\xb1)"),
        (0x4E00, "一", "CJK ideograph (should be \\xe4\\xb8\\x80)"),
        (0x1F600, "😀", "Emoji (should be \\xf0\\x9f\\x98\\x80)"),
    ]

    print("=== Testing %c formatting ===")
    for code, expected_char, description in test_cases:
        print(f"\nCode point: {code} (U+{code:04X}) - {description}")
        print(f"  Expected: {expected_char!r}")

        # Test %c formatting
        try:
            result = "%c" % code
            result_bytes = result.encode("utf-8")
            expected_bytes = expected_char.encode("utf-8")

            print(f"  Result:   {result!r}")
            print(f"  Result bytes:   {result_bytes!r} ({len(result_bytes)} bytes)")
            print(f"  Expected bytes: {expected_bytes!r} ({len(expected_bytes)} bytes)")

            if result_bytes == expected_bytes:
                print(f"  PASS")
            else:
                print(f"  FAIL - bytes don't match")

                # Check if truncated to 1 byte
                if len(result_bytes) == 1 and len(expected_bytes) > 1:
                    print(f"  NOTE: Truncated to 1 byte (bug present)")
                    print(f"     Got {result_bytes[0]:#04x}, expected multi-byte sequence")

        except Exception as e:
            print(f"  Exception: {type(e).__name__}: {e}")

    print("\n" + "=" * 60)
    print("=== Specific truncation test ===")

    # Test case that clearly shows truncation
    code = 169  # © (copyright)
    print(f"Testing code point {code} (©):")
    print(f"  Should encode to UTF-8 as: \\xc2\\xa9 (2 bytes)")

    result = "%c" % code
    result_bytes = result.encode("utf-8") if isinstance(result, str) else bytes([result])

    print(f"  Got: {result_bytes!r}")

    if result_bytes == b"\xc2\xa9":
        print(f"  PASS: Correct UTF-8 encoding")
    elif result_bytes == b"\xa9":
        print(f"  FAIL: BUG CONFIRMED: Truncated to 1 byte (lost \\xc2 prefix)")
    else:
        print(f"  NOTE: Unexpected result")


if __name__ == "__main__":
    test_char_formatting_truncation()
