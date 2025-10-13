# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Camera Snapshot Processor is a Home Assistant custom integration (HACS compatible) that processes camera snapshots with advanced image manipulation, overlay capabilities, and a professional web-based configuration UI. Version 0.9.0 (beta) targeting Home Assistant ≥ 2024.1.0, Python ≥ 3.11.

**Key Technologies:**
- Home Assistant custom integration architecture
- Pillow (PIL) for image processing
- Async Python for camera image handling
- RESTful API endpoints for web UI communication
- Jinja2 template rendering for dynamic text overlays
- Material Design Icons (MDI) font rendering

## Development Commands

### Setup and Installation

```bash
# Install development environment (if venv exists)
./venv/bin/pip install -r requirements.txt

# Or create new venv
python3 -m venv venv
source venv/bin/activate
pip install homeassistant pillow pre-commit
```

### Code Quality and Linting

```bash
# Install and setup pre-commit hooks
pip install pre-commit
pre-commit install

# Run pre-commit manually on all files
./venv/bin/pre-commit run --all-files

# Individual tools (as configured in .pre-commit-config.yaml)
black custom_components/  # Format code
isort custom_components/  # Sort imports
flake8 custom_components/ # Lint code (max-line-length=100)
```

### Testing

```bash
# Run all integration tests
./venv/bin/python test_integration.py

# Run API flow tests
./venv/bin/python test_api_flow.py

# Run frontend validation tests
./venv/bin/python test_frontend.py

# Run icon rendering tests
./venv/bin/python test_icon_rendering.py

# Validate manifest and file structure
python validate.py
```

### Local Development with Home Assistant

```bash
# Using docker-compose (recommended for testing)
docker-compose up -d

# Manual test environment setup (uses test_config/)
# See test-env.sh and TEST_ENV_README.md for details
```

### Git Workflow

```bash
# Pre-commit will run automatically on commit
git add .
git commit -m "Your commit message"

# If pre-commit modifies files, review and re-commit
git add .
git commit -m "Your commit message"
```

## Architecture

### Component Structure

The integration follows Home Assistant's standard architecture with these key components:

**Core Files:**
- `__init__.py` - Integration setup, API registration, frontend panel registration
- `const.py` - All configuration constants and defaults
- `manifest.json` - Integration metadata (domain, version, dependencies)
- `strings.json` / `translations/en.json` - UI text for config flow

**Main Components:**
- `config_flow.py` - Single-instance integration setup (redirects to web panel for camera config)
- `camera.py` - Camera entity platform, creates processed camera entities
- `image_processor.py` - Core image processing logic (crop, resize, overlays, templates)
- `api.py` - RESTful API endpoints for web UI communication
- `mdi_icons.py` - Material Design Icons mapping and character lookup

**Frontend (Web UI):**
- `frontend/panel.html` - Main panel container (iframe loaded by HA)
- `frontend/panel.js` - Main UI logic, API communication, preview generation
- `frontend/state-icon-manager.js` - State icon configuration UI module
- `frontend/styles.css` - UI styling

### Data Flow Architecture

1. **Config Entry Model:** Single integration entry with multi-camera storage:
   ```python
   entry.data = {
       "cameras": {
           "uuid-1": {camera_config_1},
           "uuid-2": {camera_config_2},
           ...
       }
   }
   ```

2. **Camera Entity Creation:** Each camera in `entry.data["cameras"]` becomes a `SnapshotProcessorCamera` entity

3. **Image Processing Pipeline:**
   - `Camera.async_camera_image()` called by HA
   - Fetch source camera snapshot
   - Pass to `ImageProcessor.process_image()`
   - Apply: crop → resize → overlays (datetime, text, state icons)
   - Return processed JPEG bytes

4. **Web UI Communication:**
   - Frontend → API endpoints (REST)
   - API updates config entry data
   - Config entry update triggers entity reload
   - Entities observe config changes via `add_update_listener()`

### Key API Endpoints

All under `/api/camera_snapshot_processor/`:
- `GET /cameras` - List all configured cameras
- `POST /cameras` - Add new camera
- `GET /cameras/{id}` - Get camera config
- `PUT /cameras/{id}` - Update camera config
- `DELETE /cameras/{id}` - Remove camera
- `POST /cameras/{id}/preview` - Generate preview with temp config
- `GET /cameras/{id}/source` - Get source camera image + dimensions
- `GET /entities` - List all HA entities (for state icon config)
- `GET /available_cameras` - List available source cameras

### State Icons System

State icons support complex multi-state rules with conditions:

