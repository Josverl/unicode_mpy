"""
Issue #8300: ESP32: os.listdir with non-ASCII chars
https://github.com/micropython/micropython/issues/8300

Description:
On ESP32, os.listdir() fails to properly handle filenames containing non-ASCII
characters (e.g., Chinese, Cyrillic, emoji).

This may be related to filesystem encoding or how the ESP32 VFS layer handles
UTF-8 encoded filenames.
"""


def test_listdir_non_ascii():
    """Test os.listdir() with non-ASCII filenames"""

    import os

    print("Testing os.listdir() with non-ASCII filenames...\n")

    # Test filenames with various Unicode characters
    test_filenames = [
        "test_ascii.txt",
        "café.txt",  # Latin with accent
        "文档.txt",  # Chinese
        "файл.txt",  # Cyrillic (Russian)
        "δοκιμή.txt",  # Greek
        "😀_emoji.txt",  # Emoji in filename
        "Zürich.txt",  # German umlaut
    ]

    test_dir = "test_unicode_files"
    created_files = []

    try:
        # Create test directory
        try:
            os.mkdir(test_dir)
            print(f"Created test directory: {test_dir}")
        except OSError:
            print(f"Test directory already exists: {test_dir}")

        print("\n=== Creating test files ===")
        for filename in test_filenames:
            filepath = f"{test_dir}/{filename}"
            try:
                with open(filepath, "w") as f:
                    f.write(f"Test file: {filename}\n")
                created_files.append(filename)
                print(f"  Created: {filename!r}")
                print(f"    UTF-8 bytes: {filename.encode('utf-8')!r}")
            except Exception as e:
                print(f"  FAIL: Failed to create {filename!r}: {e}")

        print(f"\n=== Listing directory: {test_dir} ===")
        try:
            files = os.listdir(test_dir)
            print(f"os.listdir() returned {len(files)} items:")

            for item in files:
                print(f"  - {item!r}")
                print(f"    Type: {type(item)}")
                if isinstance(item, str):
                    print(f"    UTF-8 bytes: {item.encode('utf-8')!r}")
                elif isinstance(item, bytes):
                    print(f"    Raw bytes: {item!r}")
                    try:
                        decoded = item.decode("utf-8")
                        print(f"    Decoded: {decoded!r}")
                    except:
                        print(f"    Cannot decode as UTF-8")

            # Check which created files appear in listing
            print(f"\n=== Verification ===")
            for filename in created_files:
                if filename in files:
                    print(f"  PASS: Found: {filename!r}")
                else:
                    print(f"  FAIL: Missing: {filename!r}")
                    # Check if it appears with different encoding
                    matches = [
                        f
                        for f in files
                        if filename.encode("utf-8")
                        == (f.encode("utf-8") if isinstance(f, str) else f)
                    ]
                    if matches:
                        print(f"    Possible match: {matches[0]!r}")

        except Exception as e:
            print(f"FAIL: os.listdir() failed: {type(e).__name__}: {e}")

    finally:
        # Cleanup
        print(f"\n=== Cleanup ===")
        for filename in test_filenames:
            filepath = f"{test_dir}/{filename}"
            try:
                os.remove(filepath)
                print(f"  Removed: {filename!r}")
            except:
                pass

        try:
            os.rmdir(test_dir)
            print(f"  Removed directory: {test_dir}")
        except:
            pass

    print("\n" + "=" * 60)
    print("Note: This issue is specific to ESP32 port")
    print("Test may behave differently on unix/windows ports")


if __name__ == "__main__":
    test_listdir_non_ascii()
