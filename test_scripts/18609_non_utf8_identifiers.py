"""
Issue #18609: Micropython allows creation of non UTF-8 identifiers
https://github.com/micropython/micropython/issues/18609

Description:
MicroPython allows identifiers (variable names, function names) that are not
valid UTF-8, which can cause issues when the code is processed by UTF-8 tools.

This violates Python's requirement that identifiers must be valid Unicode.
"""


def test_non_utf8_identifiers():
    """
    Test creation of identifiers with non-UTF-8 characters.

    In CPython, this would raise a SyntaxError.
    In MicroPython, this may be incorrectly allowed.
    """

    print("Testing non-UTF-8 identifier creation...")

    # Try to create a variable with a byte sequence that's not valid UTF-8
    # This should fail in both CPython and MicroPython
    code_with_invalid_utf8 = b"x\xc0\xc1 = 42"  # Invalid UTF-8 sequence

    try:
        # Try to compile code with invalid UTF-8
        compile(code_with_invalid_utf8, "<test>", "exec")
        print("ERROR: MicroPython incorrectly accepted non-UTF-8 identifier")
    except (SyntaxError, UnicodeDecodeError) as e:
        print(f"CORRECT: Rejected non-UTF-8 identifier: {e}")

    # Test with overlong encoding (security issue)
    code_overlong = b"x\xc0\x80 = 42"  # Overlong encoding of NULL

    try:
        compile(code_overlong, "<test>", "exec")
        print("ERROR: MicroPython accepted overlong UTF-8 encoding")
    except (SyntaxError, UnicodeDecodeError) as e:
        print(f"CORRECT: Rejected overlong encoding: {e}")

    print("\nNote: This issue relates to the lexer/parser accepting invalid UTF-8")
    print("Valid Python identifiers must be valid UTF-8 encoded Unicode")


if __name__ == "__main__":
    test_non_utf8_identifiers()
