# State Icons Feature - Complete Redesign

## Overview

The State Icons feature has been completely redesigned and fixed to provide a professional, intuitive way to add dynamic icons to camera snapshots based on Home Assistant entity states.

## Problems Fixed

### Backend Issues
1. **Font Rendering**: Fixed emoji and icon rendering that previously showed as rectangles
   - Added proper font file existence checking
   - Improved font fallback chain (NotoEmoji → NotoSans → DejaVu)
   - Added debug logging for font loading issues

2. **Multi-State Support**: Extended beyond simple on/off states
   - Support for unlimited state conditions
   - Multiple condition types (equals, in, contains, numeric comparisons)
   - Default/fallback state rules
   - Priority-based rule evaluation

3. **MDI Icon Support**: Added Material Design Icons support
   - MDI icon names (e.g., `mdi:lightbulb`) are converted to emoji equivalents
   - Extensible mapping system for common icons
   - Graceful fallback for unmapped icons

### Frontend UX Issues
1. **Professional Icon Picker**: Replaced manual emoji entry with modern picker
   - Emoji tab with categories (Smileys, Objects, Symbols, Nature)
   - Material Design Icons tab with searchable grid
   - Custom text/symbol input option
   - Search functionality for both emojis and MDI

2. **Multi-State Configuration**: Replaced limiting on/off model
   - Dynamic state rule builder
   - Add/edit/remove individual state rules
   - Visual preview of each rule
   - Drag-to-reorder support (UI prepared)
   - Inline editing for quick adjustments

3. **Entity-Aware Suggestions**: Smart state recommendations
   - Automatically detects entity domain (light, switch, sensor, etc.)
   - Shows common states for that entity type
   - One-click addition with sensible defaults
   - Domain-specific icon and color suggestions

## New Architecture

### Backend (Python)

**File**: `custom_components/camera_snapshot_processor/image_processor.py`

#### Key Changes:

1. **Enhanced Font Loading** (`_get_font` method):
```python
- Checks for font file existence before loading
- Improved error handling and logging
- Separate caching for emoji vs text fonts
```

2. **Multi-State Icon Rendering** (`_draw_state_icon` method):
```python
- Evaluates state_rules array in order
- Supports multiple condition types:
  - equals: Exact state match
  - in: Match any in comma-separated list
  - contains: Substring match
  - gt/gte/lt/lte: Numeric comparisons
- Backward compatible with legacy on/off format
- Default/fallback rule support
```

3. **MDI to Unicode Conversion** (`_convert_mdi_to_unicode` method):
```python
- Maps common MDI icon names to emoji
- Extensible dictionary-based approach
- Graceful fallback for unmapped icons
```

#### Configuration Format:

**New Format (multi-state):**
```json
{
  "entity": "light.living_room",
  "label": "Living Room",
  "show_label": true,
  "position": "bottom_right",
  "font_size": 18,
  "state_rules": [
    {
      "condition": "equals",
      "value": "on",
      "icon": "💡",
      "text": "ON",
      "icon_color": [255, 215, 0],
      "text_color": [255, 255, 255],
      "is_default": false
    },
    {
      "condition": "equals",
      "value": "off",
      "icon": "🌑",
      "text": "OFF",
      "icon_color": [100, 100, 100],
      "text_color": [150, 150, 150],
      "is_default": false
    }
  ]
}
```

**Legacy Format (still supported):**
```json
{
  "entity": "light.living_room",
  "state_on": "on",
  "state_off": "off",
  "icon_on": "💡",
  "icon_off": "🌑",
  "text_on": "ON",
  "text_off": "OFF",
  "icon_color_on": [255, 215, 0],
  "text_color_on": [255, 255, 255],
  "icon_color_off": [100, 100, 100],
  "text_color_off": [150, 150, 150]
}
```

### Frontend (JavaScript/HTML/CSS)

**New Files:**
- `state-icon-manager.js`: Complete icon picker and state rule builder
- Updated `panel.html`: New modal structure
- Updated `panel.js`: Integration with state icon manager
- Updated `styles.css`: Comprehensive styling for new components

#### State Icon Manager Class

**File**: `custom_components/camera_snapshot_processor/frontend/state-icon-manager.js`

**Key Features:**

1. **Icon Picker System**:
   - Tabbed interface (Emoji, MDI, Custom)
   - Category-based emoji browser
   - Searchable MDI icon grid
   - Custom text/symbol input
   - Callback-based selection for flexible integration

