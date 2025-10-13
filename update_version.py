#!/usr/bin/env python3
"""
Helper script to update version across all files.

Usage: python update_version.py 0.10.0
"""

import json
import re
import sys
from pathlib import Path


def update_version(new_version):
    """Update version in manifest.json and panel.html"""

    # Validate version format (X.Y.Z)
    if not re.match(r'^\d+\.\d+\.\d+$', new_version):
        print(f"❌ Invalid version format: {new_version}")
        print("   Expected format: X.Y.Z (e.g., 0.10.0)")
        return 1

    # Update manifest.json
    manifest_path = Path("custom_components/camera_snapshot_processor/manifest.json")
    try:
        with open(manifest_path, "r") as f:
            manifest = json.load(f)

        old_version = manifest.get("version", "unknown")
        manifest["version"] = new_version

        with open(manifest_path, "w") as f:
            json.dump(manifest, f, indent=2)
            f.write("\n")  # Add trailing newline

        print(f"✓ Updated manifest.json: {old_version} → {new_version}")
    except Exception as e:
        print(f"❌ Error updating manifest.json: {e}")
        return 1

    # Update panel.html
    panel_path = Path("custom_components/camera_snapshot_processor/frontend/panel.html")
    try:
        with open(panel_path, "r") as f:
            panel_html = f.read()

        # Replace version in all resource URLs
        updated_html = re.sub(
            r'(src|href)="([^"]+\.(?:js|css))\?v=[^"]+"',
            rf'\1="\2?v={new_version}"',
            panel_html
        )

        with open(panel_path, "w") as f:
            f.write(updated_html)

        print(f"✓ Updated panel.html resource URLs to ?v={new_version}")
    except Exception as e:
        print(f"❌ Error updating panel.html: {e}")
        return 1

    print(f"\n✅ Version updated to {new_version}")
    print("   Run 'git add .' and commit to apply changes")
    return 0


def main():
    if len(sys.argv) != 2:
        print("Usage: python update_version.py <new_version>")
        print("Example: python update_version.py 0.10.0")
        return 1

    new_version = sys.argv[1]
    return update_version(new_version)


if __name__ == "__main__":
    sys.exit(main())
