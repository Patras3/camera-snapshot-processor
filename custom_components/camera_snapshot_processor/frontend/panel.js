// Camera Snapshot Processor - Professional Multi-Camera Configuration Panel
(function() {
    'use strict';

    // State
    let cameras = {};
    let currentCameraId = null;
    let currentConfig = {};
    let entities = [];
    let availableCameras = [];
    let sourceImageDimensions = { width: 0, height: 0 };
    let sourceImageSize = 0; // Store original image size in bytes
    let previewUpdateTimeout = null;
    let hassAccessToken = null;
    let editingStateIconIndex = null; // Track which icon is being edited
    let cropDragging = false;
    let cropResizing = false;
    let cropStartX = 0;
    let cropStartY = 0;
    let currentTab = 'crop';
    let sourceImageData = null; // Store the source image for cropping
    let cropPreviewDebounceTimer = null;

    // ==================== Custom Notification System ====================

    /**
     * Show a toast notification
     * @param {string} message - The message to display
     * @param {string} type - Type of notification: 'success', 'error', 'warning', 'info'
     * @param {number} duration - Duration in ms (0 = no auto-dismiss)
     */
    function showNotification(message, type = 'info', duration = 5000) {
        const container = document.getElementById('notification-container');

        // Create notification element
        const notification = document.createElement('div');
        notification.className = `notification-toast ${type}`;

        // Icon based on type
        const icons = {
            success: '✓',
            error: '✗',
            warning: '⚠',
            info: 'ℹ'
        };

        // Title based on type
        const titles = {
            success: 'Success',
            error: 'Error',
            warning: 'Warning',
            info: 'Info'
        };

        notification.innerHTML = `
            <div class="notification-icon">${icons[type] || icons.info}</div>
            <div class="notification-content">
                <div class="notification-title">${titles[type] || titles.info}</div>
                <div class="notification-message">${message}</div>
            </div>
            <button class="notification-close">×</button>
        `;

        // Add to container
        container.appendChild(notification);

        // Close button handler
        const closeBtn = notification.querySelector('.notification-close');
        closeBtn.addEventListener('click', () => {
            dismissNotification(notification);
        });

        // Auto-dismiss if duration is set
        if (duration > 0) {
            setTimeout(() => {
                dismissNotification(notification);
            }, duration);
        }

        return notification;
    }

    /**
     * Dismiss a notification with animation
     * @param {HTMLElement} notification - The notification element to dismiss
     */
    function dismissNotification(notification) {
        if (notification && !notification.classList.contains('closing')) {
            notification.classList.add('closing');
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.parentNode.removeChild(notification);
                }
            }, 300);
        }
    }

    /**
     * Show a confirmation dialog
     * @param {string} message - The confirmation message
     * @param {string} title - The dialog title
     * @param {function} onConfirm - Callback when confirmed
     * @param {function} onCancel - Callback when cancelled
     */
    function showConfirmation(message, title = 'Confirm Action', onConfirm, onCancel) {
        const modal = document.getElementById('confirmation-modal');
        const titleElement = document.getElementById('confirmation-title');
        const messageElement = document.getElementById('confirmation-message');
        const confirmBtn = document.getElementById('confirmation-confirm');
        const cancelBtn = document.getElementById('confirmation-cancel');

        // Set content
        titleElement.textContent = title;
        messageElement.textContent = message;

        // Show modal
        modal.classList.add('active');

        // Remove any existing event listeners by replacing elements
        const newConfirmBtn = confirmBtn.cloneNode(true);
        const newCancelBtn = cancelBtn.cloneNode(true);
        confirmBtn.parentNode.replaceChild(newConfirmBtn, confirmBtn);
        cancelBtn.parentNode.replaceChild(newCancelBtn, cancelBtn);

        // Add new event listeners
        newConfirmBtn.addEventListener('click', () => {
            modal.classList.remove('active');
            if (onConfirm) onConfirm();
        });

        newCancelBtn.addEventListener('click', () => {
            modal.classList.remove('active');
            if (onCancel) onCancel();
        });

        // Close on backdrop click
        const backdropClickHandler = (e) => {
            if (e.target === modal) {
                modal.classList.remove('active');
                if (onCancel) onCancel();
                modal.removeEventListener('click', backdropClickHandler);
            }
        };
        modal.addEventListener('click', backdropClickHandler);

        // Close on Escape key
        const escapeHandler = (e) => {
            if (e.key === 'Escape') {
                modal.classList.remove('active');
                if (onCancel) onCancel();
                document.removeEventListener('keydown', escapeHandler);
            }
        };
        document.addEventListener('keydown', escapeHandler);
    }

    /**
     * Show success notification
     * @param {string} message - Success message
     */
    function showSuccess(message) {
        showNotification(message, 'success', 5000);
    }

    /**
     * Show error notification
     * @param {string} message - Error message
     */
    function showError(message) {
        showNotification(message, 'error', 7000);
    }

    /**
     * Show warning notification
     * @param {string} message - Warning message
     */
    function showWarning(message) {
        showNotification(message, 'warning', 6000);
    }

    /**
     * Show info notification
     * @param {string} message - Info message
     */
    function showInfo(message) {
        showNotification(message, 'info', 5000);
    }

    // Initialize
    document.addEventListener('DOMContentLoaded', init);

    // Get Home Assistant access token
    function getAccessToken(forceRefresh = false) {
        if (hassAccessToken && !forceRefresh) {
            return hassAccessToken;
        }

        // Try to get token from parent window (Home Assistant)
        try {
            if (window.parent && window.parent.document) {
                const authToken = window.parent.localStorage.getItem('hassTokens');
                if (authToken) {
                    const tokens = JSON.parse(authToken);
                    hassAccessToken = tokens.access_token;
                    return hassAccessToken;
                }
            }
        } catch (e) {
            // Parent window access restricted - expected in some configurations
        }

        // Fallback: check URL parameters
        const urlParams = new URLSearchParams(window.location.search);
        const token = urlParams.get('access_token');
        if (token) {
            hassAccessToken = token;
            return hassAccessToken;
        }

        // Last resort: check own localStorage
        try {
            const authToken = localStorage.getItem('hassTokens');
            if (authToken) {
                const tokens = JSON.parse(authToken);
                hassAccessToken = tokens.access_token;
                return hassAccessToken;
            }
        } catch (e) {
            // localStorage access restricted
        }

        return null;
    }

    // Create fetch options with authentication
    function getFetchOptions(options = {}) {
        const token = getAccessToken();
        const headers = options.headers || {};

        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
        }

        return {
            ...options,
            headers: headers,
            credentials: 'include'
        };
    }

    /**
     * Enhanced fetch wrapper with automatic token refresh on 401 errors
     * @param {string} url - The URL to fetch
     * @param {object} options - Fetch options
     * @param {number} retryCount - Internal retry counter
     * @returns {Promise<Response>} - The fetch response
     */
    async function authenticatedFetch(url, options = {}, retryCount = 0) {
        const MAX_RETRIES = 1;

        try {
            const response = await fetch(url, getFetchOptions(options));

            // Check if response is 401 Unauthorized
            if (response.status === 401 && retryCount < MAX_RETRIES) {
                // Force refresh the token from parent window
                const newToken = getAccessToken(true);

                if (newToken && newToken !== hassAccessToken) {
                    // Token was refreshed successfully, retry the request
                    return authenticatedFetch(url, options, retryCount + 1);
                } else {
                    // Token refresh failed or returned same token
                    showError('Session expired. Please refresh the page to continue.');
                    throw new Error('Authentication token expired. Please refresh the page.');
                }
            }

            return response;
        } catch (error) {
            // Network errors or other issues - retry once with fresh token
            if (retryCount === 0 && error.message.includes('Failed to fetch')) {
                getAccessToken(true); // Refresh token
                return authenticatedFetch(url, options, retryCount + 1);
            }
            throw error;
        }
    }

    async function init() {
        // Set up event listeners
        setupEventListeners();

        // Load data
        await loadCameras();
        await loadEntities();

        // Show appropriate view
        updateUI();
    }

    function setupEventListeners() {
        // Add camera buttons
        document.getElementById('add-camera-btn').addEventListener('click', openAddCameraModal);
        document.getElementById('add-camera-btn-empty').addEventListener('click', openAddCameraModal);
        document.getElementById('confirm-add-camera').addEventListener('click', confirmAddCamera);
        document.getElementById('cancel-add-camera').addEventListener('click', closeAddCameraModal);
        document.getElementById('cancel-state-icon').addEventListener('click', closeStateIconModal);

        // Entity name editor
        document.getElementById('entity-name-btn').addEventListener('click', openEntityNameModal);
        document.getElementById('cancel-entity-name').addEventListener('click', closeEntityNameModal);
        document.getElementById('save-entity-name').addEventListener('click', saveEntityName);

        // Entity name input validation
        const entityNameInput = document.getElementById('entity-name-input');
        entityNameInput.addEventListener('input', (e) => {
            // Convert to lowercase and filter invalid characters
            let value = e.target.value.toLowerCase();
            value = value.replace(/[^a-z0-9_]/g, '');
            e.target.value = value;

            // Clear error message when user types
            const errorEl = document.getElementById('entity-name-error');
            errorEl.style.display = 'none';
        });

        // Close modals with X button
        document.querySelectorAll('.close-modal').forEach(btn => {
            btn.addEventListener('click', () => {
                closeAddCameraModal();
                closeStateIconModal();
                closeEntityNameModal();
            });
        });

        // Modal background clicks
        document.getElementById('add-camera-modal').addEventListener('click', (e) => {
            if (e.target.id === 'add-camera-modal') closeAddCameraModal();
        });
        document.getElementById('state-icon-modal').addEventListener('click', (e) => {
            if (e.target.id === 'state-icon-modal') closeStateIconModal();
        });
        document.getElementById('entity-name-modal').addEventListener('click', (e) => {
            if (e.target.id === 'entity-name-modal') closeEntityNameModal();
        });

        // Tab switching
        document.querySelectorAll('.tab').forEach(tab => {
            tab.addEventListener('click', async () => {
                currentTab = tab.dataset.tab;
                switchTab(currentTab);
                await updateCropVisibility();

                // Refresh preview when switching away from crop tab
                // This ensures overlays/state icons show on the cropped result
                if (currentTab !== 'crop') {
                    schedulePreviewUpdate();
                }
            });
        });

        // Form inputs - auto-update preview on change
        document.querySelectorAll('input, select').forEach(input => {
            if (input.id && !input.id.includes('icon-') && !input.id.includes('new-camera')) {
                if (input.type === 'range') {
                    input.addEventListener('input', (e) => {
                        updateValueDisplay(e.target);
                        schedulePreviewUpdate();
                    });
                } else if (input.type === 'checkbox') {
                    input.addEventListener('change', schedulePreviewUpdate);
                } else {
                    input.addEventListener('input', schedulePreviewUpdate);
                }
            }
        });

        // Crop toggle
        document.getElementById('crop_enabled').addEventListener('change', async (e) => {
            const isEnabled = e.target.checked;
            document.getElementById('crop-controls').style.display = isEnabled ? 'block' : 'none';

            // Enable or disable interactive cropping based on whether image is already cropped
            updateCropInteractionState();
            await updateCropVisibility();
            updateEffectiveSourceSize();
        });

        // Reset crop button
        document.getElementById('reset-crop-btn').addEventListener('click', resetCrop);

        // Sync dimension sliders with number inputs
        // Slider -> Input: Direct sync (slider always in valid range)
        document.getElementById('width-slider').addEventListener('input', (e) => {
            document.getElementById('width').value = e.target.value;
            schedulePreviewUpdate();
        });

        // Input -> Slider: Clamp slider to its range when input goes outside
        document.getElementById('width').addEventListener('input', (e) => {
            const slider = document.getElementById('width-slider');
            const value = parseInt(e.target.value) || 0;

            // Clamp slider to its range (input can be anything)
            if (value < parseInt(slider.min)) {
                slider.value = slider.min;
            } else if (value > parseInt(slider.max)) {
                slider.value = slider.max;
            } else {
                slider.value = value;
            }

            if (sourceImageDimensions.width && !document.getElementById('crop_enabled').checked) {
                updateCropDimensionsFromSource();
            }
            updateDimensionsDisplay();
            updateFontSizeSuggestions();
        });

        document.getElementById('height-slider').addEventListener('input', (e) => {
            document.getElementById('height').value = e.target.value;
            schedulePreviewUpdate();
        });

        document.getElementById('height').addEventListener('input', (e) => {
            const slider = document.getElementById('height-slider');
            const value = parseInt(e.target.value) || 0;

            // Clamp slider to its range (input can be anything)
            if (value < parseInt(slider.min)) {
                slider.value = slider.min;
            } else if (value > parseInt(slider.max)) {
                slider.value = slider.max;
            } else {
                slider.value = value;
            }

            if (sourceImageDimensions.height && !document.getElementById('crop_enabled').checked) {
                updateCropDimensionsFromSource();
            }
            updateDimensionsDisplay();
            updateFontSizeSuggestions();
        });

        // Keep ratio checkbox - hide width control when checked
        document.getElementById('keep_ratio').addEventListener('change', (e) => {
            const widthControl = document.getElementById('width-control');
            widthControl.style.display = e.target.checked ? 'none' : 'block';
            updateDimensionsDisplay();
        });

        // Action buttons
        document.getElementById('reload-data-btn').addEventListener('click', reloadData);
        document.getElementById('save-config-btn').addEventListener('click', saveConfig);
        document.getElementById('refresh-preview-btn').addEventListener('click', refreshPreview);
        document.getElementById('delete-camera-btn').addEventListener('click', deleteCamera);

        // State icons
        document.getElementById('add-state-icon').addEventListener('click', openStateIconModal);
        document.getElementById('save-state-icon').addEventListener('click', saveStateIcon);

        // Initialize range value displays and ensure all sliders work
        document.querySelectorAll('input[type="range"]').forEach(input => {
            updateValueDisplay(input);

            // Modal sliders (icon-*) need their own listener since they're excluded above
            if (input.id && input.id.includes('icon-')) {
                input.addEventListener('input', (e) => {
                    updateValueDisplay(e.target);
                });
            }
        });

        // Opacity sliders - update value display
        const overlayBackgroundOpacitySlider = document.getElementById('overlay_background_opacity');
        const overlayBackgroundOpacityValue = document.getElementById('overlay_background_opacity-value');
        if (overlayBackgroundOpacitySlider && overlayBackgroundOpacityValue) {
            overlayBackgroundOpacitySlider.addEventListener('input', (e) => {
                overlayBackgroundOpacityValue.textContent = e.target.value;
            });
        }

        const stateIconBackgroundOpacitySlider = document.getElementById('state_icon_background_opacity');
        const stateIconBackgroundOpacityValue = document.getElementById('state_icon_background_opacity-value');
        if (stateIconBackgroundOpacitySlider && stateIconBackgroundOpacityValue) {
            stateIconBackgroundOpacitySlider.addEventListener('input', (e) => {
                stateIconBackgroundOpacityValue.textContent = e.target.value;
            });
        }

        // Setup interactive crop
        setupCropInteraction();

        // Setup Pickr color pickers
        setupColorPickers();

        // Setup strftime help
        setupStrftimeHelp();
    }

    // ==================== Pickr Color Pickers ====================

    let overlayColorPickr = null;
    let overlayBackgroundPickr = null;
    let textShadowColorPickr = null;
    let stateIconBackgroundPickr = null;
    let stateIconShadowColorPickr = null;

    function setupColorPickers() {
        // Text Color Picker (RGB only)
        overlayColorPickr = Pickr.create({
            el: '#overlay_color_picker',
            theme: 'nano',
            default: '#ffffff',
            swatches: [
                '#ffffff', '#000000', '#ff0000', '#00ff00',
                '#0000ff', '#ffff00', '#ffd700', '#ff9800'
            ],
            components: {
                preview: true,
                opacity: false,
                hue: true,
                interaction: {
                    input: true
                }
            }
        });

        overlayColorPickr.on('change', (color) => {
            if (color) {
                document.getElementById('overlay_color').value = color.toHEXA().toString();
                schedulePreviewUpdate();
            }
        });

        // Update button preview when picker is hidden
        overlayColorPickr.on('hide', () => {
            overlayColorPickr.applyColor(true);
        });

        // Background Color Picker (no opacity control - use Clear button for transparency)
        overlayBackgroundPickr = Pickr.create({
            el: '#overlay_background_picker',
            theme: 'nano',
            default: '#000000',
            swatches: [
                '#000000', '#ffffff', '#333333', '#666666',
                '#667eea', '#4caf50', '#ffeb3b', '#ff9800', '#f44336'
            ],
            components: {
                preview: true,
                opacity: false,
                hue: true,
                interaction: {
                    input: true
                }
            }
        });

        overlayBackgroundPickr.on('change', (color) => {
            if (color) {
                document.getElementById('overlay_background').value = color.toHEXA().toString();
                schedulePreviewUpdate();
            }
        });

        // Update button preview when picker is hidden
        overlayBackgroundPickr.on('hide', () => {
            overlayBackgroundPickr.applyColor(true);
        });

        // State Icon Background Color Picker (no opacity control - use Clear button for transparency)
        stateIconBackgroundPickr = Pickr.create({
            el: '#state_icon_background_picker',
            theme: 'nano',
            default: '#000000',
            swatches: [
                '#000000', '#ffffff', '#333333', '#666666',
                '#667eea', '#4caf50', '#ffeb3b', '#ff9800', '#f44336'
            ],
            components: {
                preview: true,
                opacity: false,
                hue: true,
                interaction: {
                    input: true
                }
            }
        });

        stateIconBackgroundPickr.on('change', (color) => {
            if (color) {
                document.getElementById('state_icon_background').value = color.toHEXA().toString();
                schedulePreviewUpdate();
            }
        });

        // Update button preview when picker is hidden
        stateIconBackgroundPickr.on('hide', () => {
            stateIconBackgroundPickr.applyColor(true);
        });

        // Text Shadow Color Picker
        textShadowColorPickr = Pickr.create({
            el: '#text_shadow_color_picker',
            theme: 'nano',
            default: '#000000',
            swatches: [
                '#000000', '#ffffff', '#333333', '#666666',
                '#667eea', '#4caf50', '#ffeb3b', '#ff9800', '#f44336'
            ],
            components: {
                preview: true,
                opacity: false,
                hue: true,
                interaction: {
                    input: true
                }
            }
        });

        textShadowColorPickr.on('change', (color) => {
            if (color) {
                document.getElementById('text_shadow_color').value = color.toHEXA().toString();
                schedulePreviewUpdate();
            }
        });

        textShadowColorPickr.on('hide', () => {
            textShadowColorPickr.applyColor(true);
        });

        // State Icon Shadow Color Picker
        stateIconShadowColorPickr = Pickr.create({
            el: '#state_icon_shadow_color_picker',
            theme: 'nano',
            default: '#000000',
            swatches: [
                '#000000', '#ffffff', '#333333', '#666666',
                '#667eea', '#4caf50', '#ffeb3b', '#ff9800', '#f44336'
            ],
            components: {
                preview: true,
                opacity: false,
                hue: true,
                interaction: {
                    input: true
                }
            }
        });

        stateIconShadowColorPickr.on('change', (color) => {
            if (color) {
                document.getElementById('state_icon_shadow_color').value = color.toHEXA().toString();
                schedulePreviewUpdate();
            }
        });

        stateIconShadowColorPickr.on('hide', () => {
            stateIconShadowColorPickr.applyColor(true);
        });

        // Clear background buttons
        document.getElementById('clear_overlay_background').addEventListener('click', () => {
            document.getElementById('overlay_background').value = '#00000000';
            if (overlayBackgroundPickr) {
                overlayBackgroundPickr.setColor('#00000000');
            }
            schedulePreviewUpdate();
        });

        document.getElementById('clear_state_icon_background').addEventListener('click', () => {
            document.getElementById('state_icon_background').value = '#00000000';
            if (stateIconBackgroundPickr) {
                stateIconBackgroundPickr.setColor('#00000000');
            }
            schedulePreviewUpdate();
        });
    }

    // ==================== Strftime Help ====================

    function setupStrftimeHelp() {
        const infoIcon = document.getElementById('strftime-info-icon');
        const helpBox = document.getElementById('strftime-examples');
        const datetimeFormatInput = document.getElementById('datetime_format');

        // Check if elements exist
        if (!infoIcon || !helpBox || !datetimeFormatInput) {
            console.error('Strftime help elements not found:', { infoIcon, helpBox, datetimeFormatInput });
            return;
        }

        // Toggle help box when info icon is clicked
        infoIcon.addEventListener('click', (e) => {
            e.stopPropagation();
            if (helpBox.style.display === 'none' || helpBox.style.display === '') {
                helpBox.style.display = 'block';
            } else {
                helpBox.style.display = 'none';
            }
        });

        // Close help box when clicking outside
        document.addEventListener('click', (e) => {
            if (!helpBox.contains(e.target) && e.target !== infoIcon) {
                helpBox.style.display = 'none';
            }
        });

        // Handle copy functionality for format examples
        helpBox.querySelectorAll('.copyable').forEach(codeElement => {
            codeElement.addEventListener('click', (e) => {
                e.stopPropagation();
                const format = codeElement.getAttribute('data-format');
                datetimeFormatInput.value = format;
                datetimeFormatInput.dispatchEvent(new Event('input', { bubbles: true }));

                // Visual feedback
                const originalText = codeElement.textContent;
                codeElement.textContent = '✓ Copied!';
                setTimeout(() => {
                    codeElement.textContent = originalText;
                }, 1000);

                // Update preview
                schedulePreviewUpdate();
            });
        });
    }

    // ==================== Camera Management ====================

    async function loadCameras() {
        try {
            const response = await authenticatedFetch('/api/camera_snapshot_processor/cameras');
            const data = await response.json();

            if (!data.success) {
                throw new Error(data.error || 'Failed to load cameras');
            }

            cameras = data.cameras || {};
            renderCameraList();

            // Select first camera if available
            const cameraIds = Object.keys(cameras);
            if (cameraIds.length > 0 && !currentCameraId) {
                selectCamera(cameraIds[0]);
            }
        } catch (error) {
            console.error('Failed to load cameras:', error);
            showError('Failed to load cameras: ' + error.message);
        }
    }

    async function reloadData() {
        const loadingOverlay = document.getElementById('loading-overlay');

        try {
            // Show loading overlay
            loadingOverlay.style.display = 'flex';

            // Remember current camera ID to re-select it
            const currentId = currentCameraId;

            // Reload cameras from HA
            await loadCameras();

            // Re-select the same camera if it still exists
            if (currentId && cameras[currentId]) {
                await selectCamera(currentId);
            } else if (Object.keys(cameras).length > 0) {
                // If current camera was deleted, select first available
                await selectCamera(Object.keys(cameras)[0]);
            }

            showSuccess('Data reloaded from Home Assistant');
        } catch (error) {
            console.error('Failed to reload data:', error);
            showError('Failed to reload data: ' + error.message);
        } finally {
            // Hide loading overlay
            loadingOverlay.style.display = 'none';
        }
    }

    function renderCameraList() {
        const list = document.getElementById('camera-list');
        list.innerHTML = '';

        const cameraIds = Object.keys(cameras);
        if (cameraIds.length === 0) {
            list.innerHTML = '<p class="empty-message">No cameras added yet</p>';
            return;
        }

        cameraIds.forEach(cameraId => {
            const config = cameras[cameraId];
            const sourceName = config.source_camera.replace('camera.', '').replace(/_/g, ' ');

            const item = document.createElement('div');
            item.className = 'camera-list-item';
            if (cameraId === currentCameraId) {
                item.classList.add('active');
            }

            item.innerHTML = `
                <div class="camera-icon">📷</div>
                <div class="camera-info">
                    <div class="camera-name">${sourceName}</div>
                    <div class="camera-details">${config.width}×${config.height}</div>
                </div>
            `;

            item.addEventListener('click', () => selectCamera(cameraId));
            list.appendChild(item);
        });
    }

    async function selectCamera(cameraId) {
        if (!cameras[cameraId]) {
            console.error('Camera not found:', cameraId);
            return;
        }

        currentCameraId = cameraId;
        currentConfig = cameras[cameraId];

        // Update UI
        renderCameraList();
        populateForm(currentConfig);

        // Load source image first to get dimensions
        await loadSourceImage();

        // Then update dimensions display with proper calculations
        updateDimensionsDisplay();

        // Load preview
        await refreshPreview();

        updateUI();
    }

    async function openAddCameraModal() {
        // Load available cameras
        try {
            const response = await authenticatedFetch('/api/camera_snapshot_processor/available_cameras');
            const data = await response.json();

            if (!data.success) {
                throw new Error(data.error || 'Failed to load cameras');
            }

            availableCameras = data.cameras || [];

            // Note: We allow selecting the same camera multiple times
            // to support multiple processed versions of the same source

            // Populate select
            const select = document.getElementById('new-camera-select');
            select.innerHTML = '';

            if (availableCameras.length === 0) {
                select.innerHTML = '<option value="">No available cameras</option>';
            } else {
                availableCameras.forEach(camera => {
                    const option = document.createElement('option');
                    option.value = camera.entity_id;
                    option.textContent = camera.name;
                    select.appendChild(option);
                });
            }

            document.getElementById('add-camera-modal').classList.add('active');
        } catch (error) {
            console.error('Failed to load available cameras:', error);
            showError('Failed to load available cameras: ' + error.message);
        }
    }

    function closeAddCameraModal() {
        document.getElementById('add-camera-modal').classList.remove('active');
    }

    async function confirmAddCamera() {
        const select = document.getElementById('new-camera-select');
        const sourceCamera = select.value;

        if (!sourceCamera) {
            showError('Please select a camera');
            return;
        }

        const confirmBtn = document.getElementById('confirm-add-camera');
        const originalBtnText = confirmBtn.textContent;

        try {
            // Disable button and show loading state
            confirmBtn.disabled = true;
            confirmBtn.textContent = '⏳ Adding...';

            const response = await authenticatedFetch('/api/camera_snapshot_processor/cameras', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ source_camera: sourceCamera })
            });

            const data = await response.json();

            if (!data.success) {
                throw new Error(data.error || 'Failed to add camera');
            }

            closeAddCameraModal();

            // Show loading notification
            const loadingNotification = showNotification(
                'Loading camera configuration...',
                'info',
                0  // Don't auto-dismiss
            );

            // Reload cameras and select the new one
            await loadCameras();
            await selectCamera(data.camera_id);

            // Dismiss loading notification
            dismissNotification(loadingNotification);

            // Show success
            showSuccess('Camera added and loaded successfully!');
        } catch (error) {
            console.error('Failed to add camera:', error);
            showError('Failed to add camera: ' + error.message);
        } finally {
            // Reset button state
            confirmBtn.disabled = false;
            confirmBtn.textContent = originalBtnText;
        }
    }

    async function deleteCamera() {
        if (!currentCameraId) return;

        showConfirmation(
            'Are you sure you want to delete this camera? This action cannot be undone.',
            'Delete Camera',
            async () => {
                try {
                    const response = await authenticatedFetch(`/api/camera_snapshot_processor/cameras/${currentCameraId}`, {
                        method: 'DELETE'
                    });

                    const data = await response.json();

                    if (!data.success) {
                        throw new Error(data.error || 'Failed to delete camera');
                    }

                    showSuccess('Camera deleted successfully!');

                    // Remove from local state
                    delete cameras[currentCameraId];
                    currentCameraId = null;
                    currentConfig = {};

                    // Reload and select another camera if available
                    await loadCameras();
                    updateUI();
                } catch (error) {
                    console.error('Failed to delete camera:', error);
                    showError('Failed to delete camera: ' + error.message);
                }
            }
        );
    }

    function updateUI() {
        const hasCamera = currentCameraId && cameras[currentCameraId];

        document.getElementById('empty-state').style.display = hasCamera ? 'none' : 'flex';
        document.getElementById('config-view').style.display = hasCamera ? 'block' : 'none';

        if (hasCamera) {
            const config = cameras[currentCameraId];
            const sourceName = config.source_camera.replace('camera.', '').replace(/_/g, ' ');
            document.getElementById('camera-title').textContent = sourceName;
            document.getElementById('camera-source').textContent = `Source: ${config.source_camera}`;

            // Update entity name button - use actual entity ID from HA if available
            let displayEntityId;
            if (config.actual_entity_id) {
                // Use the actual entity ID from Home Assistant registry
                displayEntityId = config.actual_entity_id;
            } else {
                // Fallback: construct from entity_name config
                const entityName = config.entity_name || `${config.source_camera.replace('camera.', '')}_processed`;
                displayEntityId = `camera.${entityName}`;
            }

            const entityNameBtn = document.getElementById('entity-name-btn');
            const entityNameSection = document.getElementById('entity-name-section');
            entityNameBtn.textContent = displayEntityId;
            entityNameSection.style.display = 'block';
        } else {
            document.getElementById('entity-name-section').style.display = 'none';
        }
    }

    // ==================== Entity Name Editor ====================

    function openEntityNameModal() {
        if (!currentCameraId || !cameras[currentCameraId]) {
            return;
        }

        const config = cameras[currentCameraId];

        // Use actual entity name from HA registry if available
        let currentEntityName;
        if (config.actual_entity_name) {
            currentEntityName = config.actual_entity_name;
        } else {
            // Fallback to config
            currentEntityName = config.entity_name || `${config.source_camera.replace('camera.', '')}_processed`;
        }

        const input = document.getElementById('entity-name-input');
        input.value = currentEntityName;

        // Clear any previous errors
        const errorEl = document.getElementById('entity-name-error');
        errorEl.style.display = 'none';

        document.getElementById('entity-name-modal').classList.add('active');

        // Focus input after a short delay to ensure modal is visible
        setTimeout(() => input.focus(), 100);
    }

    function closeEntityNameModal() {
        document.getElementById('entity-name-modal').classList.remove('active');
    }

    async function saveEntityName() {
        if (!currentCameraId) return;

        const input = document.getElementById('entity-name-input');
        const newName = input.value.trim();
        const errorEl = document.getElementById('entity-name-error');

        // Validation
        if (!newName) {
            errorEl.textContent = 'Entity name cannot be empty';
            errorEl.style.display = 'block';
            return;
        }

        if (!/^[a-z0-9_]+$/.test(newName)) {
            errorEl.textContent = 'Only lowercase letters, numbers, and underscores are allowed';
            errorEl.style.display = 'block';
            return;
        }

        const saveBtn = document.getElementById('save-entity-name');
        const originalBtnText = saveBtn.textContent;

        try {
            // Disable button and show loading state
            saveBtn.disabled = true;
            saveBtn.textContent = '💾 Saving...';

            // Update config
            currentConfig.entity_name = newName;

            // Save to backend
            const response = await authenticatedFetch(`/api/camera_snapshot_processor/cameras/${currentCameraId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ config: currentConfig })
            });

            const data = await response.json();

            if (!data.success) {
                // Show the error in the modal
                errorEl.textContent = data.error || 'Failed to save entity name';
                errorEl.style.display = 'block';
                return;
            }

            // Update local state
            cameras[currentCameraId] = currentConfig;

            closeEntityNameModal();

            // Force reload to get actual entity ID from HA
            await reloadData();

            showSuccess(`Entity ID updated to camera.${newName}`);
        } catch (error) {
            console.error('Failed to save entity name:', error);
            errorEl.textContent = `Error: ${error.message}`;
            errorEl.style.display = 'block';
        } finally {
            // Reset button state
            saveBtn.disabled = false;
            saveBtn.textContent = originalBtnText;
        }
    }

    // ==================== Configuration Management ====================

    function populateForm(config) {
        // Dimensions
        setInputValue('width', config.width || 1920);
        setInputValue('height', config.height || 1080);
        setInputValue('keep_ratio', config.keep_ratio !== false);
        setInputValue('quality', config.quality || 85);

        // Sync sliders
        document.getElementById('width-slider').value = config.width || 1920;
        document.getElementById('height-slider').value = config.height || 1080;

        // Update width control visibility based on keep_ratio
        const widthControl = document.getElementById('width-control');
        widthControl.style.display = (config.keep_ratio !== false) ? 'none' : 'block';

        // Crop
        setInputValue('crop_enabled', config.crop_enabled || false);
        setInputValue('crop_x', config.crop_x || 0);
        setInputValue('crop_y', config.crop_y || 0);
        setInputValue('crop_width', config.crop_width || config.source_width || 1920);
        setInputValue('crop_height', config.crop_height || config.source_height || 1080);

        // Show/hide crop controls
        document.getElementById('crop-controls').style.display = config.crop_enabled ? 'block' : 'none';
        document.getElementById('crop-overlay').style.display = config.crop_enabled ? 'block' : 'none';

        // Calculate suggested font sizes based on output dimensions
        const actualDimensions = calculateActualDimensions(config);
        const suggestedSizes = calculateSuggestedFontSizes(actualDimensions.width, actualDimensions.height);

        // DateTime overlay
        setInputValue('datetime_enabled', config.datetime_enabled || false);
        setInputValue('datetime_format', config.datetime_format || '%Y-%m-%d %H:%M:%S');
        setInputValue('datetime_locale', config.datetime_locale || 'system');
        setInputValue('datetime_position', config.datetime_position || 'top_left');
        // Use suggested size if config doesn't have a custom value (default is 24)
        const datetimeFontSize = (config.datetime_font_size && config.datetime_font_size !== 24) ?
            config.datetime_font_size : suggestedSizes.datetime;
        setInputValue('datetime_font_size', datetimeFontSize);
        updateFontSizeSuggestion('datetime_font_size', suggestedSizes.datetime);

        // Text overlay
        setInputValue('text_enabled', config.text_enabled || false);
        setInputValue('text_value', config.text_value || '');
        setInputValue('text_position', config.text_position || 'top_right');
        // Use suggested size if config doesn't have a custom value (default is 20)
        const textFontSize = (config.text_font_size && config.text_font_size !== 20) ?
            config.text_font_size : suggestedSizes.text;
        setInputValue('text_font_size', textFontSize);
        updateFontSizeSuggestion('text_font_size', suggestedSizes.text);

        // Styling
        if (config.overlay_color) {
            const hexColor = rgbToHex(config.overlay_color);
            setInputValue('overlay_color', hexColor);
            if (overlayColorPickr) {
                overlayColorPickr.setColor(hexColor);
            }
        }
        const bgColor = config.overlay_background || '#00000000';
        setInputValue('overlay_background', bgColor);
        if (overlayBackgroundPickr) {
            overlayBackgroundPickr.setColor(bgColor);
        }
        setInputValue('overlay_background_opacity', config.overlay_background_opacity !== undefined ? config.overlay_background_opacity : 1.0);

        // Text shadow
        setInputValue('text_shadow_enabled', config.text_shadow_enabled || false);
        const textShadowColor = config.text_shadow_color || '#000000';
        setInputValue('text_shadow_color', textShadowColor);
        if (textShadowColorPickr) {
            textShadowColorPickr.setColor(textShadowColor);
        }
        setInputValue('text_shadow_offset_x', config.text_shadow_offset_x !== undefined ? config.text_shadow_offset_x : 2);
        setInputValue('text_shadow_offset_y', config.text_shadow_offset_y !== undefined ? config.text_shadow_offset_y : 2);

        // State icon background
        const stateIconBgColor = config.state_icon_background || '#00000000';
        setInputValue('state_icon_background', stateIconBgColor);
        if (stateIconBackgroundPickr) {
            stateIconBackgroundPickr.setColor(stateIconBgColor);
        }
        setInputValue('state_icon_background_opacity', config.state_icon_background_opacity !== undefined ? config.state_icon_background_opacity : 1.0);

        // State icon shadow
        setInputValue('state_icon_shadow_enabled', config.state_icon_shadow_enabled || false);
        const stateIconShadowColor = config.state_icon_shadow_color || '#000000';
        setInputValue('state_icon_shadow_color', stateIconShadowColor);
        if (stateIconShadowColorPickr) {
            stateIconShadowColorPickr.setColor(stateIconShadowColor);
        }
        setInputValue('state_icon_shadow_offset_x', config.state_icon_shadow_offset_x !== undefined ? config.state_icon_shadow_offset_x : 2);
        setInputValue('state_icon_shadow_offset_y', config.state_icon_shadow_offset_y !== undefined ? config.state_icon_shadow_offset_y : 2);

        // Stream
        setInputValue('rtsp_url', config.rtsp_url || '');

        // State icons
        renderStateIcons(config.state_icons || []);

        // Update range displays
        document.querySelectorAll('input[type="range"]').forEach(updateValueDisplay);
    }

    function setInputValue(id, value) {
        const input = document.getElementById(id);
        if (!input) return;

        if (input.type === 'checkbox') {
            input.checked = value;
        } else {
            input.value = value;
        }
    }

    function getFormData() {
        // Get current state icons - ensure we have the latest data
        const stateIcons = currentConfig.state_icons || [];

        return {
            source_camera: currentConfig.source_camera,
            entity_name: currentConfig.entity_name,  // Keep the entity name from config
            width: parseInt(document.getElementById('width').value),
            height: parseInt(document.getElementById('height').value),
            keep_ratio: document.getElementById('keep_ratio').checked,
            quality: parseInt(document.getElementById('quality').value),
            crop_enabled: document.getElementById('crop_enabled').checked,
            crop_x: parseInt(document.getElementById('crop_x').value),
            crop_y: parseInt(document.getElementById('crop_y').value),
            crop_width: parseInt(document.getElementById('crop_width').value),
            crop_height: parseInt(document.getElementById('crop_height').value),
            datetime_enabled: document.getElementById('datetime_enabled').checked,
            datetime_format: document.getElementById('datetime_format').value,
            datetime_locale: document.getElementById('datetime_locale').value,
            datetime_position: document.getElementById('datetime_position').value,
            datetime_font_size: parseInt(document.getElementById('datetime_font_size').value),
            text_enabled: document.getElementById('text_enabled').checked,
            text_value: document.getElementById('text_value').value,
            text_position: document.getElementById('text_position').value,
            text_font_size: parseInt(document.getElementById('text_font_size').value),
            overlay_color: hexToRgb(document.getElementById('overlay_color').value),
            overlay_background: document.getElementById('overlay_background').value,
            overlay_background_opacity: parseFloat(document.getElementById('overlay_background_opacity').value),
            text_shadow_enabled: document.getElementById('text_shadow_enabled').checked,
            text_shadow_color: document.getElementById('text_shadow_color').value,
            text_shadow_offset_x: parseInt(document.getElementById('text_shadow_offset_x').value),
            text_shadow_offset_y: parseInt(document.getElementById('text_shadow_offset_y').value),
            state_icon_background: document.getElementById('state_icon_background').value,
            state_icon_background_opacity: parseFloat(document.getElementById('state_icon_background_opacity').value),
            state_icon_shadow_enabled: document.getElementById('state_icon_shadow_enabled').checked,
            state_icon_shadow_color: document.getElementById('state_icon_shadow_color').value,
            state_icon_shadow_offset_x: parseInt(document.getElementById('state_icon_shadow_offset_x').value),
            state_icon_shadow_offset_y: parseInt(document.getElementById('state_icon_shadow_offset_y').value),
            rtsp_url: document.getElementById('rtsp_url').value,
            state_icons: stateIcons,
            source_width: currentConfig.source_width,
            source_height: currentConfig.source_height
        };
    }

    async function saveConfig() {
        if (!currentCameraId) return;

        try {
            const saveBtn = document.getElementById('save-config-btn');
            saveBtn.disabled = true;
            saveBtn.textContent = '💾 Saving...';

            const formData = getFormData();

            const response = await authenticatedFetch(`/api/camera_snapshot_processor/cameras/${currentCameraId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ config: formData })
            });

            const data = await response.json();

            if (!data.success) {
                throw new Error(data.error || 'Failed to save configuration');
            }

            showSuccess('Configuration saved successfully!');
            currentConfig = formData;
            cameras[currentCameraId] = formData;
            renderCameraList();
        } catch (error) {
            showError('Failed to save configuration: ' + error.message);
        } finally {
            const saveBtn = document.getElementById('save-config-btn');
            saveBtn.disabled = false;
            saveBtn.textContent = '💾 Save';
        }
    }

    // ==================== Preview Management ====================

    function schedulePreviewUpdate() {
        clearTimeout(previewUpdateTimeout);
        previewUpdateTimeout = setTimeout(refreshPreview, 1000);
    }

    async function refreshPreview() {
        if (!currentCameraId) return;

        try {
            const loading = document.getElementById('loading');
            const previewImage = document.getElementById('preview-image');
            const wrapper = document.getElementById('preview-image-wrapper');

            loading.style.display = 'block';
            wrapper.classList.remove('loaded');

            const formData = getFormData();

            const response = await authenticatedFetch(`/api/camera_snapshot_processor/cameras/${currentCameraId}/preview`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ config: formData })
            });

            if (!response.ok) {
                throw new Error('Failed to generate preview');
            }

            const blob = await response.blob();
            const imageUrl = URL.createObjectURL(blob);

            previewImage.onload = () => {
                loading.style.display = 'none';
                const wrapper = document.getElementById('preview-image-wrapper');
                wrapper.classList.add('loaded');

                // Calculate actual output dimensions (accounting for aspect ratio)
                const actualDimensions = calculateActualDimensions(formData);

                // Update preview info
                const previewDim = document.getElementById('preview-dimensions');
                if (previewDim) {
                    if (actualDimensions.width !== formData.width || actualDimensions.height !== formData.height) {
                        previewDim.textContent = `Output: ${actualDimensions.width} × ${actualDimensions.height}px (adjusted for aspect ratio)`;
                        previewDim.style.color = '#ff9800';
                        previewDim.style.fontWeight = '600';
                    } else {
                        previewDim.textContent = `Output: ${formData.width} × ${formData.height}px`;
                        previewDim.style.color = '#667eea';
                        previewDim.style.fontWeight = '600';
                    }
                }

                // Update image size display with comparison
                const imageSize = document.getElementById('image-size');
                if (imageSize) {
                    const processedSizeBytes = blob.size; // We have the blob from above
                    const processedSizeKB = (processedSizeBytes / 1024).toFixed(1);

                    if (sourceImageSize > 0) {
                        const originalSizeKB = (sourceImageSize / 1024).toFixed(1);
                        const percentChange = (((sourceImageSize - processedSizeBytes) / sourceImageSize) * 100).toFixed(1);

                        if (processedSizeBytes < sourceImageSize) {
                            // Size decreased
                            imageSize.textContent = `Processed file size: ${processedSizeKB} KB (${originalSizeKB} KB original, ${percentChange}% smaller)`;
                            imageSize.style.color = '#4caf50'; // Green for reduction
                        } else if (processedSizeBytes > sourceImageSize) {
                            // Size increased
                            const percentIncrease = Math.abs(parseFloat(percentChange)).toFixed(1);
                            imageSize.textContent = `Processed file size: ${processedSizeKB} KB (${originalSizeKB} KB original, ${percentIncrease}% larger)`;
                            imageSize.style.color = '#ff9800'; // Orange for increase
                        } else {
                            // Size unchanged
                            imageSize.textContent = `Processed file size: ${processedSizeKB} KB (same as original)`;
                            imageSize.style.color = '#9c27b0'; // Purple for no change
                        }
                    } else {
                        // Fallback if original size not available
                        imageSize.textContent = `Processed file size: ${processedSizeKB} KB`;
                        imageSize.style.color = '#9c27b0';
                    }
                    imageSize.style.fontWeight = '600';
                }

                // Update crop box position
                updateCropBox();

                // Update interaction state
                updateCropInteractionState();
                updateCropVisibility(); // Don't await here as it's in an onload callback
            };

            previewImage.src = imageUrl;

            // Load source image dimensions if not already loaded
            if (!sourceImageDimensions.width) {
                await loadSourceImage();
            }
        } catch (error) {
            document.getElementById('loading').style.display = 'none';
            console.error('Failed to generate preview:', error);
            showError('Failed to generate preview: ' + error.message);
        }
    }

    async function loadSourceImage() {
        if (!currentCameraId) return;

        try {
            const response = await authenticatedFetch(`/api/camera_snapshot_processor/cameras/${currentCameraId}/source`);

            if (!response.ok) {
                throw new Error('Failed to load source image');
            }

            const width = parseInt(response.headers.get('X-Image-Width'));
            const height = parseInt(response.headers.get('X-Image-Height'));

            sourceImageDimensions = { width, height };

            // Get the blob to calculate original file size
            const blob = await response.blob();
            sourceImageSize = blob.size;

            // Store source image for cropping
            const imageUrl = URL.createObjectURL(blob);
            const img = new Image();
            img.onload = () => {
                sourceImageData = img;
                // Update source image element
                const sourceImg = document.getElementById('source-image');
                if (sourceImg) {
                    sourceImg.src = imageUrl;
                }
                // Update crop preview if crop is enabled
                updateCropVisibility();
                updateCropPreview();
            };
            img.src = imageUrl;

            const sourceDim = document.getElementById('source-dimensions');
            if (sourceDim) {
                sourceDim.textContent = `Source: ${width} × ${height}px`;
                sourceDim.style.color = '#4caf50';
                sourceDim.style.fontWeight = '600';
            }

            // Update slider ranges: min=100, max=source dimensions (prevent upscaling by default)
            const widthSlider = document.getElementById('width-slider');
            const heightSlider = document.getElementById('height-slider');

            widthSlider.min = 100;
            widthSlider.max = width;
            heightSlider.min = 100;
            heightSlider.max = height;

            // Update slider labels
            document.querySelector('.width-slider-min').textContent = '100';
            document.querySelector('.width-slider-max').textContent = width;
            document.querySelector('.height-slider-min').textContent = '100';
            document.querySelector('.height-slider-max').textContent = height;

            // Update crop defaults to match source dimensions
            updateCropDimensionsFromSource();

            // Store source dimensions in config
            if (!currentConfig.source_width) {
                currentConfig.source_width = width;
                currentConfig.source_height = height;
            }

            // Update dimensions display immediately
            updateDimensionsDisplay();
        } catch (error) {
            console.error('Failed to load source image:', error);
        }
    }

    function updateCropDimensionsFromSource() {
        if (sourceImageDimensions.width && sourceImageDimensions.height) {
            // Only update if crop is not manually enabled
            if (!document.getElementById('crop_enabled').checked) {
                setInputValue('crop_width', sourceImageDimensions.width);
                setInputValue('crop_height', sourceImageDimensions.height);
            }
        }
    }

    function updateCropPreview() {
        // Debounced update of crop preview
        clearTimeout(cropPreviewDebounceTimer);
        cropPreviewDebounceTimer = setTimeout(() => {
            drawCropPreview();
        }, 100); // 100ms debounce
    }

    function drawCropPreview() {
        if (!sourceImageData || !document.getElementById('crop_enabled').checked || currentTab !== 'crop') {
            return;
        }

        const canvas = document.getElementById('cropped-preview-canvas');
        const ctx = canvas.getContext('2d');

        const cropX = parseInt(document.getElementById('crop_x').value) || 0;
        const cropY = parseInt(document.getElementById('crop_y').value) || 0;
        const cropWidth = parseInt(document.getElementById('crop_width').value) || sourceImageDimensions.width;
        const cropHeight = parseInt(document.getElementById('crop_height').value) || sourceImageDimensions.height;

        // Validate crop boundaries
        const validCropX = Math.max(0, Math.min(cropX, sourceImageDimensions.width));
        const validCropY = Math.max(0, Math.min(cropY, sourceImageDimensions.height));
        const validCropWidth = Math.min(cropWidth, sourceImageDimensions.width - validCropX);
        const validCropHeight = Math.min(cropHeight, sourceImageDimensions.height - validCropY);

        // Set canvas size to crop dimensions
        canvas.width = validCropWidth;
        canvas.height = validCropHeight;

        // Draw the cropped portion
        ctx.drawImage(
            sourceImageData,
            validCropX, validCropY, validCropWidth, validCropHeight,
            0, 0, validCropWidth, validCropHeight
        );
    }

    function isCropped() {
        // Check if current crop settings differ from source dimensions
        if (!sourceImageDimensions.width || !sourceImageDimensions.height) {
            return false;
        }

        const cropX = parseInt(document.getElementById('crop_x').value) || 0;
        const cropY = parseInt(document.getElementById('crop_y').value) || 0;
        const cropWidth = parseInt(document.getElementById('crop_width').value) || sourceImageDimensions.width;
        const cropHeight = parseInt(document.getElementById('crop_height').value) || sourceImageDimensions.height;

        return cropX !== 0 || cropY !== 0 ||
               cropWidth !== sourceImageDimensions.width ||
               cropHeight !== sourceImageDimensions.height;
    }

    function updateCropInteractionState() {
        const cropEnabled = document.getElementById('crop_enabled').checked;
        const resetBtn = document.getElementById('reset-crop-btn');

        if (cropEnabled && isCropped()) {
            // Image is cropped - show reset button
            resetBtn.style.display = 'inline-block';
        } else if (cropEnabled) {
            // Crop enabled but not yet cropped - show reset button (always visible for easy reset)
            resetBtn.style.display = 'inline-block';
        } else {
            // Crop not enabled - hide reset button
            resetBtn.style.display = 'none';
        }

        // Always enable crop input fields when crop is enabled (allow multiple adjustments)
        if (cropEnabled) {
            ['crop_x', 'crop_y', 'crop_width', 'crop_height'].forEach(id => {
                document.getElementById(id).disabled = false;
            });
        }
    }

    async function updateCropVisibility() {
        const cropEnabled = document.getElementById('crop_enabled').checked;
        const cropOverlay = document.getElementById('crop-overlay');
        const onCropTab = currentTab === 'crop';

        const sourceImageSection = document.getElementById('source-image-section');
        const croppedPreviewSection = document.getElementById('cropped-preview-section');
        const previewImageWrapper = document.getElementById('preview-image-wrapper');

        // Show dual-image layout only when on crop tab and crop enabled
        if (onCropTab && cropEnabled) {
            // Ensure source image is loaded
            if (!sourceImageData && currentCameraId) {
                await loadSourceImage();
            }

            if (sourceImageData) {
                // Show dual-image cropping interface
                sourceImageSection.style.display = 'block';
                croppedPreviewSection.style.display = 'block';
                previewImageWrapper.style.display = 'none';
                cropOverlay.style.display = 'block';

                // Update crop box position
                updateCropBox();

                // Update cropped preview
                updateCropPreview();
            } else {
                // Fallback to regular preview if source image failed to load
                sourceImageSection.style.display = 'none';
                croppedPreviewSection.style.display = 'none';
                previewImageWrapper.style.display = 'block';
                cropOverlay.style.display = 'none';
            }
        } else {
            // Show regular preview image
            sourceImageSection.style.display = 'none';
            croppedPreviewSection.style.display = 'none';
            previewImageWrapper.style.display = 'block';
            cropOverlay.style.display = 'none';
        }
    }

    function resetCrop() {
        if (!sourceImageDimensions.width || !sourceImageDimensions.height) {
            showWarning('Please wait for the source image to load first');
            return;
        }

        // Reset crop to full source dimensions
        setInputValue('crop_x', 0);
        setInputValue('crop_y', 0);
        setInputValue('crop_width', sourceImageDimensions.width);
        setInputValue('crop_height', sourceImageDimensions.height);

        // Reset output dimensions to source dimensions
        setInputValue('width', sourceImageDimensions.width);
        setInputValue('height', sourceImageDimensions.height);
        document.getElementById('width-slider').value = sourceImageDimensions.width;
        document.getElementById('height-slider').value = sourceImageDimensions.height;

        // Update crop box visually
        updateCropBox();

        // Re-enable interactive cropping
        updateCropInteractionState();
        updateCropVisibility(); // Don't await in sync function

        // Update dimensions display
        updateDimensionsDisplay();

        // Refresh preview
        schedulePreviewUpdate();

        showSuccess('Crop and dimensions reset to original');
    }

    function updateDimensionsDisplay() {
        if (!sourceImageDimensions.width) return;

        const formData = getFormData();
        const actualDimensions = calculateActualDimensions(formData);

        const previewDim = document.getElementById('preview-dimensions');
        if (previewDim) {
            if (actualDimensions.width !== formData.width || actualDimensions.height !== formData.height) {
                previewDim.textContent = `Output: ${actualDimensions.width} × ${actualDimensions.height}px (adjusted for aspect ratio)`;
                previewDim.style.color = '#ff9800';
                previewDim.style.fontWeight = '600';
            } else {
                previewDim.textContent = `Output: ${formData.width} × ${formData.height}px`;
                previewDim.style.color = '#667eea';
                previewDim.style.fontWeight = '600';
            }
        }

        // Update effective source dimensions display
        updateEffectiveSourceSize();
    }

    function updateEffectiveSourceSize() {
        const effectiveSizeEl = document.getElementById('effective-source-dimensions');
        if (!effectiveSizeEl || !sourceImageDimensions.width) return;

        const formData = getFormData();

        if (formData.crop_enabled) {
            // Crop enabled - show cropped dimensions
            const cropWidth = formData.crop_width;
            const cropHeight = formData.crop_height;
            effectiveSizeEl.textContent = `${cropWidth} × ${cropHeight}px (cropped from ${sourceImageDimensions.width} × ${sourceImageDimensions.height}px)`;
            effectiveSizeEl.style.color = '#ff9800';
        } else {
            // No crop - show original dimensions
            effectiveSizeEl.textContent = `${sourceImageDimensions.width} × ${sourceImageDimensions.height}px (original camera resolution)`;
            effectiveSizeEl.style.color = '#4caf50';
        }
    }

    // ==================== Interactive Crop ====================

    function setupCropInteraction() {
        const sourceImage = document.getElementById('source-image');
        const cropOverlay = document.getElementById('crop-overlay');
        const cropBox = cropOverlay.querySelector('.crop-box');

        // Make crop box draggable
        cropBox.addEventListener('mousedown', startDragCrop);

        // Make handles resizable
        const handles = cropBox.querySelectorAll('.crop-handle');
        handles.forEach(handle => {
            handle.addEventListener('mousedown', (e) => {
                e.stopPropagation();
                startResizeCrop(e, handle.classList[1]); // nw, ne, sw, se
            });
        });

        // Update crop box when crop inputs change
        ['crop_x', 'crop_y', 'crop_width', 'crop_height'].forEach(id => {
            document.getElementById(id).addEventListener('input', async () => {
                updateCropBox();
                updateCropInteractionState();
                await updateCropVisibility();
                updateEffectiveSourceSize();
            });
        });

        // Update crop box when source image loads
        sourceImage.addEventListener('load', updateCropBox);
    }

    function startDragCrop(e) {
        e.preventDefault();
        cropDragging = true;

        cropStartX = e.clientX;
        cropStartY = e.clientY;

        const currentX = parseInt(document.getElementById('crop_x').value);
        const currentY = parseInt(document.getElementById('crop_y').value);

        const mousemove = (e) => {
            if (!cropDragging) return;

            const deltaX = e.clientX - cropStartX;
            const deltaY = e.clientY - cropStartY;

            // Convert pixel delta to source image coordinates
            const sourceImage = document.getElementById('source-image');
            const scaleX = sourceImageDimensions.width / sourceImage.clientWidth;
            const scaleY = sourceImageDimensions.height / sourceImage.clientHeight;

            const newX = Math.max(0, Math.min(sourceImageDimensions.width - parseInt(document.getElementById('crop_width').value), currentX + deltaX * scaleX));
            const newY = Math.max(0, Math.min(sourceImageDimensions.height - parseInt(document.getElementById('crop_height').value), currentY + deltaY * scaleY));

            setInputValue('crop_x', Math.round(newX));
            setInputValue('crop_y', Math.round(newY));
            updateCropBox();
            updateCropPreview(); // Update crop preview immediately
        };

        const mouseup = () => {
            cropDragging = false;
            document.removeEventListener('mousemove', mousemove);
            document.removeEventListener('mouseup', mouseup);
        };

        document.addEventListener('mousemove', mousemove);
        document.addEventListener('mouseup', mouseup);
    }

    function startResizeCrop(e, handlePosition) {
        e.preventDefault();
        cropResizing = true;

        const sourceImage = document.getElementById('source-image');
        cropStartX = e.clientX;
        cropStartY = e.clientY;

        const startX = parseInt(document.getElementById('crop_x').value);
        const startY = parseInt(document.getElementById('crop_y').value);
        const startWidth = parseInt(document.getElementById('crop_width').value);
        const startHeight = parseInt(document.getElementById('crop_height').value);

        const mousemove = (e) => {
            if (!cropResizing) return;

            const deltaX = e.clientX - cropStartX;
            const deltaY = e.clientY - cropStartY;

            // Convert pixel delta to source image coordinates
            const sourceImage = document.getElementById('source-image');
            const scaleX = sourceImageDimensions.width / sourceImage.clientWidth;
            const scaleY = sourceImageDimensions.height / sourceImage.clientHeight;

            let newX = startX;
            let newY = startY;
            let newWidth = startWidth;
            let newHeight = startHeight;

            if (handlePosition.includes('w')) {
                // Left side
                const dx = deltaX * scaleX;
                newX = Math.max(0, startX + dx);
                newWidth = startWidth - (newX - startX);
            }
            if (handlePosition.includes('e')) {
                // Right side
                newWidth = Math.min(sourceImageDimensions.width - newX, startWidth + deltaX * scaleX);
            }
            if (handlePosition.includes('n')) {
                // Top
                const dy = deltaY * scaleY;
                newY = Math.max(0, startY + dy);
                newHeight = startHeight - (newY - startY);
            }
            if (handlePosition.includes('s')) {
                // Bottom
                newHeight = Math.min(sourceImageDimensions.height - newY, startHeight + deltaY * scaleY);
            }

            // Ensure minimum size
            newWidth = Math.max(10, newWidth);
            newHeight = Math.max(10, newHeight);

            setInputValue('crop_x', Math.round(newX));
            setInputValue('crop_y', Math.round(newY));
            setInputValue('crop_width', Math.round(newWidth));
            setInputValue('crop_height', Math.round(newHeight));
            updateCropBox();
            updateCropPreview(); // Update crop preview immediately
        };

        const mouseup = () => {
            cropResizing = false;
            document.removeEventListener('mousemove', mousemove);
            document.removeEventListener('mouseup', mouseup);
        };

        document.addEventListener('mousemove', mousemove);
        document.addEventListener('mouseup', mouseup);
    }

    function updateCropBox() {
        const cropOverlay = document.getElementById('crop-overlay');
        const cropBox = cropOverlay.querySelector('.crop-box');

        // Use source image when in dual-image crop mode
        const sourceImage = document.getElementById('source-image');

        if (!sourceImage || !sourceImage.complete || !sourceImageDimensions.width) return;

        const cropX = parseInt(document.getElementById('crop_x').value) || 0;
        const cropY = parseInt(document.getElementById('crop_y').value) || 0;
        const cropWidth = parseInt(document.getElementById('crop_width').value) || sourceImageDimensions.width;
        const cropHeight = parseInt(document.getElementById('crop_height').value) || sourceImageDimensions.height;

        // Calculate position and size based on the actual rendered image dimensions
        // The image is rendered with natural aspect ratio maintained
        const scaleX = sourceImage.clientWidth / sourceImageDimensions.width;
        const scaleY = sourceImage.clientHeight / sourceImageDimensions.height;

        const left = cropX * scaleX;
        const top = cropY * scaleY;
        const width = cropWidth * scaleX;
        const height = cropHeight * scaleY;

        cropBox.style.left = `${left}px`;
        cropBox.style.top = `${top}px`;
        cropBox.style.width = `${width}px`;
        cropBox.style.height = `${height}px`;
    }

    // ==================== State Icons Management ====================

    async function loadEntities() {
        try {
            const response = await authenticatedFetch('/api/camera_snapshot_processor/entities');
            const data = await response.json();

            if (!data.success) {
                throw new Error(data.error || 'Failed to load entities');
            }

            entities = data.entities.sort((a, b) => a.entity_id.localeCompare(b.entity_id));
            populateEntitySelect();
        } catch (error) {
            console.error('Failed to load entities:', error);
        }
    }

    function populateEntitySelect() {
        // Setup searchable entity dropdown
        const searchInput = document.getElementById('icon-entity-search');
        const dropdown = document.getElementById('entity-dropdown');
        const dropdownList = document.getElementById('entity-dropdown-list');
        const hiddenInput = document.getElementById('icon-entity');
        const selectedDisplay = document.getElementById('selected-entity');
        const selectedText = document.getElementById('selected-entity-text');
        const clearBtn = document.getElementById('clear-entity');

        // Render all entities initially
        renderEntityDropdown('');

        // Search input handler
        searchInput.addEventListener('input', (e) => {
            const query = e.target.value.toLowerCase();
            renderEntityDropdown(query);
            dropdown.style.display = 'block';
        });

        // Show dropdown on focus
        searchInput.addEventListener('focus', () => {
            if (!hiddenInput.value) {
                dropdown.style.display = 'block';
                renderEntityDropdown(searchInput.value.toLowerCase());
            }
        });

        // Hide dropdown on click outside
        document.addEventListener('click', (e) => {
            if (!e.target.closest('.form-group')) {
                dropdown.style.display = 'none';
            }
        });

        // Clear selection
        clearBtn.addEventListener('click', () => {
            hiddenInput.value = '';
            searchInput.value = '';
            searchInput.disabled = false;
            selectedDisplay.style.display = 'none';
            searchInput.focus();
        });
    }

    function renderEntityDropdown(query) {
        const dropdownList = document.getElementById('entity-dropdown-list');
        dropdownList.innerHTML = '';

        const filtered = entities.filter(entity => {
            return entity.entity_id.toLowerCase().includes(query) ||
                   entity.name.toLowerCase().includes(query) ||
                   entity.domain.toLowerCase().includes(query);
        });

        if (filtered.length === 0) {
            dropdownList.innerHTML = '<div class="entity-dropdown-item" style="cursor: default; color: #999;">No entities found</div>';
            return;
        }

        // Limit to 50 results for performance
        filtered.slice(0, 50).forEach(entity => {
            const item = document.createElement('div');
            item.className = 'entity-dropdown-item';
            item.innerHTML = `
                <strong>${entity.name}</strong>
                <small>${entity.entity_id} <span class="entity-domain">${entity.domain}</span></small>
            `;
            item.addEventListener('click', () => selectEntity(entity));
            dropdownList.appendChild(item);
        });

        if (filtered.length > 50) {
            const moreItem = document.createElement('div');
            moreItem.className = 'entity-dropdown-item';
            moreItem.style.cssText = 'cursor: default; color: #999; text-align: center; font-style: italic;';
            moreItem.textContent = `... and ${filtered.length - 50} more. Refine your search.`;
            dropdownList.appendChild(moreItem);
        }
    }

    function selectEntity(entity) {
        const searchInput = document.getElementById('icon-entity-search');
        const dropdown = document.getElementById('entity-dropdown');
        const hiddenInput = document.getElementById('icon-entity');
        const selectedDisplay = document.getElementById('selected-entity');
        const selectedText = document.getElementById('selected-entity-text');

        hiddenInput.value = entity.entity_id;
        searchInput.value = '';
        searchInput.disabled = true;
        selectedText.textContent = `${entity.name} (${entity.entity_id})`;
        selectedDisplay.style.display = 'flex';
        dropdown.style.display = 'none';

        // Show suggested states for this entity
        if (window.stateIconManager) {
            window.stateIconManager.showSuggestedStates(entity.entity_id);
        }
    }

    function renderStateIcons(icons) {
        const list = document.getElementById('state-icons-list');
        list.innerHTML = '';

        if (!icons || icons.length === 0) {
            list.innerHTML = '<p class="help-text">No state icons configured. Click "Add State Icon" to create one.</p>';
            return;
        }

        icons.forEach((icon, index) => {
            const item = document.createElement('div');
            item.className = 'state-icon-item';

            // Determine rule count
            const ruleCount = icon.state_rules ? icon.state_rules.length :
                             (icon.state_on && icon.state_off ? 2 : 0);

            item.innerHTML = `
                <div class="state-icon-info">
                    <strong>${icon.entity}</strong>
                    <span>
                        ${icon.label ? `Label: ${icon.label} | ` : ''}
                        ${ruleCount} state rule${ruleCount !== 1 ? 's' : ''} |
                        Position: ${icon.position} |
                        Font: ${icon.font_size || 18}pt
                    </span>
                </div>
                <div class="state-icon-actions">
                    <button class="btn btn-secondary btn-sm" onclick="window.editStateIcon(${index})">✏️ Edit</button>
                    <button class="btn btn-danger btn-sm" onclick="window.removeStateIcon(${index})">🗑️ Remove</button>
                </div>
            `;
            list.appendChild(item);
        });
    }

    window.removeStateIcon = function(index) {
        currentConfig.state_icons = currentConfig.state_icons || [];
        currentConfig.state_icons.splice(index, 1);
        renderStateIcons(currentConfig.state_icons);
        schedulePreviewUpdate();
    };

    window.editStateIcon = function(index) {
        editingStateIconIndex = index;
        const icon = currentConfig.state_icons[index];

        // Populate entity with searchable selector
        const hiddenInput = document.getElementById('icon-entity');
        const searchInput = document.getElementById('icon-entity-search');
        const selectedDisplay = document.getElementById('selected-entity');
        const selectedText = document.getElementById('selected-entity-text');

        const entity = entities.find(e => e.entity_id === icon.entity);
        if (entity) {
            hiddenInput.value = entity.entity_id;
            searchInput.value = '';
            searchInput.disabled = true;
            selectedText.textContent = `${entity.name} (${entity.entity_id})`;
            selectedDisplay.style.display = 'flex';
        }

        // Populate label and position
        document.getElementById('icon-label').value = icon.label || '';
        document.getElementById('icon-show-label').checked = icon.show_label !== false;
        document.getElementById('icon-position').value = icon.position || 'bottom_right';

        // Calculate suggested font size for state icons based on current output dimensions
        const actualDimensions = calculateActualDimensions(currentConfig);
        const suggestedSizes = calculateSuggestedFontSizes(actualDimensions.width, actualDimensions.height);

        const fontSizeInput = document.getElementById('icon-font-size');
        // Use suggested size if icon doesn't have a custom value (default is 18)
        const iconFontSize = (icon.font_size && icon.font_size !== 18) ?
            icon.font_size : suggestedSizes.stateIcon;
        fontSizeInput.value = iconFontSize;
        updateValueDisplay(fontSizeInput);
        updateFontSizeSuggestion('icon-font-size', suggestedSizes.stateIcon);

        // Load state rules into the state icon manager
        if (window.stateIconManager) {
            // Convert legacy format to new format if needed
            const stateRules = icon.state_rules || convertLegacyToStateRules(icon);
            window.stateIconManager.loadStateRules(stateRules, icon.entity);
        }

        // Update modal title
        document.querySelector('#state-icon-modal .modal-header h3').textContent = 'Edit State Icon';
        document.getElementById('save-state-icon').textContent = 'Update Configuration';

        document.getElementById('state-icon-modal').classList.add('active');
    };

    function openStateIconModal() {
        editingStateIconIndex = null;
        document.querySelector('#state-icon-modal .modal-header h3').textContent = 'Configure State Icon';
        document.getElementById('save-state-icon').textContent = 'Save Configuration';

        // Calculate suggested font size for state icons based on current output dimensions
        const actualDimensions = calculateActualDimensions(currentConfig);
        const suggestedSizes = calculateSuggestedFontSizes(actualDimensions.width, actualDimensions.height);

        // Set suggested font size as default for new state icons
        const fontSizeInput = document.getElementById('icon-font-size');
        fontSizeInput.value = suggestedSizes.stateIcon;
        updateValueDisplay(fontSizeInput);
        updateFontSizeSuggestion('icon-font-size', suggestedSizes.stateIcon);

        // Initialize empty state rules
        if (window.stateIconManager) {
            window.stateIconManager.loadStateRules([], null);
        }

        document.getElementById('state-icon-modal').classList.add('active');
    }

    function closeStateIconModal() {
        document.getElementById('state-icon-modal').classList.remove('active');

        // Reset searchable entity selector
        const hiddenInput = document.getElementById('icon-entity');
        const searchInput = document.getElementById('icon-entity-search');
        const selectedDisplay = document.getElementById('selected-entity');
        const dropdown = document.getElementById('entity-dropdown');

        hiddenInput.value = '';
        searchInput.value = '';
        searchInput.disabled = false;
        selectedDisplay.style.display = 'none';
        dropdown.style.display = 'none';

        // Reset form
        document.getElementById('icon-label').value = '';
        document.getElementById('icon-show-label').checked = true;
        document.getElementById('icon-position').value = 'bottom_right';
        document.getElementById('icon-font-size').value = '18';

        // Clear state rules
        if (window.stateIconManager) {
            window.stateIconManager.loadStateRules([], null);
        }

        // Remove suggested states if present
        const suggestedStates = document.querySelector('.suggested-states');
        if (suggestedStates) {
            suggestedStates.remove();
        }
    }

    function saveStateIcon() {
        const entity = document.getElementById('icon-entity').value;
        if (!entity) {
            showWarning('Please select an entity');
            return;
        }

        // Get state rules from state icon manager
        const stateRules = window.stateIconManager ? window.stateIconManager.getStateRules() : [];

        if (stateRules.length === 0) {
            showWarning('Please add at least one state rule');
            return;
        }

        const iconConfig = {
            entity: entity,
            label: document.getElementById('icon-label').value,
            show_label: document.getElementById('icon-show-label').checked,
            label_color: hexToRgb('#ffffff'),
            position: document.getElementById('icon-position').value,
            font_size: parseInt(document.getElementById('icon-font-size').value),
            state_rules: stateRules
        };

        currentConfig.state_icons = currentConfig.state_icons || [];

        if (editingStateIconIndex !== null) {
            // Update existing icon
            currentConfig.state_icons[editingStateIconIndex] = iconConfig;
        } else {
            // Add new icon
            currentConfig.state_icons.push(iconConfig);
        }

        renderStateIcons(currentConfig.state_icons);
        closeStateIconModal();
        schedulePreviewUpdate();
    }

    // Helper function to convert legacy icon format to new state rules format
    function convertLegacyToStateRules(icon) {
        const rules = [];

        // Add ON state rule if configured
        if (icon.state_on) {
            rules.push({
                condition: 'equals',
                value: icon.state_on,
                icon: icon.icon_on || '💡',
                text: icon.text_on || 'ON',
                icon_color: icon.icon_color_on || icon.color_on || [255, 215, 0],
                text_color: icon.text_color_on || [255, 255, 255],
                is_default: false
            });
        }

        // Add OFF state rule if configured
        if (icon.state_off) {
            rules.push({
                condition: 'equals',
                value: icon.state_off,
                icon: icon.icon_off || '🌑',
                text: icon.text_off || 'OFF',
                icon_color: icon.icon_color_off || icon.color_off || [100, 100, 100],
                text_color: icon.text_color_off || [150, 150, 150],
                is_default: false
            });
        }

        return rules;
    }

    // ==================== UI Utilities ====================

    function switchTab(tabName) {
        document.querySelectorAll('.tab').forEach(tab => {
            tab.classList.toggle('active', tab.dataset.tab === tabName);
        });

        document.querySelectorAll('.tab-pane').forEach(pane => {
            pane.classList.toggle('active', pane.id === `tab-${tabName}`);
        });
    }

    function updateValueDisplay(input) {
        const valueDisplay = document.getElementById(`${input.id}-value`);
        if (valueDisplay) {
            valueDisplay.textContent = input.value;
        }
    }

    /**
     * Update font size suggestion display next to an input
     * @param {string} inputId - The ID of the font size input
     * @param {number} suggestedSize - The suggested font size
     */
    function updateFontSizeSuggestion(inputId, suggestedSize) {
        const input = document.getElementById(inputId);
        if (!input) return;

        // Find or create suggestion element
        let suggestionEl = document.getElementById(`${inputId}-suggestion`);
        if (!suggestionEl) {
            suggestionEl = document.createElement('span');
            suggestionEl.id = `${inputId}-suggestion`;
            suggestionEl.className = 'font-size-suggestion';
            suggestionEl.style.cssText = 'margin-left: 10px; color: #667eea; font-size: 12px; font-style: italic;';

            // Insert after the value display
            const valueDisplay = document.getElementById(`${inputId}-value`);
            if (valueDisplay && valueDisplay.parentNode) {
                valueDisplay.parentNode.insertBefore(suggestionEl, valueDisplay.nextSibling);
            } else {
                input.parentNode.appendChild(suggestionEl);
            }
        }

        // Update suggestion text
        const currentValue = parseInt(input.value);
        if (currentValue === suggestedSize) {
            suggestionEl.textContent = '(suggested)';
            suggestionEl.style.color = '#4caf50';
        } else {
            suggestionEl.textContent = `(suggested: ${suggestedSize}pt)`;
            suggestionEl.style.color = '#667eea';
        }
    }

    /**
     * Update all font size suggestions based on current output dimensions
     * Called when dimensions change to update suggestions in real-time
     */
    function updateFontSizeSuggestions() {
        if (!currentConfig) return;

        const formData = getFormData();
        const actualDimensions = calculateActualDimensions(formData);
        const suggestedSizes = calculateSuggestedFontSizes(actualDimensions.width, actualDimensions.height);

        // Update datetime font size suggestion
        updateFontSizeSuggestion('datetime_font_size', suggestedSizes.datetime);

        // Update text font size suggestion
        updateFontSizeSuggestion('text_font_size', suggestedSizes.text);

        // Note: State icon font size is updated only when modal is opened
        // as it's not part of the main form
    }

    // ==================== Utility Functions ====================

    /**
     * Calculate suggested font size based on output image dimensions
     * @param {number} width - Output image width
     * @param {number} height - Output image height
     * @returns {object} - Suggested font sizes for different overlay types
     */
    function calculateSuggestedFontSizes(width, height) {
        // Use the smaller dimension as the base for calculations
        const baseDimension = Math.min(width, height);

        // Font size calculations (as % of base dimension)
        // These ensure text is readable but not overwhelming
        const suggestions = {
            datetime: Math.max(12, Math.min(36, Math.round(baseDimension * 0.022))),  // ~2.2% of base
            text: Math.max(12, Math.min(32, Math.round(baseDimension * 0.019))),      // ~1.9% of base
            stateIcon: Math.max(14, Math.min(28, Math.round(baseDimension * 0.017)))  // ~1.7% of base
        };

        return suggestions;
    }

    function calculateActualDimensions(config) {
        // Calculate actual output dimensions accounting for aspect ratio
        if (!config.keep_ratio || !sourceImageDimensions.width) {
            return { width: config.width, height: config.height };
        }

        // Get source dimensions (after crop if enabled)
        let sourceWidth = sourceImageDimensions.width;
        let sourceHeight = sourceImageDimensions.height;

        if (config.crop_enabled) {
            sourceWidth = config.crop_width;
            sourceHeight = config.crop_height;
        }

        // Calculate aspect ratio
        const sourceRatio = sourceWidth / sourceHeight;
        const targetRatio = config.width / config.height;

        let actualWidth = config.width;
        let actualHeight = config.height;

        if (Math.abs(sourceRatio - targetRatio) > 0.01) {
            // Aspect ratios differ - need to adjust
            if (sourceRatio > targetRatio) {
                // Source is wider - adjust width
                actualWidth = Math.round(config.height * sourceRatio);
            } else {
                // Source is taller - adjust height
                actualHeight = Math.round(config.width / sourceRatio);
            }
        }

        return { width: actualWidth, height: actualHeight };
    }

    function hexToRgb(hex) {
        const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
        return result ? [
            parseInt(result[1], 16),
            parseInt(result[2], 16),
            parseInt(result[3], 16)
        ] : [255, 255, 255];
    }

    function rgbToHex(rgb) {
        if (!Array.isArray(rgb) || rgb.length < 3) return '#ffffff';
        return '#' + rgb.slice(0, 3).map(x => {
            const hex = x.toString(16);
            return hex.length === 1 ? '0' + hex : hex;
        }).join('');
    }
})();
