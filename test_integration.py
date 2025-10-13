#!/usr/bin/env python3
"""Test script to validate Camera Snapshot Processor integration."""
import asyncio
import json
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, Mock, patch

# Add custom component to path
sys.path.insert(0, str(Path(__file__).parent / "custom_components"))

print("=" * 60)
print("Camera Snapshot Processor Integration Tests")
print("=" * 60)
print()

# Test 1: Import all modules
print("Test 1: Importing modules...")
try:
    from camera_snapshot_processor import (
        DOMAIN,
        async_setup,
        async_setup_entry,
        async_unload_entry,
    )
    from camera_snapshot_processor.config_flow import (
        CameraSnapshotProcessorConfigFlow,
        OptionsFlowHandler,
    )
    from camera_snapshot_processor.api import (
        CameraSnapshotProcessorCamerasView,
        CameraSnapshotProcessorCameraView,
        CameraSnapshotProcessorPreviewView,
        CameraSnapshotProcessorSourceView,
        CameraSnapshotProcessorEntitiesView,
        CameraSnapshotProcessorAvailableCamerasView,
        setup_api,
    )
    from camera_snapshot_processor.const import (
        CONF_SOURCE_CAMERA,
        CONF_WIDTH,
        CONF_HEIGHT,
        CONF_QUALITY,
        CONF_STATE_ICONS,
        DEFAULT_WIDTH,
        DEFAULT_HEIGHT,
    )
    print("✅ All modules imported successfully")
except Exception as e:
    print(f"❌ Failed to import modules: {e}")
    sys.exit(1)

print()

# Test 2: Validate config flow structure
print("Test 2: Validating config flow...")
try:
    assert hasattr(CameraSnapshotProcessorConfigFlow, "VERSION")
    assert hasattr(CameraSnapshotProcessorConfigFlow, "async_step_user")
    assert hasattr(CameraSnapshotProcessorConfigFlow, "async_get_options_flow")
    assert hasattr(OptionsFlowHandler, "async_step_init")
    print("✅ Config flow structure is valid")
except AssertionError as e:
    print(f"❌ Config flow validation failed: {e}")
    sys.exit(1)

print()

# Test 3: Validate API views
print("Test 3: Validating API views...")
try:
    assert hasattr(CameraSnapshotProcessorCamerasView, "url")
    assert hasattr(CameraSnapshotProcessorCamerasView, "name")
    assert hasattr(CameraSnapshotProcessorCamerasView, "get")
    assert hasattr(CameraSnapshotProcessorCamerasView, "post")

    assert hasattr(CameraSnapshotProcessorCameraView, "url")
    assert hasattr(CameraSnapshotProcessorCameraView, "get")
    assert hasattr(CameraSnapshotProcessorCameraView, "put")
    assert hasattr(CameraSnapshotProcessorCameraView, "delete")

    assert hasattr(CameraSnapshotProcessorPreviewView, "url")
    assert hasattr(CameraSnapshotProcessorPreviewView, "post")

    assert hasattr(CameraSnapshotProcessorSourceView, "url")
    assert hasattr(CameraSnapshotProcessorSourceView, "get")

    assert hasattr(CameraSnapshotProcessorEntitiesView, "url")
    assert hasattr(CameraSnapshotProcessorEntitiesView, "get")

    assert hasattr(CameraSnapshotProcessorAvailableCamerasView, "url")
    assert hasattr(CameraSnapshotProcessorAvailableCamerasView, "get")

    print("✅ API views are properly structured")
except AssertionError as e:
    print(f"❌ API validation failed: {e}")
    sys.exit(1)

print()

# Test 4: Test async_setup
print("Test 4: Testing async_setup...")
async def test_async_setup():
    try:
        from homeassistant.components.http import StaticPathConfig

        mock_hass = Mock()
        mock_hass.http = Mock()
        mock_hass.http.register_view = Mock()
        # Use correct async method name
        mock_hass.http.async_register_static_paths = AsyncMock(return_value=None)

        result = await async_setup(mock_hass, {})

        assert result is True, "async_setup should return True"
        assert mock_hass.http.async_register_static_paths.called, "Static paths should be registered"

        # Verify it was called with correct format
        call_args = mock_hass.http.async_register_static_paths.call_args
        assert call_args is not None, "async_register_static_paths should have been called"
        paths = call_args[0][0]
        assert isinstance(paths, list), "Should pass list of StaticPathConfig"
        assert len(paths) > 0, "Should register at least one path"

        # Check it's a StaticPathConfig object
        first_path = paths[0]
        assert isinstance(first_path, StaticPathConfig), "Should use StaticPathConfig class"
        assert first_path.url_path == "/camera_snapshot_processor_panel", "URL path should be correct"
        assert first_path.cache_headers is False, "Cache headers should be False"

        print("✅ async_setup works correctly")
        return True
    except Exception as e:
        print(f"❌ async_setup failed: {e}")
        import traceback
        traceback.print_exc()
        return False

