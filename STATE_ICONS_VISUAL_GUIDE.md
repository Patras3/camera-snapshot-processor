# State Icons Feature - Visual User Guide

## Navigation Flow

```
Camera Configuration
    └─→ State Icons Tab
        └─→ "Add State Icon" Button
            └─→ Configuration Modal Opens
```

## Configuration Modal Structure

```
┌─────────────────────────────────────────────────────────────┐
│  Configure State Icon                                    [×] │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ 1. Select Entity                                      │   │
│  │ ┌──────────────────────────────────────────────────┐ │   │
│  │ │ Search for an entity...                      [⌄] │ │   │
│  │ └──────────────────────────────────────────────────┘ │   │
│  │ ✓ Living Room Light (light.living_room)              │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                               │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ 2. Label (Optional)                                   │   │
│  │ Label Text: [Living Room        ]  ☑ Show Label     │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                               │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ 3. State Rules                                        │   │
│  │ Define how the icon appears for different states...  │   │
│  │                                                        │   │
│  │ ┌────────────────────────────────────────────────┐   │   │
│  │ │ State = "on"                         [☰][✏️][🗑️] │   │
│  │ │ ┌──────────────┐  ┌─────────────────────────┐   │   │
│  │ │ │      💡      │  │ Condition: equals       │   │   │
│  │ │ │      ON      │  │ Value: on               │   │   │
│  │ │ └──────────────┘  │ Icon: 💡                │   │   │
│  │ │                    │ Text: ON                │   │   │
│  │ │                    │ Icon Color: [🟡]        │   │   │
│  │ │                    │ Text Color: [⚪]        │   │   │
│  │ │                    └─────────────────────────┘   │   │
│  │ └────────────────────────────────────────────────┘   │   │
│  │                                                        │   │
│  │ ┌────────────────────────────────────────────────┐   │   │
│  │ │ State = "off"                        [☰][✏️][🗑️] │   │
│  │ │ ┌──────────────┐  ┌─────────────────────────┐   │   │
│  │ │ │      🌑      │  │ Condition: equals       │   │   │
│  │ │ │     OFF      │  │ Value: off              │   │   │
│  │ │ └──────────────┘  │ Icon: 🌑                │   │   │
│  │ │                    │ Text: OFF               │   │   │
│  │ │                    │ Icon Color: [⚫]        │   │   │
│  │ │                    │ Text Color: [⚪]        │   │   │
│  │ │                    └─────────────────────────┘   │   │
│  │ └────────────────────────────────────────────────┘   │   │
│  │                                                        │   │
│  │ ┌────────────────────────────────────────────────┐   │   │
│  │ │ Suggested states for light:                    │   │
│  │ │ [on] [off] [unavailable]                      │   │
│  │ └────────────────────────────────────────────────┘   │   │
│  │                                                        │   │
│  │        [+ Add State Rule]                             │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                               │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ 4. Position & Size                                    │   │
│  │ Position: [Bottom Right ⌄]  Font Size: [18] pt      │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                               │
│  [Cancel]                          [Save Configuration]      │
└─────────────────────────────────────────────────────────────┘
```

## Icon Picker Modal

```
┌─────────────────────────────────────────────────────────────┐
│  Select Icon                                             [×] │
├─────────────────────────────────────────────────────────────┤
│  [Emoji] [Material Design Icons] [Custom Text]              │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  Search emoji...  [                                    ]     │
│                                                               │
│  [All] [😊 Smileys] [🔌 Objects] [⚡ Symbols] [🌳 Nature]  │
│                                                               │
│  ┌────────────────────────────────────────────────────────┐  │
│  │ 😊  😀  😃  😄  😁  😆  😅  🤣  😂  🙂  🙃  😉      │  │
│  │ 😌  😍  🥰  😘  😗  😙  😚  😋  😛  😝  😜  🤪      │  │
│  │ 💡  🔌  🔦  🕯️  💸  💰  💳  📱  💻  ⌚  📺  📷      │  │
│  │ ⚡  🔥  💧  💨  ☀️  🌙  ⭐  ✨  🌟  💫  ⚠️  🔴      │  │
│  │ 🌳  🌲  🌴  🌱  🌿  ☘️  🍀  🍁  🍂  🍃  🪴  🌾      │  │
│  └────────────────────────────────────────────────────────┘  │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

## Material Design Icons Tab

```
┌─────────────────────────────────────────────────────────────┐
│  Select Icon                                             [×] │
├─────────────────────────────────────────────────────────────┤
│  [Emoji] [Material Design Icons] [Custom Text]              │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  Search icons...  [                                    ]     │
│                                                               │
│  ┌────────────────────────────────────────────────────────┐  │
│  │ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐      │  │
│  │ │   💡    │ │   💡    │ │   🌑    │ │   ⚡    │      │  │
│  │ │ Light   │ │ Light   │ │ Light   │ │  Power  │      │  │
│  │ │  Bulb   │ │  Bulb   │ │  Bulb   │ │         │      │  │
│  │ │         │ │ Outline │ │  Off    │ │         │      │  │
│  │ └─────────┘ └─────────┘ └─────────┘ └─────────┘      │  │
│  │                                                         │  │
│  │ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐      │  │
│  │ │   🔌    │ │   👁️    │ │   🚪    │ │   🔒    │      │  │
│  │ │  Power  │ │ Motion  │ │  Door   │ │  Lock   │      │  │
│  │ │  Plug   │ │ Sensor  │ │         │ │         │      │  │
│  │ └─────────┘ └─────────┘ └─────────┘ └─────────┘      │  │
│  │                                                         │  │
│  │ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐      │  │
│  │ │   🌡️    │ │   💧    │ │   🔥    │ │   ❄️    │      │  │
│  │ │ Thermo- │ │  Water  │ │  Fire   │ │Snowflake│      │  │
│  │ │  meter  │ │         │ │         │ │         │      │  │
│  │ └─────────┘ └─────────┘ └─────────┘ └─────────┘      │  │
│  └────────────────────────────────────────────────────────┘  │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