**Condition Types:**
- `equals` / `not_equals` - Exact state matching
- `in` / `not_in` - List matching (comma-separated)
- `contains` / `not_contains` - Substring matching
- `gt` / `gte` / `lt` / `lte` - Numeric comparisons

**State Rule Structure:**
```python
{
    "entity": "sensor.temperature",
    "label": "Temp",
    "position": "bottom_right",
    "font_size": 18,
    "state_rules": [
        {
            "condition": "gt",
            "value": "25",
            "icon": "mdi:thermometer-high",
            "text": "Hot",
            "text_template": True,  # Enable Jinja2 rendering
            "icon_color": [255, 0, 0],
            "text_color": [255, 255, 255],
            "icon_background": True,  # Draw filled circle behind icon
            "is_default": False
        },
        # ... more rules
    ]
}
```

### Template Rendering

Text overlays and state icon text support Home Assistant Jinja2 templates:
- Rendered via `homeassistant.helpers.template.Template`
- Access to all HA template functions (`states()`, `state_attr()`, `relative_time()`, etc.)
- Real-time preview in web UI with error detection
- Async rendering in image processor

### Font System

The integration bundles fonts in `custom_components/camera_snapshot_processor/fonts/`:
- `DejaVuSans.ttf` - Classic text font
- `NotoSans-Regular.ttf` - Modern text with Unicode support
- `NotoEmoji-Regular.ttf` - Emoji support
- `materialdesignicons-webfont.ttf` - Material Design Icons font

Font selection logic (`_get_font()`):
- MDI icons: Use MDI font exclusively
- Emoji/symbols: NotoEmoji → NotoSans → DejaVuSans
- Regular text: NotoSans → DejaVuSans → NotoEmoji
- Font instances cached by (size, type) tuple

### MDI Icon System (CDN-Powered)

**Architecture:**
- Frontend loads full MDI metadata from CDN: `https://cdn.jsdelivr.net/npm/@mdi/svg@7.4.47/meta.json`
- Translation happens **once at config save time** (frontend → backend)
- Backend receives pre-computed Unicode characters for zero runtime overhead

**Translation Flow:**
```javascript
// Frontend (state-icon-manager.js)
translateMDIToCodepoint('mdi:home') {
    // 1. Lookup in meta.json: "home" → "F02DC"
    // 2. Convert to Unicode: parseInt("F02DC", 16) → chr(0xF02DC)
    // 3. Store in config: rule.icon_codepoint = "\U000F02DC"
}
```

```python
# Backend (image_processor.py)
icon_codepoint = matched_rule.get("icon_codepoint")
if icon_codepoint:
    icon = icon_codepoint  # Use directly - no lookup!
    icon_font = self._get_font(icon_font_size, use_mdi=True)
```

**Benefits:**
- ✅ Full MDI icon set available
- ✅ Zero runtime performance overhead (translation at config-time)
- ✅ No git bloat (CDN-loaded, not bundled)
- ✅ Always up-to-date (CDN ensures latest icons)
- ✅ Backward compatible (fallback to `mdi_icons.py` dict for old configs)

**UI Features:**
- Loading banner while fetching meta.json
- Search across all icons
- Curated categories for quick access

## Important Implementation Details

### Home Assistant Version Compatibility

- **Minimum HA version:** 2024.1.0 (2025.9.4 in hacs.json)
- **Breaking change in 2025.12:** Deprecation of `self.config_entry` assignment in OptionsFlowHandler
- Current code already compliant (no direct assignment to `self.config_entry`)

### Config Flow vs Web Panel

- **Initial setup:** Uses HA config flow (single instance, no camera selection)
- **Camera configuration:** Done through web panel (`/camera_snapshot_processor`)
- **Options flow:** Redirects to web panel (abort with `reason="use_panel"`)
- This design provides better UX with live preview unavailable in config flow

### Image Processing Performance

- All processing in-memory (no disk I/O)
- No caching - always fresh images
- Font instances cached for performance
- Async operations for camera image fetching
- JPEG compression with configurable quality (1-100%)

### Panel Registration

Panel registered in `async_setup_entry()`:
```python
frontend.async_register_built_in_panel(
    hass,
    component_name="iframe",
    sidebar_icon="mdi:camera-enhance",
    frontend_url_path=DOMAIN,
    config={"url": f"/{DOMAIN}_panel/panel.html"},
    require_admin=True,
)
```

### Static File Serving

