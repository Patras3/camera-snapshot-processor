"""Constants for the Camera Snapshot Processor integration."""

DOMAIN = "camera_snapshot_processor"

# Configuration
CONF_SOURCE_CAMERA = "source_camera"
CONF_SOURCE_WIDTH = "source_width"
CONF_SOURCE_HEIGHT = "source_height"
CONF_ENTITY_NAME_SUFFIX = "entity_name_suffix"
CONF_WIDTH = "width"
CONF_HEIGHT = "height"
CONF_KEEP_RATIO = "keep_ratio"
CONF_QUALITY = "quality"
CONF_CROP_ENABLED = "crop_enabled"
CONF_CROP_X = "crop_x"
CONF_CROP_Y = "crop_y"
CONF_CROP_WIDTH = "crop_width"
CONF_CROP_HEIGHT = "crop_height"
CONF_RTSP_URL = "rtsp_url"

# Overlay configuration
CONF_DATETIME_ENABLED = "datetime_enabled"
CONF_DATETIME_FORMAT = "datetime_format"
CONF_DATETIME_POSITION = "datetime_position"
CONF_TEXT_ENABLED = "text_enabled"
CONF_TEXT_VALUE = "text_value"
CONF_TEXT_POSITION = "text_position"
CONF_OVERLAY_FONT_SIZE = "overlay_font_size"  # Legacy - kept for backward compatibility
CONF_DATETIME_FONT_SIZE = "datetime_font_size"
CONF_TEXT_FONT_SIZE = "text_font_size"
CONF_STATE_ICON_FONT_SIZE = "state_icon_font_size"
CONF_OVERLAY_COLOR = "overlay_color"
CONF_OVERLAY_BACKGROUND = "overlay_background"
CONF_STATE_ICON_BACKGROUND = "state_icon_background"

# State icons configuration (multiple icons supported)
CONF_STATE_ICONS = "state_icons"
CONF_ICON_ENTITY = "entity"
CONF_ICON_CONDITIONS = "conditions"
CONF_ICON_STATE = "state"
CONF_ICON_TEXT = "text"
CONF_ICON_COLOR = "color"
CONF_ICON_POSITION = "position"

# Performance configuration
CONF_RESIZE_ALGORITHM = "resize_algorithm"

# Defaults
DEFAULT_ENTITY_NAME_SUFFIX = "processed"
DEFAULT_WIDTH = 1920
DEFAULT_HEIGHT = 1080
DEFAULT_KEEP_RATIO = True
DEFAULT_QUALITY = 85
DEFAULT_CROP_ENABLED = False
DEFAULT_DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
DEFAULT_FONT_SIZE = 20  # Legacy
DEFAULT_DATETIME_FONT_SIZE = 24
DEFAULT_TEXT_FONT_SIZE = 20
DEFAULT_STATE_ICON_FONT_SIZE = 18
DEFAULT_OVERLAY_COLOR = [255, 255, 255]  # White - RGB list for ColorRGBSelector
DEFAULT_OVERLAY_BACKGROUND = "#00000000"
DEFAULT_STATE_ICON_BACKGROUND = "#00000000"  # Transparent by default
DEFAULT_RESIZE_ALGORITHM = "lanczos"  # lanczos (best quality) or bilinear (faster)

# Preview
PREVIEW_DIR = "www/camera_snapshot_processor"

# Positions
POSITION_TOP_LEFT = "top_left"
POSITION_TOP_RIGHT = "top_right"
POSITION_BOTTOM_LEFT = "bottom_left"
POSITION_BOTTOM_RIGHT = "bottom_right"

POSITIONS = [
    POSITION_TOP_LEFT,
    POSITION_TOP_RIGHT,
    POSITION_BOTTOM_LEFT,
    POSITION_BOTTOM_RIGHT,
]
