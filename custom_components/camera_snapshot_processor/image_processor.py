"""Image processing logic for Camera Snapshot Processor."""

from __future__ import annotations

import asyncio
import io
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from homeassistant.core import HomeAssistant
from PIL import Image, ImageDraw, ImageFont

from .const import (
    CONF_CROP_ENABLED,
    CONF_CROP_HEIGHT,
    CONF_CROP_WIDTH,
    CONF_CROP_X,
    CONF_CROP_Y,
    CONF_DATETIME_ENABLED,
    CONF_DATETIME_FONT_SIZE,
    CONF_DATETIME_FORMAT,
    CONF_DATETIME_POSITION,
    CONF_HEIGHT,
    CONF_KEEP_RATIO,
    CONF_OVERLAY_BACKGROUND,
    CONF_OVERLAY_COLOR,
    CONF_OVERLAY_FONT_SIZE,
    CONF_QUALITY,
    CONF_RESIZE_ALGORITHM,
    CONF_STATE_ICONS,
    CONF_TEXT_ENABLED,
    CONF_TEXT_FONT_SIZE,
    CONF_TEXT_POSITION,
    CONF_TEXT_VALUE,
    CONF_WIDTH,
    DEFAULT_DATETIME_FONT_SIZE,
    DEFAULT_OVERLAY_BACKGROUND,
    DEFAULT_OVERLAY_COLOR,
    DEFAULT_QUALITY,
    DEFAULT_RESIZE_ALGORITHM,
    DEFAULT_STATE_ICON_FONT_SIZE,
    DEFAULT_TEXT_FONT_SIZE,
    POSITION_BOTTOM_LEFT,
    POSITION_BOTTOM_RIGHT,
    POSITION_TOP_LEFT,
    POSITION_TOP_RIGHT,
)
from .mdi_icons import get_mdi_character, is_mdi_icon

_LOGGER = logging.getLogger(__name__)


