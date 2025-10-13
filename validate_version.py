#!/usr/bin/env python3
"""
Validate that frontend resource URLs have correct version cache busting parameter.

This ensures that ?v=X.Y.Z in panel.html matches the version in manifest.json.
"""

import json
import re
import sys
from pathlib import Path


def main():
    # Read manifest.json version
    manifest_path = Path("custom_components/camera_snapshot_processor/manifest.json")
    try:
        with open(manifest_path, "r") as f:
            manifest = json.load(f)
            manifest_version = manifest.get("version")
    except Exception as e:
        print(f"❌ Error reading manifest.json: {e}")
        return 1

    if not manifest_version:
        print("❌ No version found in manifest.json")
        return 1

    print(f"✓ Manifest version: {manifest_version}")

    # Read panel.html and check version parameters
    panel_path = Path("custom_components/camera_snapshot_processor/frontend/panel.html")
    try:
        with open(panel_path, "r") as f:
            panel_html = f.read()
    except Exception as e:
        print(f"❌ Error reading panel.html: {e}")
        return 1

    # Find all resource URLs with version parameters
    # Matches: src="file.js?v=0.9.0" or href="file.css?v=0.9.0"
    version_pattern = r'(src|href)="([^"]+\.(?:js|css))\?v=([^"]+)"'
    matches = re.findall(version_pattern, panel_html)

    if not matches:
        print("❌ No versioned resources found in panel.html")
        print("   Expected resources with ?v=X.Y.Z parameter")
        return 1

    errors = []
    for attr, resource, version in matches:
        if version != manifest_version:
            errors.append(
                f"   {resource}?v={version} (expected ?v={manifest_version})"
            )
        else:
            print(f"✓ {resource}?v={version}")

    if errors:
        print("\n❌ Version mismatch found:")
        for error in errors:
            print(error)
        print(f"\n💡 Update panel.html to use ?v={manifest_version}")
        return 1

    print(f"\n✅ All resource versions match manifest.json ({manifest_version})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