2. **State Rule Builder**:
   - Visual rule editor with live preview
   - Inline editing for quick adjustments
   - Add/edit/remove operations
   - Color pickers for icon and text
   - Condition type selector
   - Default/fallback rule support

3. **Entity-Aware Suggestions**:
   - Pre-configured state suggestions per domain
   - One-click rule creation
   - Smart default icons and colors
   - Domain detection from entity_id

#### Data Structures:

**Emoji Database:**
```javascript
EMOJI_DATABASE = {
  smileys: ['😊', '😀', '😃', ...],
  objects: ['💡', '🔌', '🔦', ...],
  symbols: ['⚡', '🔥', '💧', ...],
  nature: ['🌳', '🌲', '🌴', ...]
}
```

**MDI Icons:**
```javascript
MDI_ICONS = [
  { name: 'lightbulb', icon: '💡', label: 'Light Bulb' },
  { name: 'power', icon: '⚡', label: 'Power' },
  ...
]
```

**State Suggestions:**
```javascript
STATE_SUGGESTIONS = {
  light: ['on', 'off', 'unavailable'],
  switch: ['on', 'off', 'unavailable'],
  sensor: ['unavailable'],
  climate: ['heat', 'cool', 'auto', 'off', 'unavailable'],
  ...
}
```

## User Workflow

### Adding a State Icon

1. **Navigate to State Icons Tab**
   - Click "State Icons" tab in camera configuration

2. **Click "Add State Icon"**
   - Opens professional configuration modal

3. **Select Entity**
   - Search and select entity from dropdown
   - System automatically detects entity domain
   - Suggested states appear based on entity type

4. **Configure Label (Optional)**
   - Enter custom label text
   - Toggle label visibility

5. **Add State Rules**
   - Click "Add State Rule" or use suggested state buttons
   - For each rule:
     - Select condition type (equals, in, contains, etc.)
     - Enter state value
     - Click "Choose Icon" to open icon picker
     - Select icon from Emoji, MDI, or Custom tabs
     - Enter display text
     - Choose icon and text colors
     - Save rule

6. **Configure Position & Size**
   - Select position (top-left, top-right, bottom-left, bottom-right)
   - Adjust font size with slider

7. **Save Configuration**
   - Click "Save Configuration"
   - Preview updates automatically

### Example Use Cases

#### 1. Light with Three States
```
Entity: light.bedroom
States:
  - on (💡 yellow) → "ON"
  - off (🌑 gray) → "OFF"
  - unavailable (⚠️ red) → "UNAVAILABLE"
```

#### 2. Temperature Sensor with Ranges
```
Entity: sensor.outdoor_temp
States:
  - >= 25 (🔥 red) → "HOT"
  - >= 15 (☀️ yellow) → "WARM"
  - < 15 (❄️ blue) → "COLD"
```

#### 3. Alarm Control Panel
```
Entity: alarm_control_panel.home
States:
  - armed_away (🔒 red) → "ARMED"
  - armed_home (🏠 yellow) → "HOME"
  - disarmed (🔓 green) → "DISARMED"
  - triggered (⚠️ red flash) → "ALARM!"
```

## Technical Implementation Details

### Icon Rendering Pipeline

1. **Entity State Retrieval**:
   ```python
   state = self.hass.states.get(entity_id)
   current_state = state.state.lower()
   ```

2. **Rule Evaluation**:
   ```python
   for rule in state_rules:
       if matches_condition(rule, current_state):
           matched_rule = rule
           break
   ```

3. **MDI Conversion (if applicable)**:
   ```python
   if icon.startswith("mdi:"):
       icon = self._convert_mdi_to_unicode(icon)
   ```

4. **Font Selection**:
   ```python
   prefer_emoji = not icon.startswith("mdi:")
   font = self._get_font(font_size, prefer_emoji=prefer_emoji)
   ```

5. **Multi-Color Rendering**:
   ```python
   parts = [
       {"text": label, "color": label_color},
       {"text": icon, "color": icon_color},
       {"text": text, "color": text_color}
   ]
   self._draw_multicolor_text(draw, image, parts, position, font, offset)
   ```

### Backward Compatibility

The system maintains 100% backward compatibility with existing configurations:

