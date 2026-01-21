"""
Issue #7585: REPL and `input` skip non-ascii characters of the input
https://github.com/micropython/micropython/issues/7585

Description:
When using the REPL or input() function, non-ASCII characters are skipped or
not properly processed. This affects interactive input of Unicode text.

The issue appears in the character-by-character input processing in the REPL.
"""


def test_input_non_ascii():
    """Test input() and REPL with non-ASCII characters"""

    print("Testing input() with non-ASCII characters...\n")

    # This test demonstrates the expected behavior
    # The actual bug requires interactive testing

    test_strings = [
        "hello",
        "café",
        "你好",
        "Привет",
        "😀",
        "München",
    ]

    print("=== Simulated input processing ===")
    for text in test_strings:
        print(f"\nInput text: {text!r}")
        encoded = text.encode("utf-8")
        print(f"  UTF-8 bytes ({len(encoded)} bytes): {encoded!r}")

        # Simulate character-by-character input as REPL would see it
        result = []
        i = 0
        while i < len(encoded):
            byte = encoded[i]

            # Determine how many bytes in this UTF-8 character
            if byte < 0x80:
                # 1-byte character (ASCII)
                char_bytes = 1
            elif byte < 0xE0:
                # 2-byte character
                char_bytes = 2
            elif byte < 0xF0:
                # 3-byte character
                char_bytes = 3
            else:
                # 4-byte character
                char_bytes = 4

            # Extract the full character
            char_data = encoded[i : i + char_bytes]

            try:
                char = char_data.decode("utf-8")
                result.append(char)
                print(f"    Bytes {char_data!r} -> {char!r}")
            except:
                print(f"    Bytes {char_data!r} -> DECODE ERROR")

            i += char_bytes

        reconstructed = "".join(result)
        if reconstructed == text:
            print(f"  PASS: Correctly reconstructed: {reconstructed!r}")
        else:
            print(f"  FAIL: Reconstruction failed:")
            print(f"     Expected: {text!r}")
            print(f"     Got:      {reconstructed!r}")

    print("\n" + "=" * 60)
    print("INTERACTIVE TEST REQUIRED:")
    print("=" * 60)
    print("""
To reproduce this bug interactively:

1. Start MicroPython REPL
2. Type: name = input("Enter name: ")
3. Enter a name with non-ASCII characters: café
4. Print the result: print(name)

Expected: Should see "café"
Bug: Non-ASCII characters may be skipped, showing "caf"

Another test:
1. In REPL, type: x = "café"
2. Observe if all characters appear correctly

The bug is in the terminal/REPL input character processing,
where multi-byte UTF-8 sequences are not properly handled.

Note: This may depend on the terminal emulator and port being used.
    """)

    print("\n=== Programmatic test (if interactive input available) ===")
    print("Uncomment the following code to test interactively:\n")
    print("""
# Test input() with non-ASCII
# Uncomment to run:
# response = input("Enter some text with non-ASCII (e.g., café): ")
# print(f"You entered: {response!r}")
# print(f"Length: {len(response)}")
# print(f"Bytes: {response.encode('utf-8')!r}")
""")


if __name__ == "__main__":
    test_input_non_ascii()