## Custom Text Tab

```
┌─────────────────────────────────────────────────────────────┐
│  Select Icon                                             [×] │
├─────────────────────────────────────────────────────────────┤
│  [Emoji] [Material Design Icons] [Custom Text]              │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│                                                               │
│                                                               │
│            Custom Text/Symbol                                │
│                                                               │
│            ┌──────────────────────────┐                      │
│            │                          │                      │
│            └──────────────────────────┘                      │
│                                                               │
│            Enter any text, Unicode symbol,                   │
│            or special character                              │
│                                                               │
│                                                               │
│                  [Use This Text]                             │
│                                                               │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

## State Icons List View

```
┌──────────────────────────────────────────────────────────────┐
│  State Icons                                                  │
├──────────────────────────────────────────────────────────────┤
│                                                                │
│  ┌────────────────────────────────────────────────────────┐  │
│  │ light.living_room                     [✏️ Edit] [🗑️ Del] │  │
│  │ Label: Living Room | 2 state rules |                   │  │
│  │ Position: bottom_right | Font: 18pt                    │  │
│  └────────────────────────────────────────────────────────┘  │
│                                                                │
│  ┌────────────────────────────────────────────────────────┐  │
│  │ sensor.outdoor_temp                   [✏️ Edit] [🗑️ Del] │  │
│  │ 3 state rules | Position: top_right | Font: 20pt      │  │
│  └────────────────────────────────────────────────────────┘  │
│                                                                │
│  ┌────────────────────────────────────────────────────────┐  │
│  │ binary_sensor.front_door              [✏️ Edit] [🗑️ Del] │  │
│  │ Label: Front Door | 2 state rules |                    │  │
│  │ Position: top_left | Font: 16pt                        │  │
│  └────────────────────────────────────────────────────────┘  │
│                                                                │
│                      [+ Add State Icon]                       │
│                                                                │
└──────────────────────────────────────────────────────────────┘
```

## Example Output on Camera Image

```
┌────────────────────────────────────────────────────────────┐
│ 💡 Living Room: ON              🌡️ 22°C                   │
│                                                              │
│                                                              │
│                  [ Camera Image Content ]                   │
│                                                              │
│                                                              │
│                                                              │
│ 🚪 Front Door: CLOSED                  2024-01-15 14:30:25 │
└────────────────────────────────────────────────────────────┘
```

## State Rule Condition Types

### Equals
```
┌─────────────────────────────┐
│ Condition: equals           │
│ Value: on                   │
└─────────────────────────────┘
Matches when state == "on" exactly
```

### In (List)
```
┌─────────────────────────────┐
│ Condition: in               │
│ Value: on, home, active     │
└─────────────────────────────┘
Matches when state is one of: "on", "home", "active"
```

### Contains
```
┌─────────────────────────────┐
│ Condition: contains         │
│ Value: error                │
└─────────────────────────────┘
Matches when state contains "error" (e.g., "connection_error")
```

### Greater Than
```
┌─────────────────────────────┐
│ Condition: gt               │
│ Value: 25                   │
└─────────────────────────────┘
Matches when numeric state > 25 (e.g., temperature)
```

### Greater or Equal
```
┌─────────────────────────────┐
│ Condition: gte              │
│ Value: 20                   │
└─────────────────────────────┘
Matches when numeric state >= 20
```

### Less Than
```
┌─────────────────────────────┐
│ Condition: lt               │
│ Value: 15                   │
└─────────────────────────────┘
Matches when numeric state < 15
```

### Less or Equal
```
┌─────────────────────────────┐
│ Condition: lte              │
│ Value: 10                   │
└─────────────────────────────┘
Matches when numeric state <= 10
```

## Color Coding Guide

### Icon Colors (Suggestions)
- 🟡 Yellow/Gold: Active/On states (255, 215, 0)
- ⚫ Gray: Inactive/Off states (100, 100, 100)
- 🔴 Red: Error/Unavailable (255, 0, 0)
- 🟢 Green: Success/Open (76, 175, 80)
- 🔵 Blue: Cold/Low temperature (33, 150, 243)
- 🟠 Orange: Warning/Medium (255, 152, 0)
- 🟣 Purple: Special states (156, 39, 176)

### Text Colors (Common)
- ⚪ White: Primary text (255, 255, 255)
- ⚫ Black: Dark backgrounds (0, 0, 0)
- Gray: Dimmed text (150, 150, 150)

## Keyboard Shortcuts

### In Modal
- `Tab`: Navigate between fields
- `Escape`: Close modal
- `Enter`: Save (when in last field)

### In Icon Picker
- `Tab`: Navigate icons
- `Enter`: Select focused icon
- `Escape`: Close picker
- `Arrow Keys`: Navigate grid

## Mobile View

```
┌─────────────────────────┐
│ Configure State Icon [×]│
├─────────────────────────┤
│                         │
│ 1. Select Entity        │
│ [Search...           ⌄]│
│                         │
│ 2. Label                │
│ [Label Text         ]  │
│ ☑ Show Label           │
│                         │
│ 3. State Rules          │
│ ┌─────────────────────┐│
│ │ State = "on"        ││
│ │ [☰] [✏️] [🗑️]        ││
│ │ ┌─────────────────┐ ││
│ │ │      💡        │ ││
│ │ │      ON         │ ││
│ │ └─────────────────┘ ││
│ │ Condition: equals   ││
│ │ Value: on           ││
│ │ Icon: 💡           ││
│ │ Text: ON            ││
│ │ Colors: [🟡] [⚪]   ││
│ └─────────────────────┘│
│                         │
│ [+ Add State Rule]      │
│                         │
│ 4. Position & Size      │
│ Position: [Bottom Right]│
│ Font Size: [18] pt      │
│                         │
│ [Cancel] [Save]         │
│                         │
└─────────────────────────┘
```

## Tips and Best Practices

### 1. Start Simple
```
Begin with 2 states:
✓ on → 💡 Yellow
✓ off → 🌑 Gray
```

### 2. Add Error States
```
Always include unavailable:
✓ on → 💡 Yellow
✓ off → 🌑 Gray
✓ unavailable → ⚠️ Red
```

### 3. Use Meaningful Icons
```
Temperature sensor:
✓ >= 25 → 🔥 Hot
✓ >= 15 → ☀️ Warm
✓ < 15 → ❄️ Cold
```

### 4. Consider Labels
```
Multiple similar sensors:
✓ Show label: "Bedroom"
✓ Show label: "Living Room"
✓ Show label: "Kitchen"
```

### 5. Position Strategy
```
Top-left: Important status
Top-right: Secondary info
Bottom-left: Extra sensors
Bottom-right: Timestamp/stats
```

## Quick Reference Card

```
╔════════════════════════════════════════════════════════════╗
║                STATE ICONS QUICK REFERENCE                  ║
╠════════════════════════════════════════════════════════════╣
║ Entity Selection                                           ║
║  • Search by name or entity_id                            ║
║  • Auto-suggest based on domain                           ║
║                                                            ║
║ State Rules                                                ║
║  • equals: Exact match                                    ║
║  • in: Multiple values (comma-separated)                  ║
║  • contains: Substring match                              ║
║  • gt/gte/lt/lte: Numeric comparisons                    ║
║                                                            ║
║ Icon Sources                                               ║
║  • Emoji: 500+ categorized emojis                        ║
║  • MDI: 30+ Material Design Icons                        ║
║  • Custom: Any text/symbol                               ║
║                                                            ║
║ Colors                                                     ║
║  • Click color picker for each element                   ║
║  • Icon and text can have different colors              ║
║                                                            ║
║ Position                                                   ║
║  • Top-left, Top-right                                   ║
║  • Bottom-left, Bottom-right                             ║
║                                                            ║
║ Tips                                                       ║
║  • Start with suggested states                           ║
║  • Always include error/unavailable state                ║
║  • Test with actual entity states                        ║
║  • Use meaningful icons and colors                       ║
╚════════════════════════════════════════════════════════════╝
```
