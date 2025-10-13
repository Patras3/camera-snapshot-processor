#!/usr/bin/env python3
"""Validation script for Camera Snapshot Processor."""
import json
import sys
from pathlib import Path

def validate_manifest():
    """Validate manifest.json."""
    print("Validating manifest.json...")
    manifest_path = Path("custom_components/camera_snapshot_processor/manifest.json")

    try:
        with open(manifest_path) as f:
            manifest = json.load(f)

        required_fields = ["domain", "name", "version", "documentation", "dependencies", "requirements"]
        missing = [field for field in required_fields if field not in manifest]

        if missing:
            print(f"  ❌ Missing required fields: {missing}")
            return False

        print(f"  ✅ Manifest valid (version {manifest['version']})")
        return True
    except Exception as e:
        print(f"  ❌ Error reading manifest: {e}")
        return False

def validate_imports():
    """Test if component syntax is valid."""
    print("\nValidating Python syntax...")
    import ast

    files_to_check = [
        "custom_components/camera_snapshot_processor/__init__.py",
        "custom_components/camera_snapshot_processor/const.py",
        "custom_components/camera_snapshot_processor/config_flow.py",
        "custom_components/camera_snapshot_processor/camera.py",
        "custom_components/camera_snapshot_processor/image_processor.py",
    ]

    all_valid = True
    for file_path in files_to_check:
        try:
            with open(file_path) as f:
                ast.parse(f.read(), filename=file_path)
            print(f"  ✅ {Path(file_path).name}")
        except SyntaxError as e:
            print(f"  ❌ {Path(file_path).name}: {e}")
            all_valid = False
        except Exception as e:
            print(f"  ⚠️  {Path(file_path).name}: {e}")

    return all_valid

def validate_strings():
    """Validate strings.json format."""
    print("\nValidating strings.json...")
    strings_path = Path("custom_components/camera_snapshot_processor/strings.json")

    try:
        with open(strings_path) as f:
            strings = json.load(f)

        # Check structure
        if "config" not in strings or "options" not in strings:
            print("  ❌ Missing config or options sections")
            return False

        print("  ✅ strings.json valid")
        return True
    except Exception as e:
        print(f"  ❌ Error reading strings: {e}")
        return False

def validate_files():
    """Check if all required files exist."""
    print("\nValidating file structure...")
    base = Path("custom_components/camera_snapshot_processor")

    required_files = [
        "__init__.py",
        "manifest.json",
        "const.py",
        "config_flow.py",
        "camera.py",
        "image_processor.py",
        "strings.json",
        "translations/en.json",
    ]

    all_exist = True
    for file in required_files:
        path = base / file
        if path.exists():
            print(f"  ✅ {file}")
        else:
            print(f"  ❌ Missing: {file}")
            all_exist = False

    return all_exist

def main():
    """Run all validations."""
    print("=" * 60)
    print("Camera Snapshot Processor - Component Validation")
    print("=" * 60)

    results = [
        validate_files(),
        validate_manifest(),
        validate_strings(),
        validate_imports(),
    ]

    print("\n" + "=" * 60)
    if all(results):
        print("✅ All validations passed!")
        print("=" * 60)
        return 0
    else:
        print("❌ Some validations failed")
        print("=" * 60)
        return 1

if __name__ == "__main__":
    sys.exit(main())