class ImageProcessor:
    """Process camera images with various transformations."""

    def __init__(self, hass: HomeAssistant, config: dict[str, Any]) -> None:
        """Initialize the image processor."""
        self.hass = hass
        self.config = config
        self._font_cache: dict[
            tuple[int, str], ImageFont.FreeTypeFont | ImageFont.ImageFont
        ] = {}

    async def process_image(self, image_bytes: bytes) -> bytes:
        """Process the image according to configuration.

        Offloads CPU-intensive PIL operations to a thread pool for better performance.
        """
        try:
            # Step 1: Offload decode/crop/resize to thread pool (CPU-intensive)
            image = await asyncio.to_thread(
                self._decode_and_transform_image, image_bytes
            )

            # Step 2: Apply overlays (may include async state lookups)
            image = await self._apply_overlays(image)

            # Step 3: Offload JPEG encoding to thread pool (CPU-intensive)
            processed_bytes = await asyncio.to_thread(self._encode_image, image)

            return processed_bytes

        except Exception as err:
            _LOGGER.error("Error processing image: %s", err)
            return image_bytes

    def _decode_and_transform_image(self, image_bytes: bytes) -> Image.Image:
        """Decode and transform image (runs in thread pool).

        This method handles CPU-intensive PIL operations:
        - Image decoding (JPEG → PIL Image)
        - Color conversion
        - Cropping
        - Resizing

        Returns PIL Image ready for overlay application.
        """
        # Load image
        image = Image.open(io.BytesIO(image_bytes))

        # Ensure RGB mode for processing
        if image.mode != "RGB":
            image = image.convert("RGB")

        # Apply crop if enabled
        if self.config.get(CONF_CROP_ENABLED, False):
            image = self._crop_image(image)

        # Resize image
        image = self._resize_image(image)

        return image

    def _encode_image(self, image: Image.Image) -> bytes:
        """Encode image to JPEG (runs in thread pool)."""
        output = io.BytesIO()
        quality = int(self.config.get(CONF_QUALITY, DEFAULT_QUALITY))
        image.save(output, format="JPEG", quality=quality, optimize=True)
        return output.getvalue()

    def _crop_image(self, image: Image.Image) -> Image.Image:
        """Crop the image based on configuration."""
        crop_x = int(self.config.get(CONF_CROP_X, 0))
        crop_y = int(self.config.get(CONF_CROP_Y, 0))
        crop_width = int(self.config.get(CONF_CROP_WIDTH, image.width))
        crop_height = int(self.config.get(CONF_CROP_HEIGHT, image.height))

        # Validate crop boundaries
        crop_x = max(0, min(crop_x, image.width))
        crop_y = max(0, min(crop_y, image.height))
        crop_width = min(crop_width, image.width - crop_x)
        crop_height = min(crop_height, image.height - crop_y)

        return image.crop((crop_x, crop_y, crop_x + crop_width, crop_y + crop_height))

    def _resize_image(self, image: Image.Image) -> Image.Image:
        """Resize the image based on configuration."""
        target_width = self.config.get(CONF_WIDTH)
        target_height = self.config.get(CONF_HEIGHT)
        keep_ratio = self.config.get(CONF_KEEP_RATIO, True)

        # Convert to int if provided (NumberSelector returns float)
        if target_width is not None:
            target_width = int(target_width)
        if target_height is not None:
            target_height = int(target_height)

        if not target_width and not target_height:
            return image

        current_width, current_height = image.size

        if keep_ratio:
            # Calculate size maintaining aspect ratio
            if target_width and target_height:
                # Both specified - fit within bounds
                ratio = min(
                    target_width / current_width, target_height / current_height
                )
                new_width = int(current_width * ratio)
                new_height = int(current_height * ratio)
            elif target_width:
                # Only width specified
                ratio = target_width / current_width
                new_width = target_width
                new_height = int(current_height * ratio)
            else:
                # Only height specified
                ratio = target_height / current_height
                new_width = int(current_width * ratio)
                new_height = target_height
        else:
            # Force exact dimensions
            new_width = int(target_width or current_width)
            new_height = int(target_height or current_height)

        # Choose resize algorithm based on config
        # LANCZOS: Best quality, slower (~50-100ms for 1920x1080)
        # BILINEAR: Good quality, faster (~20-40ms for 1920x1080)
        resize_algorithm = self.config.get(
            CONF_RESIZE_ALGORITHM, DEFAULT_RESIZE_ALGORITHM
        )
        if resize_algorithm == "bilinear":
            resampling = Image.Resampling.BILINEAR
        else:
            resampling = Image.Resampling.LANCZOS

        return image.resize((new_width, new_height), resampling)

    async def _apply_overlays(self, image: Image.Image) -> Image.Image:
        """Apply text and icon overlays to the image."""
        draw = ImageDraw.Draw(image, "RGBA")

        # Track which positions are used to add spacing
        position_counts = {
            pos: 0
            for pos in [
                POSITION_TOP_LEFT,
                POSITION_TOP_RIGHT,
                POSITION_BOTTOM_LEFT,
                POSITION_BOTTOM_RIGHT,
            ]
        }

        # Apply datetime overlay with its own font size
        if self.config.get(CONF_DATETIME_ENABLED, False):
            datetime_font_size = int(
                self.config.get(
                    CONF_DATETIME_FONT_SIZE,
                    self.config.get(CONF_OVERLAY_FONT_SIZE, DEFAULT_DATETIME_FONT_SIZE),
                )
            )
            datetime_font = self._get_font(datetime_font_size)
            datetime_format = self.config.get(CONF_DATETIME_FORMAT, "%Y-%m-%d %H:%M:%S")
            datetime_text = datetime.now().strftime(datetime_format)
            position = self.config.get(CONF_DATETIME_POSITION, POSITION_TOP_LEFT)
            self._draw_text(
                draw,
                image,
                datetime_text,
                position,
                datetime_font,
                position_counts[position],
            )
            position_counts[position] += 1

        # Apply custom text overlay with its own font size
        if self.config.get(CONF_TEXT_ENABLED, False):
            text_value = self.config.get(CONF_TEXT_VALUE, "")
            if text_value:
                text_font_size = int(
                    self.config.get(
                        CONF_TEXT_FONT_SIZE,
                        self.config.get(CONF_OVERLAY_FONT_SIZE, DEFAULT_TEXT_FONT_SIZE),
                    )
                )
                text_font = self._get_font(text_font_size)
                position = self.config.get(CONF_TEXT_POSITION, POSITION_TOP_RIGHT)
                self._draw_text(
                    draw,
                    image,
                    text_value,
                    position,
                    text_font,
                    position_counts[position],
                )
                position_counts[position] += 1

        # Apply state icon overlays
        state_icons = self.config.get(CONF_STATE_ICONS, [])
        for icon_config in state_icons:
            await self._draw_state_icon(draw, image, icon_config, position_counts)

        return image

    def _get_font(
        self, font_size: int, prefer_emoji: bool = False, use_mdi: bool = False
    ) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
        """Get a font with the specified size."""
        # Determine font type for caching
        if use_mdi:
            font_type = "mdi"
        elif prefer_emoji:
            font_type = "emoji"
        else:
            font_type = "text"

        cache_key = (font_size, font_type)
        if cache_key in self._font_cache:
            return self._font_cache[cache_key]

        integration_dir = Path(__file__).parent
        fonts_dir = integration_dir / "fonts"

        # Choose font order based on content type
        if use_mdi:
            # For MDI icons, use the MDI font exclusively
            font_files = [
                fonts_dir / "materialdesignicons-webfont.ttf",  # MDI font
            ]
        elif prefer_emoji:
            # For emoji/symbols, try emoji font first with fallback chain
            font_files = [
                fonts_dir / "NotoEmoji-Regular.ttf",  # Best emoji support
                fonts_dir / "NotoSans-Regular.ttf",  # Unicode fallback
                fonts_dir / "DejaVuSans.ttf",  # Classic fallback
            ]
        else:
            # For regular text, try text fonts first
            font_files = [
                fonts_dir / "NotoSans-Regular.ttf",  # Best text rendering
                fonts_dir / "DejaVuSans.ttf",  # Classic fallback
                fonts_dir / "NotoEmoji-Regular.ttf",  # Emoji support as fallback
            ]

        for font_path in font_files:
            try:
                if font_path.exists():
                    font = ImageFont.truetype(str(font_path), font_size)
                    self._font_cache[cache_key] = font
                    _LOGGER.debug(
                        "Loaded font %s at %dpt for %s",
                        font_path.name,
                        font_size,
                        font_type,
                    )
                    return font
                else:
                    _LOGGER.debug("Font file not found: %s", font_path)
            except Exception as err:
                _LOGGER.debug("Could not load font %s: %s", font_path.name, err)
                continue

        # Ultimate fallback
        _LOGGER.warning("Could not load any bundled fonts, using system default")
        default_font = ImageFont.load_default()
        self._font_cache[cache_key] = default_font
        return default_font

    def _draw_text(
        self,
        draw: ImageDraw.ImageDraw,
        image: Image.Image,
        text: str,
        position: str,
        font: ImageFont.FreeTypeFont | ImageFont.ImageFont,
        offset: int = 0,
        custom_color: str | list | None = None,
    ) -> None:
        """Draw text on the image at specified position."""
        color = custom_color or self.config.get(
            CONF_OVERLAY_COLOR, DEFAULT_OVERLAY_COLOR
        )
        bg_color = self.config.get(CONF_OVERLAY_BACKGROUND, DEFAULT_OVERLAY_BACKGROUND)

        # Normalize colors (convert RGB lists to hex strings if needed)
        color = self._normalize_color(color)
        bg_color = self._normalize_color(bg_color)

        # Convert hex colors to RGBA
        text_color = self._hex_to_rgba(color)
        background_color = self._hex_to_rgba(bg_color)

        # Get text bounding box
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        # Dynamic padding based on font size (minimum 8px, scales with text height)
        # This ensures text like 'p', 'g', 'y' with descenders are fully visible
        padding = max(8, int(text_height * 0.4))
        margin = padding  # Margin between image edge and background
        spacing = offset * (text_height + padding * 2)

        # Calculate position - add margin so background doesn't start at corner
        if position == POSITION_TOP_LEFT:
            x = margin + padding  # margin from edge + padding inside background
            y = margin + padding + spacing
        elif position == POSITION_TOP_RIGHT:
            x = image.width - text_width - margin - padding
            y = margin + padding + spacing
        elif position == POSITION_BOTTOM_LEFT:
            x = margin + padding
            y = image.height - text_height - margin - padding * 2 - spacing
        else:  # POSITION_BOTTOM_RIGHT
            x = image.width - text_width - margin - padding
            y = image.height - text_height - margin - padding * 2 - spacing

        # Draw background rectangle (only if not fully transparent)
        if background_color[3] > 0:
            draw.rectangle(
                [
                    x - padding,
                    y - padding,
                    x + text_width + padding,
                    y + text_height + padding,
                ],
                fill=background_color,
            )

        # Draw text
        draw.text((x, y), text, font=font, fill=text_color)

    async def _draw_state_icon(
        self,
        draw: ImageDraw.ImageDraw,
        image: Image.Image,
        icon_config: dict[str, Any],
        position_counts: dict[str, int],
    ) -> None:
        """Draw state icon overlay with full customization supporting multiple states."""
        entity_id = icon_config.get("entity")
        if not entity_id:
            return

        state = self.hass.states.get(entity_id)
        if not state:
            return

        current_state = state.state.lower()

        # Check for new multi-state configuration format
        state_rules = icon_config.get("state_rules", [])

        matched_rule = None

        if state_rules:
            # New format: iterate through state rules to find match
            for rule in state_rules:
                condition_type = rule.get("condition", "equals")
                condition_value = str(rule.get("value", "")).lower()

                _LOGGER.debug(
                    "Evaluating rule for entity %s (state=%s): condition=%s, value=%s",
                    entity_id,
                    current_state,
                    condition_type,
                    condition_value,
                )

                # Special case: any_state always matches
                if condition_type == "any_state":
                    matched_rule = rule
                    _LOGGER.debug("Rule matched: any_state (always matches)")
                    break
                elif condition_type == "equals":
                    if current_state == condition_value:
                        matched_rule = rule
                        break
                elif condition_type == "not_equals":
                    if current_state != condition_value:
                        matched_rule = rule
                        break
                elif condition_type == "in":
                    # Multiple values separated by comma
                    values = [v.strip().lower() for v in condition_value.split(",")]
                    if current_state in values:
                        matched_rule = rule
                        break
                elif condition_type == "not_in":
                    # Multiple values separated by comma
                    values = [v.strip().lower() for v in condition_value.split(",")]
                    if current_state not in values:
                        matched_rule = rule
                        break
                elif condition_type == "contains":
                    if condition_value in current_state:
                        matched_rule = rule
                        break
                elif condition_type == "not_contains":
                    if condition_value not in current_state:
                        matched_rule = rule
                        break
                elif condition_type in ["gt", "gte", "lt", "lte"]:
                    # Numeric comparisons
                    try:
                        current_val = float(current_state)
                        target_val = float(condition_value)
                        if condition_type == "gt" and current_val > target_val:
                            matched_rule = rule
                            break
                        elif condition_type == "gte" and current_val >= target_val:
                            matched_rule = rule
                            break
                        elif condition_type == "lt" and current_val < target_val:
                            matched_rule = rule
                            break
                        elif condition_type == "lte" and current_val <= target_val:
                            matched_rule = rule
                            break
                    except (ValueError, TypeError):
                        continue
        else:
            # Legacy format: backward compatibility with on/off states
            state_on = icon_config.get("state_on", "on")
            state_off = icon_config.get("state_off", "off")

            if current_state == state_on.lower():
                matched_rule = {
                    "icon": icon_config.get("icon_on", "💡"),
                    "text": icon_config.get("text_on", "ON"),
                    "icon_color": icon_config.get(
                        "icon_color_on", icon_config.get("color_on", [255, 215, 0])
                    ),
                    "text_color": icon_config.get("text_color_on", [255, 255, 255]),
                }
            elif current_state == state_off.lower():
                matched_rule = {
                    "icon": icon_config.get("icon_off", "🌑"),
                    "text": icon_config.get("text_off", "OFF"),
                    "icon_color": icon_config.get(
                        "icon_color_off", icon_config.get("color_off", [100, 100, 100])
                    ),
                    "text_color": icon_config.get("text_color_off", [150, 150, 150]),
                }

        # If no rule matched, check for default rule or return
        if not matched_rule:
            _LOGGER.debug(
                "No state rule matched for entity %s (state=%s), checking for default rule",
                entity_id,
                current_state,
            )
            # Look for default rule
            for rule in state_rules:
                if rule.get("is_default", False):
                    matched_rule = rule
                    _LOGGER.debug("Using default rule for entity %s", entity_id)
                    break

            if not matched_rule:
                _LOGGER.debug(
                    "No default rule found for entity %s, state icon will not be displayed",
                    entity_id,
                )
                return

        # Extract appearance from matched rule
        icon = matched_rule.get("icon", "")
        text = matched_rule.get("text", "")
        text_template = matched_rule.get("text_template", False)
        icon_color = matched_rule.get("icon_color", [255, 255, 255])
        text_color = matched_rule.get("text_color", [255, 255, 255])
        icon_background = matched_rule.get("icon_background", False)

        _LOGGER.debug(
            "Rendering state icon for entity %s: icon=%s, text=%s, "
            "icon_color=%s, text_color=%s, icon_background=%s, display_order=%s",
            entity_id,
            icon[:20] if icon else "None",  # Truncate icon to avoid log spam
            text if not text_template else f"{text[:20]}... (template)",
            icon_color,
            text_color,
            icon_background,
            matched_rule.get("display_order", "icon_first"),
        )

        # Render template if text_template is enabled
        if text_template and text:
            text = await self._render_template(text)
            if text is None:
                text = ""  # Fallback to empty string if template fails

        # Get font size for this state icon (with backward compatibility)
        icon_font_size = int(
            icon_config.get(
                "font_size",
                self.config.get(CONF_OVERLAY_FONT_SIZE, DEFAULT_STATE_ICON_FONT_SIZE),
            )
        )

        # Check if we have pre-computed codepoint from frontend (CDN translation)
        icon_codepoint = matched_rule.get("icon_codepoint")

        if icon_codepoint:
            # Use pre-computed codepoint directly - no lookup needed!
            # Frontend already translated mdi:icon-name → \U000F#### at config time
            icon = icon_codepoint
            icon_font = self._get_font(icon_font_size, use_mdi=True)
            _LOGGER.debug(
                "Using pre-computed MDI codepoint for rendering (CDN-translated)"
            )
        elif is_mdi_icon(icon):
            # Fallback: Use legacy lookup for old configs without icon_codepoint
            mdi_char = get_mdi_character(icon)
            if mdi_char:
                icon = mdi_char
                icon_font = self._get_font(icon_font_size, use_mdi=True)
                _LOGGER.debug(
                    "Using legacy MDI lookup for '%s' (consider re-saving config)", icon
                )
            else:
                # Icon not found in mappings, use emoji font with fallback
                _LOGGER.warning(
                    "MDI icon '%s' not found in mappings (install newer version or re-save config)",
                    icon,
                )
                icon = "●"  # Fallback to bullet point
                icon_font = self._get_font(icon_font_size, prefer_emoji=True)
        else:
            # Regular emoji or text
            icon_font = self._get_font(icon_font_size, prefer_emoji=True)

        # Get text font for labels and status text (always use text font, not icon font)
        text_font = self._get_font(icon_font_size, prefer_emoji=False)

        position = icon_config.get("position", POSITION_BOTTOM_RIGHT)
        offset = position_counts.get(position, 0)

        # Build parts list with their colors AND fonts
        parts = []

        # Add label if configured
        label = icon_config.get("label", "")
        show_label = icon_config.get("show_label", True)
        label_color = icon_config.get("label_color", text_color)

        if label and show_label:
            parts.append({"text": label + ":", "color": label_color, "font": text_font})

        # Get display order preference (default: icon first)
        display_order = matched_rule.get("display_order", "icon_first")

        # Build icon and text parts based on display order
        icon_part = None
        text_part = None

        if icon:
            icon_part = {
                "text": icon,
                "color": icon_color,
                "font": icon_font,
                "icon_background": icon_background,
            }

        if text:
            text_part = {"text": text, "color": text_color, "font": text_font}

        # Add icon and text in the specified order
        if display_order == "text_first":
            if text_part:
                parts.append(text_part)
            if icon_part:
                parts.append(icon_part)
        else:  # icon_first (default)
            if icon_part:
                parts.append(icon_part)
            if text_part:
                parts.append(text_part)

        # Draw multi-color text with per-part fonts
        if parts:
            self._draw_multicolor_text(draw, image, parts, position, offset)
            position_counts[position] = offset + 1

    def _draw_multicolor_text(
        self,
        draw: ImageDraw.ImageDraw,
        image: Image.Image,
        parts: list[dict[str, Any]],
        position: str,
        offset: int = 0,
    ) -> None:
        """Draw text with multiple colors and fonts.

        Each part can have different color and font.
        """
        if not parts:
            return

        bg_color = self.config.get(CONF_OVERLAY_BACKGROUND, DEFAULT_OVERLAY_BACKGROUND)
        bg_color = self._normalize_color(bg_color)
        background_color = self._hex_to_rgba(bg_color)

        # Calculate total dimensions - each part uses its own font
        total_width = 0
        max_height = 0
        part_widths = []

        for part in parts:
            part_font = part.get("font")
            if not part_font:
                _LOGGER.warning("Part missing font: %s", part)
                continue

            bbox = draw.textbbox(
                (0, 0), part["text"] + " ", font=part_font
            )  # Add space
            width = bbox[2] - bbox[0]
            height = bbox[3] - bbox[1]
            part_widths.append(width)
            total_width += width
            max_height = max(max_height, height)

        # Remove trailing space width from last part
        if part_widths and parts:
            last_font = parts[-1].get("font")
            if last_font:
                last_space_bbox = draw.textbbox((0, 0), " ", font=last_font)
                total_width -= last_space_bbox[2] - last_space_bbox[0]

        # Dynamic padding based on font size (minimum 8px, scales with text height)
        # This ensures text like 'p', 'g', 'y' with descenders are fully visible
        padding = max(8, int(max_height * 0.4))
        margin = padding  # Margin between image edge and background
        spacing = offset * (max_height + padding * 2)

        # Calculate starting position - add margin so background doesn't start at corner
        if position == POSITION_TOP_LEFT:
            x_start = margin + padding  # margin from edge + padding inside background
            y = margin + padding + spacing
        elif position == POSITION_TOP_RIGHT:
            x_start = image.width - total_width - margin - padding
            y = margin + padding + spacing
        elif position == POSITION_BOTTOM_LEFT:
            x_start = margin + padding
            y = image.height - max_height - margin - padding * 2 - spacing
        else:  # POSITION_BOTTOM_RIGHT
            x_start = image.width - total_width - margin - padding
            y = image.height - max_height - margin - padding * 2 - spacing

        # Draw background rectangle (only if not fully transparent)
        if background_color[3] > 0:
            draw.rectangle(
                [
                    x_start - padding,
                    y - padding,
                    x_start + total_width + padding,
                    y + max_height + padding,
                ],
                fill=background_color,
            )

        # Draw each part with its own color and font
        x = x_start
        for i, part in enumerate(parts):
            part_font = part.get("font")
            if not part_font:
                continue

            color = self._normalize_color(part["color"])
            rgba_color = self._hex_to_rgba(color)

            # Draw icon background if requested
            if part.get("icon_background", False):
                # Calculate icon bounding box
                text_bbox = draw.textbbox((x, y), part["text"], font=part_font)
                icon_width = text_bbox[2] - text_bbox[0]
                icon_height = text_bbox[3] - text_bbox[1]

                # Draw filled circle/ellipse behind the icon
                icon_size = max(icon_width, icon_height)
                # Add padding to make the circle slightly larger than the icon
                bg_padding = icon_size * 0.3
                center_x = x + icon_width / 2
                center_y = y + icon_height / 2
                radius = (icon_size + bg_padding) / 2

                # Draw filled circle in the icon color
                draw.ellipse(
                    [
                        center_x - radius,
                        center_y - radius,
                        center_x + radius,
                        center_y + radius,
                    ],
                    fill=rgba_color,
                )

                # Change icon color to white for contrast against background
                rgba_color = (255, 255, 255, 255)

            text_to_draw = part["text"]
            if i < len(parts) - 1:  # Add space after all parts except last
                text_to_draw += " "

            draw.text((x, y), text_to_draw, font=part_font, fill=rgba_color)
            x += part_widths[i]

    async def _render_template(self, template_str: str) -> str | None:
        """Render a Home Assistant template string.

        Args:
            template_str: The template string to render (e.g., "{{ states('sensor.temp') }}")

        Returns:
            The rendered template result as a string, or None if rendering fails
        """
        try:
            from homeassistant.helpers import template

            # Create template object
            tpl = template.Template(template_str, self.hass)

            # Render the template
            result = tpl.async_render(parse_result=False)

            # Convert result to string
            return str(result)
        except Exception as err:
            _LOGGER.warning("Failed to render template '%s': %s", template_str, err)
            return None

    @staticmethod
    def _normalize_color(color: str | list) -> str:
        """Convert color (RGB list or hex string) to hex string format."""
        if isinstance(color, list):
            # Convert RGB list [R, G, B] to hex string "#RRGGBB"
            if len(color) >= 3:
                return f"#{int(color[0]):02x}{int(color[1]):02x}{int(color[2]):02x}"
            else:
                return "#FFFFFF"  # Default to white
        return color  # Already a string

    @staticmethod
    def _hex_to_rgba(hex_color: str) -> tuple[int, int, int, int]:
        """Convert hex color to RGBA tuple."""
        hex_color = hex_color.lstrip("#")

        if len(hex_color) == 8:
            # RRGGBBAA
            r, g, b, a = (
                int(hex_color[0:2], 16),
                int(hex_color[2:4], 16),
                int(hex_color[4:6], 16),
                int(hex_color[6:8], 16),
            )
        elif len(hex_color) == 6:
            # RRGGBB
            r, g, b = (
                int(hex_color[0:2], 16),
                int(hex_color[2:4], 16),
                int(hex_color[4:6], 16),
            )
            a = 255
        else:
            # Default to white
            r, g, b, a = 255, 255, 255, 255

        return (r, g, b, a)
