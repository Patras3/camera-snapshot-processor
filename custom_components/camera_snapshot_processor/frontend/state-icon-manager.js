// State Icon Manager - Professional Icon Picker and Multi-State Configuration
// MDI-only version with comprehensive icon support and background fill options
(function() {
    'use strict';

    // ==================== Data ====================

    // Helper function to render MDI icon using CSS classes
    function renderMDIIcon(iconName) {
        const name = iconName.replace('mdi:', '');
        return `<i class="mdi mdi-${name}"></i>`;
    }

    // Suggested icons for quick access (collapsed from previous categories)
    const SUGGESTED_ICONS = [
        'cctv', 'camera', 'video', 'webcam',
        'motion-sensor', 'eye', 'radar',
        'alarm', 'alarm-light', 'bell', 'bell-ring',
        'lightbulb', 'lightbulb-on', 'lightbulb-off', 'light-switch', 'spotlight',
        'lock', 'lock-open', 'shield', 'shield-check', 'security',
        'door', 'door-open', 'door-closed', 'garage', 'garage-open', 'gate',
        'window-open', 'window-closed',
        'smoke-detector', 'fire-alert', 'fire',
        'power', 'power-plug', 'flash',
        'thermometer', 'snowflake', 'fan', 'air-conditioner',
        'weather-sunny', 'weather-cloudy', 'weather-rainy',
        'home', 'sofa', 'bed', 'stove', 'fridge',
        'washing-machine', 'robot-vacuum',
        'television', 'speaker', 'music',
        'check', 'close', 'alert', 'information',
        'arrow-up', 'arrow-down', 'arrow-left', 'arrow-right',
        'car',
    ];

    // Dynamic categories based on MDI tags
    const DYNAMIC_CATEGORIES = [
        { id: 'home', label: 'Home', tags: ['home', 'house'] },
        { id: 'light', label: 'Lights', tags: ['light', 'lamp', 'bulb'] },
        { id: 'lock', label: 'Security', tags: ['lock', 'security', 'shield', 'alarm'] },
        { id: 'camera', label: 'Cameras', tags: ['camera', 'video', 'cctv'] },
        { id: 'door', label: 'Doors', tags: ['door', 'gate', 'garage'] },
        { id: 'weather', label: 'Weather', tags: ['weather', 'cloud', 'rain', 'sun'] },
        { id: 'device', label: 'Devices', tags: ['device', 'phone', 'computer', 'tablet'] },
        { id: 'media', label: 'Media', tags: ['music', 'video', 'play', 'speaker'] },
        { id: 'arrow', label: 'Arrows', tags: ['arrow', 'chevron', 'navigate'] },
        { id: 'alert', label: 'Alerts', tags: ['alert', 'warning', 'error', 'information'] },
    ];

    // Entity domain to state suggestions mapping
    const STATE_SUGGESTIONS = {
        light: ['on', 'off', 'unavailable'],
        switch: ['on', 'off', 'unavailable'],
        binary_sensor: ['on', 'off', 'unavailable'],
        sensor: ['unavailable'],
        climate: ['heat', 'cool', 'auto', 'off', 'unavailable'],
        cover: ['open', 'closed', 'opening', 'closing', 'unavailable'],
        lock: ['locked', 'unlocked', 'jammed', 'unavailable'],
        fan: ['on', 'off', 'unavailable'],
        media_player: ['playing', 'paused', 'idle', 'off', 'unavailable'],
        alarm_control_panel: ['armed_home', 'armed_away', 'armed_night', 'disarmed', 'pending', 'triggered', 'unavailable'],
        vacuum: ['cleaning', 'docked', 'returning', 'error', 'unavailable'],
        person: ['home', 'not_home', 'unavailable'],
    };

    // State icon manager class
    window.StateIconManager = class {
        constructor() {
            this.currentIconCallback = null;
            this.currentRuleIndex = null;
            this.stateRules = [];
            this.selectedEntity = null;
            this.mdiMetadata = null; // Will hold all 7,447 MDI icons
            this.mdiMetadataLoading = false;
            this.setupIconPicker();
            this.setupStateRuleBuilder();
            this.loadMDIMetadata(); // Load full icon list from CDN
        }

        // ==================== MDI Metadata (CDN) ====================

        async loadMDIMetadata() {
            if (this.mdiMetadataLoading || this.mdiMetadata) return;

            this.mdiMetadataLoading = true;

            // Show loading banner
            this.showMDILoadingBanner(true);

            try {
                const response = await fetch('https://cdn.jsdelivr.net/npm/@mdi/svg@7.4.47/meta.json');
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }

                this.mdiMetadata = await response.json();
            } catch (error) {
                // Failed to load full icon set - fallback to curated icons
                this.mdiMetadata = null;
            } finally {
                this.mdiMetadataLoading = false;
                // Hide loading banner after load (success or failure)
                setTimeout(() => this.showMDILoadingBanner(false), 500);
            }
        }

        showMDILoadingBanner(show) {
            const banner = document.getElementById('mdi-loading-banner');
            if (banner) {
                banner.style.display = show ? 'flex' : 'none';
            }
        }

        /**
         * Translate MDI icon name to Unicode character for backend rendering.
         * @param {string} iconName - Icon name like "mdi:home" or "home"
         * @returns {string|null} - Unicode character (e.g., actual icon char) or null if not found
         */
        translateMDIToCodepoint(iconName) {
            if (!iconName) return null;

            // Remove "mdi:" prefix if present
            const name = iconName.startsWith('mdi:') ? iconName.substring(4) : iconName;

            // Try to find in full metadata first
            if (this.mdiMetadata) {
                const icon = this.mdiMetadata.find(i => i.name === name);
                if (icon && icon.codepoint) {
                    // Convert hex codepoint "F02DC" to actual Unicode character
                    // This character will be properly encoded in JSON and decoded in Python
                    const codepointInt = parseInt(icon.codepoint, 16);
                    const unicodeChar = String.fromCodePoint(codepointInt);
                    return unicodeChar;
                }
            }

            // Icon not found in metadata
            return null;
        }

        // ==================== Icon Picker ====================

        setupIconPicker() {
            // Icon picker tab switching
            document.querySelectorAll('.icon-picker-tab').forEach(tab => {
                tab.addEventListener('click', () => {
                    document.querySelectorAll('.icon-picker-tab').forEach(t => t.classList.remove('active'));
                    document.querySelectorAll('.icon-picker-pane').forEach(p => p.classList.remove('active'));

                    tab.classList.add('active');
                    document.getElementById(`icon-picker-${tab.dataset.tab}`).classList.add('active');
                });
            });

            // MDI category selection
            document.querySelectorAll('.mdi-category').forEach(btn => {
                btn.addEventListener('click', () => {
                    document.querySelectorAll('.mdi-category').forEach(b => b.classList.remove('active'));
                    btn.classList.add('active');
                    this.renderMDIGrid(btn.dataset.category);
                });
            });

            // Search functionality
            document.getElementById('mdi-search').addEventListener('input', (e) => {
                this.searchMDI(e.target.value);
            });

            // Custom icon button
            document.getElementById('use-custom-icon').addEventListener('click', () => {
                const text = document.getElementById('custom-icon-text').value.trim();
                if (text && this.currentIconCallback) {
                    this.currentIconCallback(text);
                    this.closeIconPicker();
                }
            });

            // Close icon picker
            document.getElementById('close-icon-picker').addEventListener('click', () => {
                this.closeIconPicker();
            });

            // Initial render - show suggested icons
            this.renderMDIGrid('suggested');
        }

        openIconPicker(callback) {
            this.currentIconCallback = callback;
            document.getElementById('icon-picker-modal').classList.add('active');
            // Reset to MDI tab
            document.querySelectorAll('.icon-picker-tab')[0].click();
        }

        closeIconPicker() {
            document.getElementById('icon-picker-modal').classList.remove('active');
            this.currentIconCallback = null;
            document.getElementById('custom-icon-text').value = '';
            document.getElementById('mdi-search').value = '';
        }

        renderMDIGrid(category = 'suggested', filter = '') {
            const grid = document.getElementById('mdi-grid');
            grid.innerHTML = '';

            let icons = [];

            // If searching, use full metadata
            if (filter && this.mdiMetadata) {
                const lowerFilter = filter.toLowerCase();
                const searchTerm = lowerFilter.replace('mdi:', '');

                // Search full metadata
                icons = this.mdiMetadata
                    .filter(icon => icon.name.includes(searchTerm))
                    .map(icon => ({ name: icon.name, label: icon.name }));
            } else if (category === 'suggested') {
                // Show suggested icons
                if (this.mdiMetadata) {
                    icons = SUGGESTED_ICONS
                        .map(name => {
                            const icon = this.mdiMetadata.find(i => i.name === name);
                            return icon ? { name: icon.name, label: icon.name } : null;
                        })
                        .filter(icon => icon !== null);
                } else {
                    // Fallback to basic list if CDN not loaded
                    icons = SUGGESTED_ICONS.map(name => ({ name, label: name }));
                }
            } else {
                // Dynamic category - filter by tags
                if (this.mdiMetadata) {
                    const dynamicCat = DYNAMIC_CATEGORIES.find(c => c.id === category);
                    if (dynamicCat) {
                        icons = this.mdiMetadata
                            .filter(icon => {
                                if (!icon.tags) return false;
                                return dynamicCat.tags.some(tag =>
                                    icon.tags.some(iconTag => iconTag.includes(tag))
                                );
                            })
                            .map(icon => ({ name: icon.name, label: icon.name }));
                    }
                }
            }

            // Render icons
            icons.forEach(icon => {
                const item = document.createElement('div');
                item.className = 'mdi-item';
                const iconName = `mdi:${icon.name}`;
                item.innerHTML = `
                    <div class="mdi-item-icon">${renderMDIIcon(icon.name)}</div>
                    <div class="mdi-item-name">${iconName}</div>
                `;
                item.addEventListener('click', () => {
                    if (this.currentIconCallback) {
                        // Return MDI format for backend processing
                        this.currentIconCallback(iconName);
                        this.closeIconPicker();
                    }
                });
                grid.appendChild(item);
            });

            // Show count
            let countText;
            if (filter) {
                countText = `Found ${icons.length} icon${icons.length !== 1 ? 's' : ''} matching "${filter}"`;
            } else if (category === 'suggested') {
                countText = `Showing ${icons.length} suggested icons`;
            } else {
                const dynamicCat = DYNAMIC_CATEGORIES.find(c => c.id === category);
                const catLabel = dynamicCat ? dynamicCat.label : 'Icons';
                countText = `${catLabel}: ${icons.length} icon${icons.length !== 1 ? 's' : ''}`;
            }

            // Add count display if not exists
            let countDisplay = document.getElementById('mdi-icon-count');
            if (!countDisplay) {
                countDisplay = document.createElement('div');
                countDisplay.id = 'mdi-icon-count';
                countDisplay.style.cssText = 'padding: 10px; text-align: center; color: #666; font-size: 13px;';
                grid.parentElement.insertBefore(countDisplay, grid);
            }
            countDisplay.textContent = countText;
        }

        searchMDI(query) {
            // Search uses full metadata (category doesn't matter when filtering)
            this.renderMDIGrid('suggested', query);
        }

        // ==================== State Rule Builder ====================

        setupStateRuleBuilder() {
            document.getElementById('add-state-rule').addEventListener('click', () => {
                this.addStateRule();
            });
        }

        loadStateRules(rules, entityId) {
            this.stateRules = rules || [];
            this.selectedEntity = entityId;
            this.renderStateRules();

            // Show suggested states if entity is selected
            if (entityId) {
                this.showSuggestedStates(entityId);
            }
        }

        renderStateRules() {
            const list = document.getElementById('state-rules-list');
            list.innerHTML = '';

            if (this.stateRules.length === 0) {
                list.innerHTML = '<p class="help-text">No state rules configured. Click "Add State Rule" to create one.</p>';
                return;
            }

            this.stateRules.forEach((rule, index) => {
                const item = this.createStateRuleElement(rule, index);
                list.appendChild(item);
            });
        }

        createStateRuleElement(rule, index) {
            const item = document.createElement('div');
            item.className = 'state-rule-item' + (rule.is_default ? ' is-default' : '');
            item.dataset.index = index;

            const conditionText = this.getConditionDisplayText(rule);

            // Render icon using CSS classes
            let displayIcon = '';
            if (rule.icon) {
                if (rule.icon.startsWith('mdi:')) {
                    displayIcon = renderMDIIcon(rule.icon);
                } else {
                    // Non-MDI icon (text/emoji)
                    displayIcon = rule.icon;
                }
            }

            // For preview, show loading indicator if template is enabled
            const previewText = rule.text_template && rule.text ? '<span class="template-loading">⏳</span>' : rule.text;

            // Build preview HTML based on display order
            const displayOrder = rule.display_order || 'icon_first';
            let previewHtml = '';

            if (displayOrder === 'text_first') {
                // Text first, then icon
                if (previewText) {
                    previewHtml += `<span class="preview-text" style="color: ${this.rgbToHex(rule.text_color)}">${previewText}</span> `;
                }
                if (displayIcon) {
                    previewHtml += `<span class="preview-icon" style="color: ${this.rgbToHex(rule.icon_color)}">${displayIcon}</span>`;
                }
            } else {
                // Icon first (default)
                if (displayIcon) {
                    previewHtml += `<span class="preview-icon" style="color: ${this.rgbToHex(rule.icon_color)}">${displayIcon}</span> `;
                }
                if (previewText) {
                    previewHtml += `<span class="preview-text" style="color: ${this.rgbToHex(rule.text_color)}">${previewText}</span>`;
                }
            }

            // Calculate smart background based on icon and text colors
            const previewBackground = this.getSmartPreviewBackground(rule.icon_color, rule.text_color);

            item.innerHTML = `
                <div class="state-rule-header">
                    <div class="state-rule-title">
                        ${rule.is_default ? '<span class="default-rule-badge">Default</span>' : conditionText}
                    </div>
                    <div class="state-rule-actions">
                        <button class="btn btn-secondary btn-sm" data-action="edit">Edit</button>
                        <button class="btn btn-danger btn-sm" data-action="remove">Remove</button>
                    </div>
                </div>
                <div class="state-rule-body">
                    <div class="state-rule-preview" style="${previewBackground}">
                        ${previewHtml}
                    </div>
                    <div class="state-rule-fields">
                        <div><strong>Condition:</strong> ${conditionText}</div>
                        <div><strong>Icon:</strong> ${rule.icon || 'None'}</div>
                        <div><strong>Text:</strong> ${rule.text || 'None'}${rule.text_template ? ' <span style="color: #2196f3;">(Template)</span>' : ''}</div>
                        ${rule.icon_background ? '<div><strong>Background:</strong> Enabled</div>' : ''}
                    </div>
                </div>
            `;

            // Event listeners
            item.querySelector('[data-action="edit"]').addEventListener('click', () => {
                this.editStateRule(index);
            });

            item.querySelector('[data-action="remove"]').addEventListener('click', () => {
                this.removeStateRule(index);
            });

            // Render template preview if needed
            if (rule.text_template && rule.text) {
                this.renderTemplatePreview(item, rule);
            }

            return item;
        }

        async renderTemplatePreview(item, rule) {
            const previewTextSpan = item.querySelector('.preview-text');
            if (!previewTextSpan) return;

            try {
                // Get auth token
                const hassTokensStr = localStorage.getItem('hassTokens');
                let token = null;

                if (hassTokensStr) {
                    try {
                        const hassTokens = JSON.parse(hassTokensStr);
                        token = hassTokens.access_token;
                    } catch (e) {
                        // Failed to parse tokens
                    }
                }

                const headers = {
                    'Content-Type': 'application/json'
                };

                if (token) {
                    headers['Authorization'] = `Bearer ${token}`;
                }

                const response = await fetch('/api/template', {
                    method: 'POST',
                    headers: headers,
                    body: JSON.stringify({ template: rule.text })
                });

                if (!response.ok) {
                    const errorText = await response.text();
                    throw new Error(errorText);
                }

                const result = await response.text();
                previewTextSpan.innerHTML = this.escapeHtml(result);
            } catch (error) {
                // Show error indicator with tooltip
                previewTextSpan.innerHTML = `<span class="template-error" title="${this.escapeHtml(error.message)}" style="color: #f44336; cursor: help;">&lt;error&gt;</span>`;
            }
        }

        getConditionDisplayText(rule) {
            if (rule.is_default) return 'Default (fallback)';

            const condition = rule.condition || 'equals';
            const value = rule.value || '';

            switch (condition) {
                case 'any_state': return 'Any State (always show)';
                case 'equals': return `State = "${value}"`;
                case 'not_equals': return `State ≠ "${value}"`;
                case 'in': return `State in [${value}]`;
                case 'not_in': return `State not in [${value}]`;
                case 'contains': return `State contains "${value}"`;
                case 'not_contains': return `State not contains "${value}"`;
                case 'gt': return `State > ${value}`;
                case 'gte': return `State >= ${value}`;
                case 'lt': return `State < ${value}`;
                case 'lte': return `State <= ${value}`;
                default: return `State = "${value}"`;
            }
        }

        rgbToHex(rgb) {
            if (!Array.isArray(rgb) || rgb.length < 3) return '#ffffff';
            return '#' + rgb.slice(0, 3).map(x => {
                const hex = x.toString(16);
                return hex.length === 1 ? '0' + hex : hex;
            }).join('');
        }

        /**
         * Calculate smart background for preview based on icon and text colors
         * Logic:
         * - If icon is white/very light → use dark background (#3a3a3a)
         * - If icon is black/very dark → use light background (#f5f5f5)
         * - Otherwise → use checkered pattern
         * - Icon color takes priority over text color when they differ
         */
        getSmartPreviewBackground(iconColor, textColor) {
            const isLight = (rgb) => {
                if (!Array.isArray(rgb) || rgb.length < 3) return false;
                // Calculate perceived brightness (0-255)
                const brightness = (rgb[0] * 299 + rgb[1] * 587 + rgb[2] * 114) / 1000;
                return brightness > 200; // Very light if > 200
            };

            const isDark = (rgb) => {
                if (!Array.isArray(rgb) || rgb.length < 3) return false;
                const brightness = (rgb[0] * 299 + rgb[1] * 587 + rgb[2] * 114) / 1000;
                return brightness < 55; // Very dark if < 55
            };

            // Icon color takes priority (if mixing white icon + black text, icon wins)
            if (isLight(iconColor)) {
                // White/light icon → dark background
                return 'background: #3a3a3a !important;';
            } else if (isDark(iconColor)) {
                // Black/dark icon → light background
                return 'background: #f5f5f5 !important;';
            } else if (isLight(textColor)) {
                // Icon is not extreme, check text color
                return 'background: #3a3a3a !important;';
            } else if (isDark(textColor)) {
                return 'background: #f5f5f5 !important;';
            }

            // Mixed colors or medium brightness → use checkered pattern (default CSS)
            return '';
        }

        hexToRgb(hex) {
            const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
            return result ? [
                parseInt(result[1], 16),
                parseInt(result[2], 16),
                parseInt(result[3], 16)
            ] : [255, 255, 255];
        }

        addStateRule(ruleData = null) {
            const rule = ruleData || {
                condition: 'equals',
                value: '',
                icon: 'mdi:lightbulb',
                text: '',
                icon_color: [255, 255, 255],
                text_color: [255, 255, 255],
                icon_background: false,
                is_default: false
            };

            this.stateRules.push(rule);
            this.renderStateRules();
            // Auto-edit the new rule
            this.editStateRule(this.stateRules.length - 1);
        }

        editStateRule(index) {
            const rule = this.stateRules[index];
            this.currentRuleIndex = index;

            // Create inline editor
            const ruleItem = document.querySelector(`[data-index="${index}"]`);
            const body = ruleItem.querySelector('.state-rule-body');

            body.innerHTML = `
                <div class="state-rule-fields" style="grid-column: 1 / -1;">
                    ${!rule.is_default ? `
                    <div class="rule-condition-group">
                        <select class="rule-condition-type" title="Select condition type">
                            <option value="any_state" ${rule.condition === 'any_state' ? 'selected' : ''}>Any State (always show)</option>
                            <option value="equals" ${rule.condition === 'equals' ? 'selected' : ''}>Equals</option>
                            <option value="not_equals" ${rule.condition === 'not_equals' ? 'selected' : ''}>Not Equals</option>
                            <option value="in" ${rule.condition === 'in' ? 'selected' : ''}>In List (comma-separated)</option>
                            <option value="not_in" ${rule.condition === 'not_in' ? 'selected' : ''}>Not In List (comma-separated)</option>
                            <option value="contains" ${rule.condition === 'contains' ? 'selected' : ''}>Contains</option>
                            <option value="not_contains" ${rule.condition === 'not_contains' ? 'selected' : ''}>Not Contains</option>
                            <option value="gt" ${rule.condition === 'gt' ? 'selected' : ''}>Greater Than (numeric)</option>
                            <option value="gte" ${rule.condition === 'gte' ? 'selected' : ''}>Greater or Equal (numeric)</option>
                            <option value="lt" ${rule.condition === 'lt' ? 'selected' : ''}>Less Than (numeric)</option>
                            <option value="lte" ${rule.condition === 'lte' ? 'selected' : ''}>Less or Equal (numeric)</option>
                        </select>
                        <input type="text" class="rule-value" placeholder="State value (use comma for lists)" value="${rule.value || ''}" title="For 'In List'/'Not In List': enter comma-separated values (e.g., on,off,unavailable)" ${rule.condition === 'any_state' ? 'style="display:none;"' : ''}>
                    </div>
                    ` : ''}

                    <div class="icon-input-group">
                        <label>Icon:</label>
                        <div class="icon-input-with-picker">
                            <input type="text" class="rule-icon" value="${rule.icon || ''}" placeholder="Select or enter icon">
                            <button type="button" class="btn-icon-picker">Choose Icon</button>
                        </div>
                    </div>

                    <div style="grid-column: 1 / -1;">
                        <label>Text:</label>
                        <div class="text-template-group">
                            <textarea class="rule-text" placeholder="Display text or template" rows="2" style="width: 100%; resize: vertical;">${rule.text || ''}</textarea>
                            <div class="template-options" style="display: flex; gap: 10px; margin-top: 5px; align-items: center;">
                                <label style="display: flex; align-items: center; gap: 5px; cursor: pointer; font-size: 0.9em;">
                                    <input type="checkbox" class="rule-text-template" ${rule.text_template ? 'checked' : ''}>
                                    <span>Use HA Template</span>
                                </label>
                                <button type="button" class="btn btn-secondary btn-sm btn-test-template" style="padding: 4px 12px;">🧪 Test Template</button>
                                <button type="button" class="btn btn-secondary btn-sm btn-use-entity-state" style="padding: 4px 12px;">📊 Use Entity State</button>
                            </div>
                            <div class="template-result" style="display: none; margin-top: 8px; padding: 8px; background: #f0f8ff; border-left: 3px solid #2196f3; font-size: 0.85em;"></div>
                            <small class="help-text">Examples: <code>{{ state_attr('sun.sun', 'elevation') }}°</code> or <code>{{ relative_time(states.sensor.uptime.last_changed) }} ago</code></small>
                        </div>
                    </div>

                    <div style="grid-column: 1 / -1;">
                        <label>Icon Color:</label>
                        <div class="color-picker-enhanced">
                            <div class="color-preview rule-icon-color-preview"></div>
                            <input type="color" class="rule-icon-color" value="${this.rgbToHex(rule.icon_color)}">
                            <div class="color-swatches">
                                <button type="button" class="color-swatch" data-color="#ffffff" title="White" style="background: #ffffff;"></button>
                                <button type="button" class="color-swatch" data-color="#000000" title="Black" style="background: #000000;"></button>
                                <button type="button" class="color-swatch" data-color="#ffd700" title="Gold" style="background: #ffd700;"></button>
                                <button type="button" class="color-swatch" data-color="#ff0000" title="Red" style="background: #ff0000;"></button>
                                <button type="button" class="color-swatch" data-color="#00ff00" title="Green" style="background: #00ff00;"></button>
                                <button type="button" class="color-swatch" data-color="#0000ff" title="Blue" style="background: #0000ff;"></button>
                                <button type="button" class="color-swatch" data-color="#ffff00" title="Yellow" style="background: #ffff00;"></button>
                                <button type="button" class="color-swatch" data-color="#ff9800" title="Orange" style="background: #ff9800;"></button>
                            </div>
                        </div>
                    </div>

                    <div style="grid-column: 1 / -1;">
                        <label>Text Color:</label>
                        <div class="color-picker-enhanced">
                            <div class="color-preview rule-text-color-preview"></div>
                            <input type="color" class="rule-text-color" value="${this.rgbToHex(rule.text_color)}">
                            <div class="color-swatches">
                                <button type="button" class="color-swatch" data-color="#ffffff" title="White" style="background: #ffffff;"></button>
                                <button type="button" class="color-swatch" data-color="#000000" title="Black" style="background: #000000;"></button>
                                <button type="button" class="color-swatch" data-color="#cccccc" title="Gray" style="background: #cccccc;"></button>
                                <button type="button" class="color-swatch" data-color="#ffd700" title="Gold" style="background: #ffd700;"></button>
                                <button type="button" class="color-swatch" data-color="#ff0000" title="Red" style="background: #ff0000;"></button>
                                <button type="button" class="color-swatch" data-color="#00ff00" title="Green" style="background: #00ff00;"></button>
                                <button type="button" class="color-swatch" data-color="#0000ff" title="Blue" style="background: #0000ff;"></button>
                                <button type="button" class="color-swatch" data-color="#ff9800" title="Orange" style="background: #ff9800;"></button>
                            </div>
                        </div>
                    </div>

                    <div>
                        <label>Display Order:</label>
                        <select class="rule-display-order">
                            <option value="icon_first" ${(rule.display_order || 'icon_first') === 'icon_first' ? 'selected' : ''}>Icon First</option>
                            <option value="text_first" ${rule.display_order === 'text_first' ? 'selected' : ''}>Text First</option>
                        </select>
                        <small class="help-text">Choose whether icon or text appears first</small>
                    </div>

                    <div>
                        <label style="display: flex; align-items: center; gap: 8px; cursor: pointer;">
                            <input type="checkbox" class="rule-icon-background" ${rule.icon_background ? 'checked' : ''} title="Fill icon background (e.g., solid bulb instead of outline)">
                            <span>Use Icon Background (Fill)</span>
                        </label>
                        <div style="font-size: 12px; color: #666; margin-top: 4px;">
                            Enable for filled/solid icons (e.g., solid yellow bulb vs outline)
                        </div>
                    </div>

                    <div style="display: flex; gap: 10px; margin-top: 10px; justify-content: flex-end;">
                        <button type="button" class="btn btn-secondary btn-sm" data-action="cancel-rule">Cancel</button>
                        <button type="button" class="btn btn-primary btn-sm" data-action="save-rule">Save</button>
                    </div>
                </div>
            `;

            // Condition type change handler - hide/show value input
            if (!rule.is_default) {
                const conditionSelect = body.querySelector('.rule-condition-type');
                const valueInput = body.querySelector('.rule-value');
                conditionSelect.addEventListener('change', () => {
                    if (conditionSelect.value === 'any_state') {
                        valueInput.style.display = 'none';
                        valueInput.value = '';  // Clear value when any_state is selected
                    } else {
                        valueInput.style.display = '';
                    }
                });
            }

            // Icon picker button
            body.querySelector('.btn-icon-picker').addEventListener('click', () => {
                this.openIconPicker((selectedIcon) => {
                    body.querySelector('.rule-icon').value = selectedIcon;
                });
            });

            // Test template button
            body.querySelector('.btn-test-template').addEventListener('click', () => {
                this.testTemplate(body);
            });

            // Use entity state button
            body.querySelector('.btn-use-entity-state').addEventListener('click', () => {
                this.useEntityState(body);
            });

            // Save button
            body.querySelector('[data-action="save-rule"]').addEventListener('click', () => {
                this.saveRuleEdit(index, body);
            });

            // Cancel button
            body.querySelector('[data-action="cancel-rule"]').addEventListener('click', () => {
                this.renderStateRules();
            });

            // Setup color pickers
            this.setupStateRuleColorPicker(body, '.rule-icon-color', '.rule-icon-color-preview');
            this.setupStateRuleColorPicker(body, '.rule-text-color', '.rule-text-color-preview');
        }

        setupStateRuleColorPicker(container, inputSelector, previewSelector) {
            const input = container.querySelector(inputSelector);
            const preview = container.querySelector(previewSelector);

            if (!input || !preview) return;

            // Update preview when input changes
            const updatePreview = () => {
                const color = input.value;
                preview.style.backgroundColor = color;

                // Update active swatch
                const colorPicker = input.closest('.color-picker-enhanced');
                if (colorPicker) {
                    const swatches = colorPicker.querySelectorAll('.color-swatch');
                    swatches.forEach(swatch => {
                        if (swatch.getAttribute('data-color').toLowerCase() === color.toLowerCase()) {
                            swatch.classList.add('active');
                        } else {
                            swatch.classList.remove('active');
                        }
                    });
                }
            };

            input.addEventListener('input', updatePreview);

            // Setup swatch click handlers
            const colorPicker = input.closest('.color-picker-enhanced');
            if (colorPicker) {
                const swatches = colorPicker.querySelectorAll('.color-swatch');
                swatches.forEach(swatch => {
                    swatch.addEventListener('click', () => {
                        const color = swatch.getAttribute('data-color');
                        input.value = color;
                        updatePreview();
                    });
                });
            }

            // Preview click opens color picker
            preview.addEventListener('click', () => {
                input.click();
            });

            // Initial preview update
            updatePreview();
        }

        async testTemplate(body) {
            const templateText = body.querySelector('.rule-text').value;
            const resultDiv = body.querySelector('.template-result');

            if (!templateText || !templateText.includes('{{')) {
                resultDiv.style.display = 'block';
                resultDiv.style.background = '#fff3cd';
                resultDiv.style.borderColor = '#ffc107';
                resultDiv.innerHTML = '⚠️ Please enter a template with {{ }}';
                setTimeout(() => resultDiv.style.display = 'none', 3000);
                return;
            }

            resultDiv.style.display = 'block';
            resultDiv.style.background = '#f0f8ff';
            resultDiv.style.borderColor = '#2196f3';
            resultDiv.innerHTML = '🔄 Testing template...';

            try {
                // Get auth token from localStorage hassTokens
                const hassTokensStr = localStorage.getItem('hassTokens');
                let token = null;

                if (hassTokensStr) {
                    try {
                        const hassTokens = JSON.parse(hassTokensStr);
                        token = hassTokens.access_token;
                    } catch (e) {
                        // Failed to parse tokens
                    }
                }

                const headers = {
                    'Content-Type': 'application/json'
                };

                if (token) {
                    headers['Authorization'] = `Bearer ${token}`;
                }

                const response = await fetch('/api/template', {
                    method: 'POST',
                    headers: headers,
                    body: JSON.stringify({ template: templateText })
                });

                if (!response.ok) {
                    const errorText = await response.text();
                    throw new Error(`HTTP ${response.status}: ${errorText}`);
                }

                const result = await response.text();
                resultDiv.style.background = '#e8f5e9';
                resultDiv.style.borderColor = '#4caf50';
                resultDiv.innerHTML = `✅ <strong>Result:</strong> ${this.escapeHtml(result)}`;
            } catch (error) {
                resultDiv.style.background = '#ffebee';
                resultDiv.style.borderColor = '#f44336';
                resultDiv.innerHTML = `❌ <strong>Error:</strong> ${this.escapeHtml(error.message)}`;
            }
        }

        escapeHtml(unsafe) {
            return unsafe
                .replace(/&/g, "&amp;")
                .replace(/</g, "&lt;")
                .replace(/>/g, "&gt;")
                .replace(/"/g, "&quot;")
                .replace(/'/g, "&#039;");
        }

        useEntityState(body) {
            // Get entity from modal's hidden input (for new state icons)
            // or from this.selectedEntity (for editing existing state icons)
            const entityId = document.getElementById('icon-entity')?.value || this.selectedEntity;

            if (!entityId) {
                const resultDiv = body.querySelector('.template-result');
                resultDiv.style.display = 'block';
                resultDiv.style.background = '#fff3cd';
                resultDiv.style.borderColor = '#ffc107';
                resultDiv.innerHTML = '⚠️ Please select an entity first';
                setTimeout(() => resultDiv.style.display = 'none', 3000);
                return;
            }

            const templateText = `{{ states('${entityId}') }}`;
            const textArea = body.querySelector('.rule-text');
            textArea.value = templateText;
            body.querySelector('.rule-text-template').checked = true;

            // Show confirmation
            const resultDiv = body.querySelector('.template-result');
            resultDiv.style.display = 'block';
            resultDiv.style.background = '#e8f5e9';
            resultDiv.style.borderColor = '#4caf50';
            resultDiv.innerHTML = `✅ Template set to: <code>${templateText}</code>`;
            setTimeout(() => resultDiv.style.display = 'none', 3000);
        }

        saveRuleEdit(index, body) {
            const rule = this.stateRules[index];

            if (!rule.is_default) {
                rule.condition = body.querySelector('.rule-condition-type').value;
                rule.value = body.querySelector('.rule-value').value;
            }

            const iconName = body.querySelector('.rule-icon').value;
            rule.icon = iconName;
            rule.text = body.querySelector('.rule-text').value;
            rule.text_template = body.querySelector('.rule-text-template').checked;
            rule.icon_color = this.hexToRgb(body.querySelector('.rule-icon-color').value);
            rule.text_color = this.hexToRgb(body.querySelector('.rule-text-color').value);
            rule.display_order = body.querySelector('.rule-display-order').value;
            rule.icon_background = body.querySelector('.rule-icon-background').checked;

            // Translate MDI icon to codepoint for backend (one-time translation!)
            if (iconName && iconName.startsWith('mdi:')) {
                const codepoint = this.translateMDIToCodepoint(iconName);
                rule.icon_codepoint = codepoint || null;
            } else {
                // Non-MDI icon (emoji/text) - no codepoint needed
                rule.icon_codepoint = null;
            }

            this.renderStateRules();
        }

        removeStateRule(index) {
            this.stateRules.splice(index, 1);
            this.renderStateRules();
        }

        getStateRules() {
            return this.stateRules;
        }

        showSuggestedStates(entityId) {
            const domain = entityId.split('.')[0];
            const suggestions = STATE_SUGGESTIONS[domain];

            if (!suggestions || suggestions.length === 0) {
                return;
            }

            // Check if suggested states section already exists
            let suggestedSection = document.querySelector('.suggested-states');
            if (!suggestedSection) {
                suggestedSection = document.createElement('div');
                suggestedSection.className = 'suggested-states';
                suggestedSection.innerHTML = `
                    <h5>Suggested States for ${domain}:</h5>
                    <div class="suggested-states-list"></div>
                `;
                document.querySelector('.config-section:nth-child(3)').appendChild(suggestedSection);
            }

            const list = suggestedSection.querySelector('.suggested-states-list');
            list.innerHTML = '';

            suggestions.forEach(state => {
                const btn = document.createElement('button');
                btn.className = 'suggested-state-btn';
                btn.textContent = state;
                btn.addEventListener('click', () => {
                    this.addStateRule({
                        condition: 'equals',
                        value: state,
                        icon: this.getDefaultIconForState(domain, state),
                        text: state.toUpperCase(),
                        icon_color: this.getDefaultIconColor(state),
                        text_color: [255, 255, 255],
                        icon_background: false,
                        is_default: false
                    });
                });
                list.appendChild(btn);
            });
        }

        getDefaultIconForState(domain, state) {
            // Default MDI icons for common states
            const defaults = {
                'light_on': 'mdi:lightbulb-on',
                'light_off': 'mdi:lightbulb-off',
                'switch_on': 'mdi:power-plug',
                'switch_off': 'mdi:power-off',
                'lock_locked': 'mdi:lock',
                'lock_unlocked': 'mdi:lock-open',
                'door_open': 'mdi:door-open',
                'door_closed': 'mdi:door-closed',
                'garage_open': 'mdi:garage-open',
                'garage_closed': 'mdi:garage',
            };

            const key = `${domain}_${state}`;
            return defaults[key] || 'mdi:alert-circle';
        }

        getDefaultIconColor(state) {
            if (state === 'on') return [255, 215, 0]; // Gold
            if (state === 'off') return [100, 100, 100]; // Gray
            if (state === 'unavailable') return [255, 0, 0]; // Red
            if (state.includes('open') || state.includes('unlock')) return [76, 175, 80]; // Green
            if (state.includes('closed') || state.includes('lock')) return [244, 67, 54]; // Red
            return [255, 255, 255]; // White default
        }
    };

    // Initialize the state icon manager when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => {
            window.stateIconManager = new window.StateIconManager();
        });
    } else {
        window.stateIconManager = new window.StateIconManager();
    }
})();