Frontend files served via `async_register_static_paths()`:
```python
await hass.http.async_register_static_paths([
    StaticPathConfig(
        url_path=f"/{DOMAIN}_panel",
        path=str(frontend_path),
        cache_headers=False,
    )
])
```

## Common Development Tasks

### Adding a New Configuration Option

1. Add constant to `const.py` (e.g., `CONF_NEW_OPTION`, `DEFAULT_NEW_OPTION`)
2. Update camera config structure in `api.py` (if needed in default config)
3. Add to `ImageProcessor` config handling in `image_processor.py`
4. Add UI controls in `frontend/panel.js` or `frontend/panel.html`
5. Update `strings.json` for any user-facing text
6. Add to pre-commit tests if validation needed

### Adding a New API Endpoint

1. Create view class in `api.py` extending `HomeAssistantView`
2. Define `url`, `name`, `requires_auth` attributes
3. Implement HTTP methods (`get`, `post`, `put`, `delete`)
4. Register in `setup_api()` function
5. Update frontend to call new endpoint
6. Add tests to `test_api_flow.py`

### Modifying Image Processing

All image processing happens in `ImageProcessor` class:
- `process_image()` - Main pipeline orchestration
- `_crop_image()` - Cropping logic
- `_resize_image()` - Resizing with aspect ratio handling
- `_apply_overlays()` - Overlay rendering orchestration
- `_draw_state_icon()` - State icon rendering with rule matching
- `_draw_multicolor_text()` - Multi-color text with per-part fonts
- `_render_template()` - Jinja2 template rendering

### Working with State Icons

State icon configuration stored in `CONF_STATE_ICONS` array in camera config. Each state icon has:
- `entity` - Entity ID to monitor
- `label` - Optional label text
- `position` - Corner placement (top_left, top_right, bottom_left, bottom_right)
- `font_size` - Icon and text size
- `show_label` - Show/hide label
- `label_color` - Label color
- `state_rules` - Array of condition-based rules

Rule matching is first-match-wins, with fallback to default rule if specified.

### Working with MDI Icons

**Full MDI icon set is automatically available** via CDN. No manual mapping needed!

**For adding curated icons** (quick-access category):
1. Update `MDI_ICONS` dict in `state-icon-manager.js`
2. Organize by category (CCTV, Motion, Alarms, Security, etc.)
3. Format: `{ name: 'icon-name', label: 'Display Label' }`
4. Icons render automatically from CDN CSS

**Legacy fallback** (`mdi_icons.py`):
- Kept for backward compatibility with old configs
- Used when `icon_codepoint` is not available
- Contains manually-mapped icons for legacy support
- Only needed for configs created before CDN implementation

## Code Style and Conventions

- **Line length:** 100 characters (flake8)
- **Import sorting:** isort with black profile
- **Formatting:** black (Python 3.12)
- **Type hints:** Use where possible (especially public APIs)
- **Async/await:** Required for all I/O operations
- **Logging:** Use `_LOGGER` with appropriate levels (debug, info, warning, error)
- **Error handling:** Try/except with logging, graceful degradation

## Testing Strategy

The project uses custom test scripts (not pytest) due to Home Assistant mocking complexity:

- `test_integration.py` - Core integration structure validation (11 tests)
- `test_api_flow.py` - API endpoint testing with mock requests
- `test_frontend.py` - Frontend file validation and structure checks
- `test_icon_rendering.py` - Icon rendering and font loading tests

Pre-commit hooks run all tests automatically on commit.

## Deployment and Release

1. Update version using helper script:
   ```bash
   python update_version.py 0.10.0
   ```
   This automatically updates:
   - `manifest.json` version
   - Resource cache-busting parameters in `panel.html` (?v=0.10.0)

2. Update `README.md` changelog section
3. Run all tests: `./venv/bin/python test_integration.py`
4. Commit changes (pre-commit will validate version consistency)
5. Tag release: `git tag -a v0.10.0 -m "Release 0.10.0"`
6. Users install via HACS custom repository

**Version Validation:**
- Pre-commit hook (`validate_version.py`) ensures all resource URLs have correct `?v=X.Y.Z` parameter
- Prevents commits if version mismatch detected between `manifest.json` and `panel.html`
- Ensures browser cache busting works correctly after updates

## Known Issues and Limitations

- Beta version (0.9.0) - active development
- No automated unit tests (uses custom test scripts)
- Frontend is vanilla JS (no framework) - intentional for simplicity
- No persistent caching of processed images
- State icon rules evaluated on every image render
- CDN required for full MDI icon set (falls back to curated icons if offline)