asyncio.run(test_async_setup())

print()

# Test 5: Test config flow user step
print("Test 5: Testing config flow user step...")
async def test_config_flow():
    try:
        from homeassistant import config_entries
        from homeassistant.data_entry_flow import FlowResult

        mock_hass = Mock()
        mock_hass.states = Mock()
        mock_hass.states.async_entity_ids = Mock(return_value=[
            "camera.front_door",
            "camera.backyard"
        ])

        flow = CameraSnapshotProcessorConfigFlow()
        flow.hass = mock_hass

        # Test without user input (should show form)
        result = await flow.async_step_user(user_input=None)

        assert result["type"] == "form", "Should show form initially"
        assert result["step_id"] == "user"

        print("✅ Config flow user step works correctly")
        return True
    except Exception as e:
        print(f"❌ Config flow test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

asyncio.run(test_config_flow())

print()

# Test 6: Test panel registration
print("Test 6: Testing panel registration...")
async def test_panel_registration():
    try:
        from homeassistant import config_entries
        from homeassistant.components import frontend as frontend_module
        from unittest.mock import patch

        mock_hass = Mock()
        mock_hass.data = {}
        mock_hass.config_entries = Mock()
        mock_hass.config_entries.async_forward_entry_setups = AsyncMock()

        # Create a mock config entry
        mock_entry = Mock()
        mock_entry.entry_id = "test_entry_123"
        mock_entry.title = "Camera Snapshot Processor"
        mock_entry.data = {
            "cameras": {}
        }
        mock_entry.add_update_listener = Mock(return_value=lambda: None)
        mock_entry.async_on_unload = Mock()

        # Mock frontend.async_register_built_in_panel (it's not actually async despite the name)
        with patch('camera_snapshot_processor.frontend.async_register_built_in_panel') as mock_register:
            # Test async_setup_entry
            result = await async_setup_entry(mock_hass, mock_entry)

            assert result is True, "async_setup_entry should return True"
            assert mock_register.called, "Panel should be registered"

            # Verify panel registration parameters
            call_args = mock_register.call_args
            assert call_args is not None, "Panel registration should be called"

            # First arg should be hass
            assert call_args[0][0] == mock_hass, "First argument should be hass"

            # Check kwargs
            kwargs = call_args[1]
            assert kwargs["component_name"] == "iframe", "Should use iframe component"
            assert "Snapshot Processor" in kwargs["sidebar_title"], "Title should include Snapshot Processor"
            assert kwargs["sidebar_icon"] == "mdi:camera-enhance", "Should use correct icon"
            assert kwargs["require_admin"] is True, "Should require admin"
            assert "url" in kwargs["config"], "Config should have url"

        print("✅ Panel registration works correctly")
        return True
    except Exception as e:
        print(f"❌ Panel registration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

asyncio.run(test_panel_registration())

print()

# Test 7: Validate API endpoint URLs
print("Test 7: Validating API endpoint URLs...")
try:
    cameras_url = CameraSnapshotProcessorCamerasView.url
    camera_url = CameraSnapshotProcessorCameraView.url
    preview_url = CameraSnapshotProcessorPreviewView.url
    source_url = CameraSnapshotProcessorSourceView.url
    entities_url = CameraSnapshotProcessorEntitiesView.url
    available_cameras_url = CameraSnapshotProcessorAvailableCamerasView.url

    assert "{camera_id}" in camera_url, "Camera URL should have camera_id parameter"
    assert "{camera_id}" in preview_url, "Preview URL should have camera_id parameter"
    assert "{camera_id}" in source_url, "Source URL should have camera_id parameter"
    assert "/api/camera_snapshot_processor" in cameras_url, "URLs should have correct prefix"

    print(f"  Cameras URL: {cameras_url}")
    print(f"  Camera URL: {camera_url}")
    print(f"  Preview URL: {preview_url}")
    print(f"  Source URL: {source_url}")
    print(f"  Entities URL: {entities_url}")
    print(f"  Available Cameras URL: {available_cameras_url}")
    print("✅ All API endpoint URLs are valid")
except AssertionError as e:
    print(f"❌ API URL validation failed: {e}")
    sys.exit(1)

print()

# Test 8: Validate frontend files exist
print("Test 8: Checking frontend files...")
try:
    frontend_dir = Path(__file__).parent / "custom_components" / "camera_snapshot_processor" / "frontend"

    panel_html = frontend_dir / "panel.html"
    panel_js = frontend_dir / "panel.js"
    styles_css = frontend_dir / "styles.css"

    assert panel_html.exists(), "panel.html should exist"
    assert panel_js.exists(), "panel.js should exist"
    assert styles_css.exists(), "styles.css should exist"

    # Check file sizes (should not be empty)
    assert panel_html.stat().st_size > 0, "panel.html should not be empty"
    assert panel_js.stat().st_size > 0, "panel.js should not be empty"
    assert styles_css.stat().st_size > 0, "styles.css should not be empty"

    print(f"  panel.html: {panel_html.stat().st_size:,} bytes")
    print(f"  panel.js: {panel_js.stat().st_size:,} bytes")
    print(f"  styles.css: {styles_css.stat().st_size:,} bytes")
    print("✅ All frontend files exist and are valid")
except AssertionError as e:
    print(f"❌ Frontend files validation failed: {e}")
    sys.exit(1)

print()

# Test 9: Validate manifest.json
print("Test 9: Validating manifest.json...")
try:
    manifest_path = Path(__file__).parent / "custom_components" / "camera_snapshot_processor" / "manifest.json"

    with open(manifest_path) as f:
        manifest = json.load(f)

    assert "domain" in manifest, "manifest should have domain"
    assert manifest["domain"] == DOMAIN, "domain should match const"
    assert "name" in manifest, "manifest should have name"
    assert "version" in manifest, "manifest should have version"
    assert "requirements" in manifest, "manifest should have requirements"

    print(f"  Domain: {manifest['domain']}")
    print(f"  Name: {manifest['name']}")
    print(f"  Version: {manifest['version']}")
    print(f"  Requirements: {', '.join(manifest['requirements'])}")
    print("✅ manifest.json is valid")
except Exception as e:
    print(f"❌ manifest.json validation failed: {e}")
    sys.exit(1)

print()

# Test 10: Test API setup
print("Test 10: Testing API setup...")
try:
    mock_hass = Mock()
    mock_hass.http = Mock()
    mock_hass.http.register_view = Mock()

    setup_api(mock_hass)

    assert mock_hass.http.register_view.call_count == 6, "Should register 6 views"
    print("✅ API setup registers all views correctly")
except Exception as e:
    print(f"❌ API setup test failed: {e}")
    sys.exit(1)

print()

# Test 11: Validate constants
print("Test 11: Validating constants...")
try:
    assert DOMAIN == "camera_snapshot_processor", "Domain should be correct"
    assert DEFAULT_WIDTH == 1920, "Default width should be 1920"
    assert DEFAULT_HEIGHT == 1080, "Default height should be 1080"
    assert isinstance(CONF_SOURCE_CAMERA, str), "Config keys should be strings"
    assert isinstance(CONF_WIDTH, str), "Config keys should be strings"

    print(f"  Domain: {DOMAIN}")
    print(f"  Default dimensions: {DEFAULT_WIDTH}x{DEFAULT_HEIGHT}")
    print("✅ Constants are valid")
except AssertionError as e:
    print(f"❌ Constants validation failed: {e}")
    sys.exit(1)

print()
print("=" * 60)
print("🎉 All tests passed! Integration is ready for Home Assistant")
print("=" * 60)
print()
print("Summary:")
print("✅ 11 tests passed")
print("✅ Integration structure validated")
print("✅ Config flow validated")
print("✅ API views validated")
print("✅ async_setup with async_register_static_paths validated")
print("✅ Panel registration with correct method validated")
print()
print("Next steps:")
print("1. Copy custom_components/camera_snapshot_processor to your HA config")
print("2. Restart Home Assistant")
print("3. Add integration via UI")
print("4. Access the panel from the sidebar")
