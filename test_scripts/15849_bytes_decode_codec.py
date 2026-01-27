"""
Issue #15849: bytes.decode codec not checked for validity + missing codec
https://github.com/micropython/micropython/issues/15849

Description:
1. bytes.decode() doesn't validate that the codec name is valid
2. Some standard Python codecs are missing in MicroPython
3. Error messages are unclear when codec is invalid

Expected behavior:
- Should raise LookupError for unknown codecs
- Should support common codecs or document which are missing
"""

# MicroPython compatibility
try:
    UnicodeDecodeError
except NameError:
    UnicodeDecodeError = Exception


def test_bytes_decode_codec_validation():
    """Test bytes.decode() with various codec names"""

    print("Testing bytes.decode() codec validation...\n")

    test_data = b"Hello, World!"

    # Valid codecs that should work
    # MicroPython only supports UTF-8 (and ASCII as a subset)
    valid_codecs = [
        "utf-8",
        "utf8",
        "ascii",
    ]

    # Invalid/missing codecs
    invalid_codecs = [
        "invalid-codec-name",
        "utf-16",  # Not implemented
        "utf-32",  # Not implemented
        "cp1252",  # Windows encoding - not supported
        "iso-8859-1",  # Not supported
        "latin-1",  # Not supported
        "latin1",  # Not supported
        "",  # Empty codec name
        "gb2312",  # Chinese encoding - not supported
        "shift-jis",  # Japanese encoding - not supported
    ]

    print("=== Testing valid codecs ===")
    for codec in valid_codecs:
        try:
            result = test_data.decode(codec)
            print(f"PASS {codec!r}: {result!r}")
        except Exception as e:
            print(f"FAIL {codec!r}: {type(e).__name__}: {e}")

    print("\n=== Testing invalid/missing codecs ===")
    for codec in invalid_codecs:
        try:
            result = test_data.decode(codec)
            print(f"NOTE {codec!r}: Accepted (returned {result!r})")
        except LookupError as e:
            print(f"PASS {codec!r}: LookupError (correct): {e}")
        except ValueError as e:
            print(f"NOTE {codec!r}: ValueError (should be LookupError): {e}")
        except Exception as e:
            print(f"FAIL {codec!r}: {type(e).__name__}: {e}")

    print("\n=== Testing error handling ===")
    # Test with data that can't be decoded
    invalid_utf8 = b"\x80\x81\x82"

    try:
        result = invalid_utf8.decode("utf-8")
        print(f"FAIL: Should have raised UnicodeDecodeError, got: {result!r}")
    except UnicodeDecodeError as e:
        print(f"PASS: UnicodeDecodeError correctly raised: {e}")

    # Test with error handling parameter
    print("\n=== Testing error handling modes ===")
    error_modes = ["strict", "ignore", "replace"]

    for mode in error_modes:
        try:
            result = invalid_utf8.decode("utf-8", mode)
            print(f"  {mode!r}: {result!r}")
        except Exception as e:
            print(f"  {mode!r}: {type(e).__name__}: {e}")


if __name__ == "__main__":
    test_bytes_decode_codec_validation()
