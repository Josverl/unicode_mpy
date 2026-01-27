"""
Issue #15979: SPI Connection to SD Card Fails to Recognize Chinese Directories
https://github.com/micropython/micropython/issues/15979

Description:
When using SD card with SPI connection, MicroPython fails to properly handle
directory names containing Chinese (or other multi-byte Unicode) characters.

This is related to filesystem encoding issues when interacting with FAT filesystems
that may use different encodings for filenames.
"""


def test_chinese_directory_names():
    """
    Test handling of Chinese characters in directory names.

    This tests with /sd/unicode directory on SD card to verify
    FAT filesystem handling of Unicode filenames.
    """

    import os

    print("Testing Chinese directory name handling on SD card...\n")

    # Check if SD card is mounted
    try:
        os.stat("/sd")
        print("SD card detected at /sd")
    except:
        print("ERROR: SD card not mounted at /sd")
        print("Please mount SD card first")
        return

    # Create base test directory
    base_dir = "/sd/unicode"
    try:
        os.mkdir(base_dir)
        print(f"Created base directory: {base_dir}\n")
    except OSError:
        print(f"Base directory already exists: {base_dir}\n")

    # Test directory names with Chinese characters
    test_dirs = [
        "测试目录",  # "Test Directory" in Chinese
        "中文文件夹",  # "Chinese Folder"
        "图片_2024",  # "Pictures_2024"
        "文档",  # "Documents"
    ]

    created_dirs = []

    for dirname in test_dirs:
        full_path = f"{base_dir}/{dirname}"
        print(f"Testing directory: {dirname!r}")

        # Test encoding to bytes (as would be needed for FAT filesystem)
        try:
            encoded = dirname.encode("utf-8")
            print(f"  UTF-8 encoded: {encoded!r}")
            print(f"  Byte length: {len(encoded)}")

            # Some FAT implementations might use different encoding
            # Try GB2312/GBK (common for Chinese systems)
            try:
                encoded_gbk = dirname.encode("gbk")
                print(f"  GBK encoded: {encoded_gbk!r}")
            except:
                print(f"  GBK encoding not available")

            # Try to create directory on SD card
            try:
                os.mkdir(full_path)
                print(f"  Created directory: {full_path}")
                created_dirs.append(dirname)

                # Create a test file in the directory
                test_file = f"{full_path}/test.txt"
                try:
                    with open(test_file, "w") as f:
                        f.write(f"Test file in {dirname}\n")
                    print(f"  Created test file: test.txt")
                except Exception as e:
                    print(f"  WARNING: Could not create test file: {e}")

            except OSError as e:
                print(f"  FAIL: Could not create directory: {e}")

        except Exception as e:
            print(f"  Error: {e}")

        print()

    # List the base directory to verify
    print(f"Listing {base_dir}:")
    try:
        files = os.listdir(base_dir)
        print(f"  Found {len(files)} items:")
        for item in files:
            print(f"    - {item!r}")
            print(f"      UTF-8 bytes: {item.encode('utf-8')!r}")

            # Check if this was one of our test directories
            if item in created_dirs:
                print(f"      PASS: Directory appears correctly")
            elif item in test_dirs:
                print(f"      NOTE: Directory found but name may differ")
    except Exception as e:
        print(f"  ERROR listing directory: {e}")

    print()

    # Verification: check which directories can be accessed
    print("Verification - accessing created directories:")
    for dirname in created_dirs:
        full_path = f"{base_dir}/{dirname}"
        try:
            contents = os.listdir(full_path)
            print(f"  PASS: Can access {dirname!r} - contains {len(contents)} items")
        except Exception as e:
            print(f"  FAIL: Cannot access {dirname!r}: {e}")

    print()
    print("Note: Directories are left on SD card for inspection")
    print(f"To clean up, delete: {base_dir}")
    print("Issue #15979 relates to FAT LFN (Long File Name) encoding")


if __name__ == "__main__":
    test_chinese_directory_names()
