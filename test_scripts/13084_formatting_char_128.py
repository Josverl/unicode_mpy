"""
Issue #13084: formatting character values >= 128 gives unexpected results, can crash
https://github.com/micropython/micropython/issues/13084

Description:
Using string formatting with character values >= 128 (i.e., non-ASCII Unicode)
produces unexpected results and can cause crashes.

This is related to how %c formatting handles Unicode code points.
"""


def test_char_formatting_high_values():
    """Test formatting of character values >= 128"""

    print("Testing character formatting with values >= 128...\n")

    # Test various character values
    test_values = [
        (65, "A - ASCII letter"),
        (127, "DEL - last ASCII char"),
        (128, "First non-ASCII"),
        (255, "ÿ - Latin-1 max"),
        (256, "Ā - Latin Extended"),
        (0x4E00, "一 - CJK Unified Ideograph"),
        (0x1F600, "😀 - Emoji"),
        (0x10FFFF, "Maximum Unicode code point"),
    ]

    print("=== Testing %c formatting ===")
    for value, description in test_values:
        print(f"\nValue: {value} ({value:#x}) - {description}")

        try:
            # Test %c formatting
            result = "%c" % value
            print(f"  '%c' %% {value} = {result!r}")
            print(f"  Result bytes: {result.encode('utf-8')!r}")

        except Exception as e:
            print(f"  ❌ Error: {type(e).__name__}: {e}")

    print("\n" + "=" * 60)
    print("=== Testing chr() function ===")
    for value, description in test_values:
        print(f"\nValue: {value} ({value:#x}) - {description}")

        try:
            result = chr(value)
            print(f"  chr({value}) = {result!r}")
            print(f"  Result bytes: {result.encode('utf-8')!r}")

        except Exception as e:
            print(f"  ❌ Error: {type(e).__name__}: {e}")

    print("\n" + "=" * 60)

    print("=== Testing edge cases ===")

    # Test invalid values
    invalid_values = [
        -1,  # Negative
        0x110000,  # Beyond max Unicode
        0xD800,  # Surrogate (invalid)
        0xDFFF,  # Surrogate (invalid)
    ]

    for value in invalid_values:
        print(f"\nInvalid value: {value} ({value:#x})")

        for func, name in [(chr, "chr"), (lambda x: "%c" % x, "%c")]:
            try:
                result = func(value)
                print(f"  NOTE: {name}({value}) succeeded: {result!r} (should fail)")
            except ValueError as e:
                print(f"  PASS: {name}({value}) correctly raised ValueError: {e}")
            except Exception as e:
                print(f"  FAIL: {name}({value}) raised {type(e).__name__}: {e}")


if __name__ == "__main__":
    test_char_formatting_high_values()
