#!/usr/bin/env python3
"""Test script for icon rendering - verifies MDI and emoji icons render correctly."""

import io
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

# Add the custom component to path
sys.path.insert(0, str(Path(__file__).parent))

from custom_components.camera_snapshot_processor.mdi_icons import (
    MDI_CODEPOINTS,
    get_mdi_character,
    is_mdi_icon,
)


def load_font(font_name: str, size: int):
    """Load a font from the fonts directory."""
    fonts_dir = Path(__file__).parent / "custom_components/camera_snapshot_processor/fonts"
    font_path = fonts_dir / font_name

    if not font_path.exists():
        print(f"❌ Font not found: {font_path}")
        return None

    try:
        font = ImageFont.truetype(str(font_path), size)
        print(f"✅ Loaded font: {font_name} at {size}pt")
        return font
    except Exception as e:
        print(f"❌ Failed to load font {font_name}: {e}")
        return None


def test_icon_rendering():
    """Test rendering of various icons."""
    print("\n" + "="*80)
    print("ICON RENDERING TEST")
    print("="*80)

    # Create test image (taller to fit all tests)
    img_width = 900
    img_height = 900
    image = Image.new('RGB', (img_width, img_height), color=(240, 240, 240))
    draw = ImageDraw.Draw(image, 'RGBA')

    # Load fonts
    emoji_font = load_font("NotoEmoji-Regular.ttf", 48)
    mdi_font = load_font("materialdesignicons-webfont.ttf", 48)
    text_font = load_font("NotoSans-Regular.ttf", 20)

    if not all([emoji_font, mdi_font, text_font]):
        print("\n❌ Cannot proceed without all fonts")
        return False

    # Test cases - focus on CCTV/security/alarm icons
    test_icons = [
        # (icon_name, icon_value, color, description)
        ("MDI CCTV", "mdi:cctv", (33, 150, 243), "CCTV camera"),
        ("MDI Motion Sensor", "mdi:motion-sensor", (255, 152, 0), "Motion detection"),
        ("MDI Alarm", "mdi:alarm", (244, 67, 54), "Alarm system"),
        ("MDI Spotlight", "mdi:spotlight-beam", (255, 235, 59), "Security spotlight"),
        ("MDI Lock Alert", "mdi:lock-alert", (211, 47, 47), "Lock with alert"),
        ("MDI Garage", "mdi:garage", (76, 175, 80), "Garage door"),
        ("MDI Smoke Detector", "mdi:smoke-detector", (158, 158, 158), "Smoke alarm"),
        ("MDI Bell Ring", "mdi:bell-ring", (255, 193, 7), "Doorbell"),
        ("MDI Eye Check", "mdi:eye-check", (139, 195, 74), "Visual detection OK"),
        ("MDI Camera Wireless", "mdi:camera-wireless", (3, 169, 244), "WiFi camera"),
    ]

    print(f"\n📝 Testing {len(test_icons)} icons:\n")

    y_position = 50
    x_start = 50
    success_count = 0

    for icon_name, icon_value, color, description in test_icons:
        print(f"Testing: {icon_name:20s} ({icon_value:20s}) - {description}")

        # Determine if MDI icon
        if is_mdi_icon(icon_value):
            # Get MDI character
            mdi_char = get_mdi_character(icon_value)
            if mdi_char:
                icon_to_render = mdi_char
                font_to_use = mdi_font
                print(f"  → MDI character: U+{ord(mdi_char):04X} = '{mdi_char}'")
                success_count += 1
            else:
                icon_to_render = "●"
                font_to_use = emoji_font
                print(f"  ❌ MDI icon not found in mappings, using fallback")
        else:
            icon_to_render = icon_value
            font_to_use = emoji_font
            print(f"  → Emoji/Unicode character")
            success_count += 1

        # Draw label
        draw.text((x_start, y_position), icon_name + ":", font=text_font, fill=(50, 50, 50))

        # Draw icon
        icon_x = x_start + 200
        draw.text((icon_x, y_position - 10), icon_to_render, font=font_to_use, fill=color)

        # Draw description
        draw.text((icon_x + 80, y_position + 5), description, font=text_font, fill=(100, 100, 100))

        y_position += 60

    # Add section title for icon+text test
    y_position += 20
    section_font = load_font("NotoSans-Regular.ttf", 16)
    draw.text((x_start, y_position), "Icon + Text Test:", font=section_font, fill=(0, 0, 0))
    y_position += 40

    # Test icon with text labels (simulate actual state icon rendering)
    icon_text_tests = [
        ("mdi:garage", "OPEN", (76, 175, 80)),
        ("mdi:lock", "LOCKED", (244, 67, 54)),
        ("mdi:motion-sensor", "MOTION", (255, 152, 0)),
    ]

    for icon_value, status_text, color in icon_text_tests:
        mdi_char = get_mdi_character(icon_value)
        if mdi_char:
            # Draw icon
            draw.text((x_start, y_position), mdi_char, font=mdi_font, fill=color)
            # Draw text next to icon using text font (NOT mdi font!)
            text_x = x_start + 60
            draw.text((text_x, y_position + 5), status_text, font=text_font, fill=(255, 255, 255))
            # Draw label
            label_x = text_x + 80
            draw.text((label_x, y_position + 8), f"← Icon+Text test", font=text_font, fill=(100, 100, 100))
            y_position += 55

    # Draw title
    title_font = load_font("NotoSans-Regular.ttf", 24)
    draw.text((img_width // 2 - 200, 10), "Icon Rendering Test - CCTV/Security", font=title_font, fill=(0, 0, 0))

    # Save image
    output_path = Path(__file__).parent / "test_icon_output.png"
    image.save(output_path)

    print(f"\n{'='*80}")
    print(f"✅ Test complete: {success_count}/{len(test_icons)} icons processed")
    print(f"📁 Output saved to: {output_path}")
    print(f"👁️  Open the image to visually verify icon rendering")
    print(f"{'='*80}\n")

    return True


def test_mdi_codepoints():
    """Test MDI codepoint mappings."""
    print("\n" + "="*80)
    print("MDI CODEPOINT MAPPINGS TEST")
    print("="*80)

    print(f"\n📊 Total MDI icons mapped: {len(MDI_CODEPOINTS)}")

    # Test specific CCTV/security icons
    test_mdi = [
        "cctv", "motion-sensor", "alarm", "spotlight-beam",
        "lock-alert", "garage", "smoke-detector", "bell-ring"
    ]

    print(f"\n🔍 Testing specific CCTV/Security MDI icons:\n")
    for icon_name in test_mdi:
        full_name = f"mdi:{icon_name}"
        char = get_mdi_character(full_name)
        if char:
            codepoint = ord(char)
            print(f"  ✅ {full_name:30s} → U+{codepoint:04X} ('{char}')")
        else:
            print(f"  ❌ {full_name:30s} → NOT FOUND")

    # List all available categories
    print(f"\n📋 Available MDI icon categories:\n")
    categories = {
        "CCTV & Cameras": ["cctv", "camera", "video", "webcam"],
        "Motion & Detection": ["motion-sensor", "eye", "walk", "radar"],
        "Alarms & Bells": ["alarm", "bell", "bell-ring", "bullhorn"],
        "Lights & Spotlights": ["spotlight", "flashlight", "lightbulb"],
        "Security & Locks": ["lock", "shield", "security"],
        "Doors & Access": ["door", "garage", "gate"],
        "Fire & Smoke": ["smoke-detector", "fire-alert", "fire-extinguisher"],
        "Power": ["power", "power-plug", "flash"],
        "Home": ["home", "sofa", "bed"],
    }

    for category, icons in categories.items():
        available = [f"mdi:{icon}" for icon in icons if icon in MDI_CODEPOINTS]
        print(f"  {category:20s}: {len(available)} icons - {', '.join(available[:3])}")

    print(f"\n{'='*80}\n")


def main():
    """Run all icon tests."""
    print("\n🧪 CAMERA SNAPSHOT PROCESSOR - ICON RENDERING TEST SUITE")

    # Test 1: MDI codepoint mappings
    test_mdi_codepoints()

    # Test 2: Visual rendering test
    success = test_icon_rendering()

    if success:
        print("✅ All tests completed successfully!")
        print("\n💡 Next steps:")
        print("   1. Open 'test_icon_output.png' to verify icons render correctly")
        print("   2. Check that MDI icons (home, garage, lock, etc.) show as proper glyphs")
        print("   3. Check that emoji icons (❤️, 💡) render correctly")
        print("   4. If icons appear as rectangles, there may be a font loading issue")
        return 0
    else:
        print("❌ Tests failed - check error messages above")
        return 1


if __name__ == "__main__":
    sys.exit(main())
