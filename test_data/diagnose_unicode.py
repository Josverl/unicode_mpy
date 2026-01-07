#!/usr/bin/env python3
"""
Diagnose which Unicode filenames cause mpremote cp errors.
Run this from the test_data folder.
"""

import os
import subprocess
import sys
from pathlib import Path

# Configuration
MPREMOTE_CONNECTION = "socket://localhost:2218"
TEST_DIR = Path(".")
RESULTS_FILE = "unicode_diagnosis_results.txt"


def test_file_copy(filepath: Path) -> tuple[bool, str]:
    """Try to copy a single file using mpremote and return success/failure."""
    # Use a flat destination to avoid directory issues
    dest = f":/test_copy/{filepath.name}"

    cmd = ["mpremote", "connect", MPREMOTE_CONNECTION, "cp", str(filepath), dest]

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
            return True, ""
        else:
            error = result.stderr.strip() or result.stdout.strip()
            return False, error
    except subprocess.TimeoutExpired:
        return False, "TIMEOUT"
    except Exception as e:
        return False, str(e)


def analyze_filename(filename: str) -> dict:
    """Analyze a filename for potentially problematic characters."""
    info = {
        "filename": filename,
        "length": len(filename),
        "codepoints": [],
        "categories": set(),
        "potential_issues": [],
    }

    import unicodedata

    for char in filename:
        cp = ord(char)
        try:
            name = unicodedata.name(char, f"U+{cp:04X}")
            category = unicodedata.category(char)
        except:
            name = f"U+{cp:04X}"
            category = "??"

        info["codepoints"].append(
            {
                "char": char,
                "codepoint": f"U+{cp:04X}",
                "name": name,
                "category": category,
            }
        )
        info["categories"].add(category)

        # Flag potential issues
        if cp > 0xFFFF:  # Surrogate pairs needed (outside BMP)
            info["potential_issues"].append(f"Outside BMP: {char} (U+{cp:04X})")
        if category.startswith("M"):  # Combining marks
            info["potential_issues"].append(f"Combining mark: {char} (U+{cp:04X})")
        if category == "Cf":  # Format characters (zero-width, etc.)
            info["potential_issues"].append(f"Format char: U+{cp:04X}")
        if category == "Co":  # Private use
            info["potential_issues"].append(f"Private use: U+{cp:04X}")
        if char in "\x00\x01\x02\x03\x04\x05\x06\x07\x08\x0b\x0c\x0e\x0f":
            info["potential_issues"].append(f"Control char: U+{cp:04X}")

    return info


def main():
    print("=" * 70)
    print("Unicode Filename Diagnosis for mpremote")
    print("=" * 70)

    # Collect all files
    all_files = []
    for root, dirs, files in os.walk(TEST_DIR):
        # Skip hidden dirs and this script
        dirs[:] = [d for d in dirs if not d.startswith(".")]
        for f in files:
            if f.endswith(".py") or f == RESULTS_FILE:
                continue
            filepath = Path(root) / f
            all_files.append(filepath)

    print(f"\nFound {len(all_files)} files to test\n")

    # Test each file
    passed = []
    failed = []

    for i, filepath in enumerate(sorted(all_files), 1):
        rel_path = filepath.relative_to(TEST_DIR)
        print(f"[{i:3}/{len(all_files)}] Testing: {rel_path}", end=" ... ")
        sys.stdout.flush()

        success, error = test_file_copy(filepath)

        if success:
            print("PASS")
            passed.append(filepath)
        else:
            print("FAIL")
            failed.append((filepath, error))

    # Report results
    print("\n" + "=" * 70)
    print("RESULTS SUMMARY")
    print("=" * 70)
    print(f"\nPassed: {len(passed)}")
    print(f"Failed: {len(failed)}")

    if failed:
        print("\n" + "-" * 70)
        print("FAILED FILES - DETAILED ANALYSIS")
        print("-" * 70)

        with open(RESULTS_FILE, "w", encoding="utf-8") as f:
            f.write("Unicode Filename Diagnosis Results\n")
            f.write("=" * 70 + "\n\n")

            for filepath, error in failed:
                rel_path = filepath.relative_to(TEST_DIR)
                filename = filepath.name

                print(f"\n📁 Folder: {rel_path.parent}")
                print(f"📄 File:   {filename}")
                print(f"❌ Error:  {error[:200]}")

                # Analyze the filename
                analysis = analyze_filename(filename)

                if analysis["potential_issues"]:
                    print("⚠️  Potential issues:")
                    for issue in analysis["potential_issues"]:
                        print(f"    - {issue}")

                # Write to file
                f.write(f"\nFile: {rel_path}\n")
                f.write(f"Error: {error}\n")
                f.write("Codepoints:\n")
                for cp in analysis["codepoints"]:
                    f.write(
                        f"  {cp['char']} = {cp['codepoint']} ({cp['name']}) [{cp['category']}]\n"
                    )
                if analysis["potential_issues"]:
                    f.write("Issues:\n")
                    for issue in analysis["potential_issues"]:
                        f.write(f"  - {issue}\n")
                f.write("-" * 40 + "\n")

            print(f"\n\nDetailed results saved to: {RESULTS_FILE}")

    # Group failures by issue type
    if failed:
        print("\n" + "-" * 70)
        print("FAILURE CATEGORIES")
        print("-" * 70)

        outside_bmp = []
        combining = []
        format_chars = []
        other = []

        for filepath, error in failed:
            analysis = analyze_filename(filepath.name)
            issues = analysis["potential_issues"]

            categorized = False
            for issue in issues:
                if "Outside BMP" in issue:
                    outside_bmp.append(filepath.name)
                    categorized = True
                    break
                elif "Combining" in issue:
                    combining.append(filepath.name)
                    categorized = True
                    break
                elif "Format char" in issue:
                    format_chars.append(filepath.name)
                    categorized = True
                    break

            if not categorized:
                other.append(filepath.name)

        if outside_bmp:
            print(f"\n🔴 Outside BMP (U+10000+) - {len(outside_bmp)} files:")
            print(
                "   These use characters requiring surrogate pairs (emoji, ancient scripts)"
            )
            for name in outside_bmp[:10]:
                print(f"   • {name}")
            if len(outside_bmp) > 10:
                print(f"   ... and {len(outside_bmp) - 10} more")

        if combining:
            print(f"\n🟠 Combining marks - {len(combining)} files:")
            print("   These use combining diacritical marks (e.g., zalgo text)")
            for name in combining[:10]:
                print(f"   • {name}")

        if format_chars:
            print(f"\n🟡 Format characters - {len(format_chars)} files:")
            print("   These contain zero-width or other invisible format chars")
            for name in format_chars[:10]:
                print(f"   • {name}")

        if other:
            print(f"\n🔵 Other issues - {len(other)} files:")
            for name in other[:10]:
                print(f"   • {name}")


if __name__ == "__main__":
    main()
