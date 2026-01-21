"""
Issue #17827: str.center() bug with unicode characters
https://github.com/micropython/micropython/issues/17827

Description:
str.center() method produces incorrect results when centering strings
that contain Unicode characters (multi-byte UTF-8 sequences).

The issue is likely that the method counts bytes instead of characters.
"""


def test_str_center_unicode():
    """Test str.center() with Unicode characters"""

    print("Testing str.center() with Unicode characters...\n")

    # Test cases with various Unicode characters
    test_cases = [
        ("hello", 10, " "),  # ASCII baseline
        ("héllo", 10, " "),  # Latin with accent (é is 2 bytes in UTF-8)
        ("你好", 10, " "),  # Chinese (each char is 3 bytes in UTF-8)
        ("🎉", 5, " "),  # Emoji (4 bytes in UTF-8)
        ("café", 8, "-"),  # Mixed with custom fill char
        ("München", 15, " "),  # German with umlaut
        ("Москва", 12, " "),  # Cyrillic
    ]

    for text, width, fillchar in test_cases:
        # MicroPython's str.center() may not support fillchar parameter
        try:
            result = text.center(width, fillchar)
        except TypeError:
            # Fallback to default fillchar (space)
            if fillchar == " ":
                result = text.center(width)
            else:
                print(f"Text: {text!r}")
                print(f"  NOTE: MicroPython doesn't support fillchar parameter")
                print(f"  Skipping test with fillchar={fillchar!r}")
                print()
                continue

        # Calculate expected: text should be centered with character count
        text_len = len(text)
        byte_len = len(text.encode("utf-8"))
        result_len = len(result)

        print(f"Text: {text!r}")
        print(f"  Character length: {text_len}, Byte length: {byte_len}")
        print(f"  center({width}, {fillchar!r}) = {result!r}")
        print(f"  Result length: {result_len} (expected: {width})")

        # Check if result has correct length
        if result_len != width:
            print(f"  FAIL: Result length is {result_len}, expected {width}")
        else:
            print(f"  PASS")
        print()


if __name__ == "__main__":
    test_str_center_unicode()