1. **Legacy Detection**:
   - If `state_rules` is not present, system checks for `state_on`/`state_off`
   - Legacy format is automatically converted to rule format

2. **Conversion Function**:
   ```javascript
   function convertLegacyToStateRules(icon) {
       // Converts old on/off format to new state rules array
   }
   ```

3. **Migration Path**:
   - Existing configurations continue to work
   - Edit old icons to see them in new format
   - Save to automatically upgrade to new format

## CSS Class Reference

### Modal Styling
- `.modal-large`: Larger modal for complex configurations
- `.config-section`: Numbered configuration sections
- `.state-rule-item`: Individual state rule card
- `.state-rule-item.is-default`: Default/fallback rule styling

### Icon Picker
- `.icon-picker-tabs`: Tab navigation
- `.icon-picker-tab`: Individual tab button
- `.icon-picker-pane`: Tab content pane
- `.emoji-grid`: Emoji display grid
- `.mdi-grid`: MDI icon display grid

### State Rules
- `.state-rule-preview`: Visual preview of rule appearance
- `.state-rule-fields`: Rule configuration fields
- `.rule-condition-group`: Condition selector and value input
- `.icon-input-with-picker`: Icon input with picker button

### Suggested States
- `.suggested-states`: Container for suggestions
- `.suggested-state-btn`: Individual suggestion button

## Performance Considerations

1. **Font Caching**: Fonts are cached after first load
2. **Emoji Grid**: Limited to 50 items initially, loads more on scroll
3. **MDI Search**: Client-side filtering for instant results
4. **Rule Evaluation**: Short-circuits on first match
5. **Preview Updates**: Debounced to prevent excessive API calls

## Accessibility

1. **Keyboard Navigation**: All controls accessible via keyboard
2. **ARIA Labels**: Proper labeling for screen readers
3. **Color Contrast**: Meets WCAG AA standards
4. **Focus Indicators**: Clear focus states for all interactive elements

## Testing Recommendations

### Backend Testing
```bash
# Test emoji rendering
# Create state icon with emoji: 💡, 🌡️, 🔥

# Test MDI rendering
# Create state icon with: mdi:lightbulb, mdi:thermometer

# Test multi-state
# Create icon with 3+ states, verify correct icon shows

# Test numeric conditions
# Create sensor with > and < conditions
```

### Frontend Testing
```bash
# Test icon picker
# Open picker, switch tabs, search, select icons

# Test state rules
# Add, edit, remove rules
# Test different condition types

# Test entity suggestions
# Select different entity types
# Verify domain-specific suggestions appear
```

## Future Enhancements

1. **Drag-to-Reorder**: Implement drag-and-drop for rule priority
2. **Icon Animations**: Support for animated icons/GIFs
3. **Custom Icon Upload**: Allow users to upload custom icon images
4. **Template Support**: Use Home Assistant templates in text fields
5. **Advanced Conditions**: Regular expressions, multiple conditions per rule
6. **Icon Library Expansion**: More MDI icons, Font Awesome support
7. **Preview in Modal**: Live preview of icon appearance in modal
8. **Import/Export**: Share icon configurations between cameras
9. **Icon Groups**: Reusable icon sets for multiple cameras
10. **State History**: Show icon changes over time in preview

## Support and Troubleshooting

### Common Issues

**Icons appear as rectangles:**
- Verify NotoEmoji-Regular.ttf exists in fonts directory
- Check Home Assistant logs for font loading errors
- Try using emojis instead of MDI icons

**State not matching:**
- Verify entity_id is correct
- Check entity state in Home Assistant Developer Tools
- Ensure state value matches exactly (case-insensitive)
- Check rule order - first match wins

**Icon picker not appearing:**
- Check browser console for JavaScript errors
- Verify state-icon-manager.js is loaded
- Clear browser cache

**Colors not applying:**
- Verify RGB color format: [R, G, B] where values are 0-255
- Check for color picker value in hex format

### Debug Mode

Enable debug logging in Home Assistant:
```yaml
logger:
  default: warning
  logs:
    custom_components.camera_snapshot_processor.image_processor: debug
```

## Credits

This redesign addresses multiple UX and technical issues:
- Professional icon selection experience
- Flexible multi-state configuration
- Entity-aware smart suggestions
- Robust backend rendering
- Comprehensive documentation

Built with modern web standards and best practices for Home Assistant integration.
