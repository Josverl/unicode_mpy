#!/usr/bin/env python3
"""Quick test of mpremote copy with different file types."""

import subprocess
import sys

CONN = "socket://localhost:2218"
CONN = "auto"


def test_copy(src: str, name: str) -> bool:
    """Test copying a file."""
    dest = f":/test_copy/{name}"
    cmd = ["mpremote", "connect", CONN, "cp", src, dest]
    print(f"Testing: {name} ... ", end="", flush=True)
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30,
            encoding="utf-8",
            errors="replace",
        )
        if result.returncode == 0:
            print("PASS")
            return True
        else:
            print(f"FAIL: {result.stderr.strip()}")
            return False
    except Exception as e:
        print(f"ERROR: {e}")
        return False


# Test files - start with known good, then progressively more complex
tests = [
    ("README.md", "README.md"),  # ASCII only
    (r"Celtic_Gaelic\Dafydd_Llywelyn.txt", "Dafydd_Llywelyn.txt"),  # ASCII in subfolder
    (r"Celtic_Gaelic\Séamus_Ó_Murchú.txt", "Séamus_Ó_Murchú.txt"),  # Latin accents
    (r"Cyrillic\Владимир_Петров.txt", "Владимир_Петров.txt"),  # Cyrillic
    (r"East_Asian\さくら_はな.txt", "さくら_はな.txt"),  # Japanese hiragana
    (r"East_Asian\王明_李华.txt", "王明_李华.txt"),  # Chinese
    (r"Emoji_Symbols\😀_User_🎉.txt", "😀_User_🎉.txt"),  # Emoji
    (
        r"Ancient_Scripts\𓀀𓀁𓀂𓀃_hieroglyph.txt",
        "𓀀𓀁𓀂𓀃_hieroglyph.txt",
    ),  # Egyptian hieroglyphs (outside BMP)
    (
        r"Edge_Cases\H̸̡̪̯ë̵͎l̶̬̈l̴̞̅o̷̧͋_zalgo.txt",
        "H̸̡̪̯ë̵͎l̶̬̈l̴̞̅o̷̧͋_zalgo.txt",
    ),  # Zalgo text with combining marks
    (
        r"Edge_Cases\Hidden​Chars_zerowidth.txt",
        "Hidden​Chars_zerowidth.txt",
    ),  # Zero-width chars
    # Additional folders to test
    (r"Nordic_Icelandic\Þórður_Björk.txt", "Þórður_Björk.txt"),  # Icelandic thorn
    (r"Pacific_Polynesian\Hōkūle'a_Maui.txt", "Hōkūle_Maui.txt"),  # Hawaiian
    (r"South_Asian_Indic\राजेश_शर्मा.txt", "राजेश_शर्मा.txt"),  # Hindi Devanagari
    (r"Southeast_Asian\ประยุทธ์_ไทย.txt", "ประยุทธ์_ไทย.txt"),  # Thai
]

print("Quick Unicode mpremote test\n")
for src, name in tests:
    test_copy(src, name)
