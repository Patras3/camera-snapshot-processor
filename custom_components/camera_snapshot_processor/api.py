"""API endpoints for Camera Snapshot Processor configuration panel."""

from __future__ import annotations

import io
import logging
import uuid

from aiohttp import web
from homeassistant.components.http import HomeAssistantView
from homeassistant.core import HomeAssistant

from .const import (
    CONF_HEIGHT,
    CONF_KEEP_RATIO,
    CONF_QUALITY,
    CONF_SOURCE_CAMERA,
    CONF_STATE_ICONS,
    CONF_WIDTH,
    DEFAULT_HEIGHT,
    DEFAULT_KEEP_RATIO,
    DEFAULT_QUALITY,
    DEFAULT_WIDTH,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


class CameraSnapshotProcessorCamerasView(HomeAssistantView):
    """Handle cameras list GET/POST requests."""

    url = "/api/camera_snapshot_processor/cameras"
    name = "api:camera_snapshot_processor:cameras"
    requires_auth = True

    def __init__(self, hass: HomeAssistant) -> None:
        """Initialize the view."""
        self.hass = hass

    async def get(self, request: web.Request) -> web.Response:
        """Get all configured cameras."""
        try:
            entry = self._get_entry()
            if not entry:
                return web.json_response(
                    {"error": "Integration not configured"}, status=404
                )

            cameras = entry.data.get("cameras", {})
            return web.json_response({"success": True, "cameras": cameras})

        except Exception as err:
            _LOGGER.error("Error getting cameras: %s", err, exc_info=True)
            return web.json_response({"error": str(err)}, status=500)

    async def post(self, request: web.Request) -> web.Response:
        """Add a new camera."""
        try:
            entry = self._get_entry()
            if not entry:
                return web.json_response(
                    {"error": "Integration not configured"}, status=404
                )

            data = await request.json()
            source_camera = data.get("source_camera")

            if not source_camera:
                return web.json_response(
                    {"error": "source_camera is required"}, status=400
                )

            # Check if camera already exists
            cameras = dict(entry.data.get("cameras", {}))
            for cam_id, cam_config in cameras.items():
                if cam_config.get(CONF_SOURCE_CAMERA) == source_camera:
                    return web.json_response(
                        {"error": "Camera already configured"}, status=400
                    )

            # Create new camera with default config
            camera_id = str(uuid.uuid4())
            cameras[camera_id] = {
                CONF_SOURCE_CAMERA: source_camera,
                CONF_WIDTH: DEFAULT_WIDTH,
                CONF_HEIGHT: DEFAULT_HEIGHT,
                CONF_KEEP_RATIO: DEFAULT_KEEP_RATIO,
                CONF_QUALITY: DEFAULT_QUALITY,
                CONF_STATE_ICONS: [],
            }

            # Update entry
            self.hass.config_entries.async_update_entry(
                entry, data={"cameras": cameras}
            )

            return web.json_response(
                {
                    "success": True,
                    "camera_id": camera_id,
                    "message": "Camera added successfully",
                }
            )

        except Exception as err:
            _LOGGER.error("Error adding camera: %s", err, exc_info=True)
            return web.json_response({"error": str(err)}, status=500)

    def _get_entry(self):
        """Get the integration entry."""
        entries = self.hass.config_entries.async_entries(DOMAIN)
        return entries[0] if entries else None


class CameraSnapshotProcessorCameraView(HomeAssistantView):
    """Handle single camera GET/PUT/DELETE requests."""

    url = "/api/camera_snapshot_processor/cameras/{camera_id}"
    name = "api:camera_snapshot_processor:camera"
    requires_auth = True

    def __init__(self, hass: HomeAssistant) -> None:
        """Initialize the view."""
        self.hass = hass

    async def get(self, request: web.Request, camera_id: str) -> web.Response:
        """Get camera configuration."""
        try:
            entry = self._get_entry()
            if not entry:
                return web.json_response(
                    {"error": "Integration not configured"}, status=404
                )

            cameras = entry.data.get("cameras", {})
            if camera_id not in cameras:
                return web.json_response({"error": "Camera not found"}, status=404)

            return web.json_response({"success": True, "config": cameras[camera_id]})

        except Exception as err:
            _LOGGER.error("Error getting camera config: %s", err, exc_info=True)
            return web.json_response({"error": str(err)}, status=500)

    async def put(self, request: web.Request, camera_id: str) -> web.Response:
        """Update camera configuration."""
        try:
            entry = self._get_entry()
            if not entry:
                return web.json_response(
                    {"error": "Integration not configured"}, status=404
                )

            cameras = dict(entry.data.get("cameras", {}))
            if camera_id not in cameras:
                return web.json_response({"error": "Camera not found"}, status=404)

            data = await request.json()
            new_config = data.get("config", {})

            # Preserve source camera
            new_config[CONF_SOURCE_CAMERA] = cameras[camera_id][CONF_SOURCE_CAMERA]

            # Log state icons config for debugging
            state_icons = new_config.get(CONF_STATE_ICONS, [])
            if state_icons:
                _LOGGER.debug(
                    "Saving camera %s with %d state icon(s)",
                    camera_id,
                    len(state_icons),
                )
                for idx, icon_config in enumerate(state_icons):
                    rules = icon_config.get("state_rules", [])
                    _LOGGER.debug(
                        "  State icon %d: entity=%s, rules=%d",
                        idx,
                        icon_config.get("entity"),
                        len(rules),
                    )
                    for rule_idx, rule in enumerate(rules):
                        _LOGGER.debug(
                            "    Rule %d: condition=%s, value=%s, icon=%s, default=%s",
                            rule_idx,
                            rule.get("condition"),
                            rule.get("value"),
                            rule.get("icon", "")[
                                :20
                            ],  # Truncate icon to avoid log spam
                            rule.get("is_default", False),
                        )

            # Update camera config
            cameras[camera_id] = new_config

            # Update entry - this should trigger the update listener
            self.hass.config_entries.async_update_entry(
                entry, data={"cameras": cameras}
            )

            _LOGGER.info(
                "Camera configuration saved for %s, config entry will reload",
                camera_id,
            )

            return web.json_response(
                {"success": True, "message": "Configuration saved successfully"}
            )

        except Exception as err:
            _LOGGER.error("Error saving camera config: %s", err, exc_info=True)
            return web.json_response({"error": str(err)}, status=500)

    async def delete(self, request: web.Request, camera_id: str) -> web.Response:
        """Delete camera."""
        try:
            entry = self._get_entry()
            if not entry:
                return web.json_response(
                    {"error": "Integration not configured"}, status=404
                )

            cameras = dict(entry.data.get("cameras", {}))
            if camera_id not in cameras:
                return web.json_response({"error": "Camera not found"}, status=404)

            # Remove camera
            del cameras[camera_id]

            # Update entry
            self.hass.config_entries.async_update_entry(
                entry, data={"cameras": cameras}
            )

            return web.json_response(
                {"success": True, "message": "Camera removed successfully"}
            )

        except Exception as err:
            _LOGGER.error("Error deleting camera: %s", err, exc_info=True)
            return web.json_response({"error": str(err)}, status=500)

    def _get_entry(self):
        """Get the integration entry."""
        entries = self.hass.config_entries.async_entries(DOMAIN)
        return entries[0] if entries else None


class CameraSnapshotProcessorPreviewView(HomeAssistantView):
    """Handle preview generation requests."""

    url = "/api/camera_snapshot_processor/cameras/{camera_id}/preview"
    name = "api:camera_snapshot_processor:preview"
    requires_auth = True

    def __init__(self, hass: HomeAssistant) -> None:
        """Initialize the view."""
        self.hass = hass

    async def post(self, request: web.Request, camera_id: str) -> web.Response:
        """Generate a preview with given configuration."""
        try:
            entry = self._get_entry()
            if not entry:
                return web.json_response(
                    {"error": "Integration not configured"}, status=404
                )

            cameras = entry.data.get("cameras", {})
            if camera_id not in cameras:
                return web.json_response({"error": "Camera not found"}, status=404)

            # Parse the request body (optional override config)
            data = await request.json()
            config = data.get("config", cameras[camera_id])

            # Get source camera
            source_camera = config.get(CONF_SOURCE_CAMERA)
            if not source_camera:
                return web.json_response(
                    {"error": "No source camera configured"}, status=400
                )

            # Get camera entity
            camera_entity = self._get_camera_entity(source_camera)
            if not camera_entity:
                return web.json_response(
                    {"error": f"Camera entity not found: {source_camera}"}, status=404
                )

            # Get original image
            original_image = await camera_entity.async_camera_image()
            if not original_image:
                return web.json_response(
                    {"error": f"Could not get image from camera: {source_camera}"},
                    status=500,
                )

            # Process image with provided config
            from .image_processor import ImageProcessor

            processor = ImageProcessor(self.hass, config)
            processed_image = await processor.process_image(original_image)

            # Return the processed image
            return web.Response(
                body=processed_image,
                content_type="image/jpeg",
                headers={
                    "Cache-Control": "no-cache, no-store, must-revalidate",
                    "Pragma": "no-cache",
                    "Expires": "0",
                },
            )

        except Exception as err:
            _LOGGER.error("Error generating preview: %s", err, exc_info=True)
            return web.json_response({"error": str(err)}, status=500)

    def _get_entry(self):
        """Get the integration entry."""
        entries = self.hass.config_entries.async_entries(DOMAIN)
        return entries[0] if entries else None

    def _get_camera_entity(self, entity_id: str):
        """Get camera entity from entity_id."""
        component = self.hass.data.get("camera")
        if not component:
            return None

        for entity in component.entities:
            if entity.entity_id == entity_id:
                return entity
        return None


class CameraSnapshotProcessorSourceView(HomeAssistantView):
    """Handle source image requests."""

    url = "/api/camera_snapshot_processor/cameras/{camera_id}/source"
    name = "api:camera_snapshot_processor:source"
    requires_auth = True

    def __init__(self, hass: HomeAssistant) -> None:
        """Initialize the view."""
        self.hass = hass

    async def get(self, request: web.Request, camera_id: str) -> web.Response:
        """Get source camera image."""
        try:
            entry = self._get_entry()
            if not entry:
                return web.json_response(
                    {"error": "Integration not configured"}, status=404
                )

            cameras = entry.data.get("cameras", {})
            if camera_id not in cameras:
                return web.json_response({"error": "Camera not found"}, status=404)

            # Get source camera
            source_camera = cameras[camera_id].get(CONF_SOURCE_CAMERA)
            if not source_camera:
                return web.json_response(
                    {"error": "No source camera configured"}, status=400
                )

            # Get camera entity
            camera_entity = self._get_camera_entity(source_camera)
            if not camera_entity:
                return web.json_response(
                    {"error": f"Camera entity not found: {source_camera}"}, status=404
                )

            # Get original image
            original_image = await camera_entity.async_camera_image()
            if not original_image:
                return web.json_response(
                    {"error": f"Could not get image from camera: {source_camera}"},
                    status=500,
                )

            # Get image dimensions
            from PIL import Image

            img = Image.open(io.BytesIO(original_image))
            width, height = img.size

            # Return the original image with dimensions in headers
            return web.Response(
                body=original_image,
                content_type="image/jpeg",
                headers={
                    "X-Image-Width": str(width),
                    "X-Image-Height": str(height),
                    "Cache-Control": "no-cache, no-store, must-revalidate",
                    "Pragma": "no-cache",
                    "Expires": "0",
                },
            )

        except Exception as err:
            _LOGGER.error("Error getting source image: %s", err, exc_info=True)
            return web.json_response({"error": str(err)}, status=500)

    def _get_entry(self):
        """Get the integration entry."""
        entries = self.hass.config_entries.async_entries(DOMAIN)
        return entries[0] if entries else None

    def _get_camera_entity(self, entity_id: str):
        """Get camera entity from entity_id."""
        component = self.hass.data.get("camera")
        if not component:
            return None

        for entity in component.entities:
            if entity.entity_id == entity_id:
                return entity
        return None


class CameraSnapshotProcessorEntitiesView(HomeAssistantView):
    """Handle entity list requests."""

    url = "/api/camera_snapshot_processor/entities"
    name = "api:camera_snapshot_processor:entities"
    requires_auth = True

    def __init__(self, hass: HomeAssistant) -> None:
        """Initialize the view."""
        self.hass = hass

    async def get(self, request: web.Request) -> web.Response:
        """Get all entities (for state icon configuration)."""
        try:
            # Get all states
            entities = []
            for state in self.hass.states.async_all():
                entities.append(
                    {
                        "entity_id": state.entity_id,
                        "name": state.name or state.entity_id,
                        "state": state.state,
                        "domain": state.domain,
                    }
                )

            return web.json_response({"success": True, "entities": entities})

        except Exception as err:
            _LOGGER.error("Error getting entities: %s", err, exc_info=True)
            return web.json_response({"error": str(err)}, status=500)


class CameraSnapshotProcessorAvailableCamerasView(HomeAssistantView):
    """Handle available camera entities list requests."""

    url = "/api/camera_snapshot_processor/available_cameras"
    name = "api:camera_snapshot_processor:available_cameras"
    requires_auth = True

    def __init__(self, hass: HomeAssistant) -> None:
        """Initialize the view."""
        self.hass = hass

    async def get(self, request: web.Request) -> web.Response:
        """Get all available camera entities."""
        try:
            from homeassistant.components.camera import DOMAIN as CAMERA_DOMAIN

            camera_entities = []
            for entity_id in self.hass.states.async_entity_ids(CAMERA_DOMAIN):
                # Skip our own processed cameras
                if not entity_id.startswith(f"{CAMERA_DOMAIN}.{DOMAIN}"):
                    state = self.hass.states.get(entity_id)
                    if state:
                        camera_entities.append(
                            {
                                "entity_id": entity_id,
                                "name": state.name or entity_id,
                            }
                        )

            return web.json_response({"success": True, "cameras": camera_entities})

        except Exception as err:
            _LOGGER.error("Error getting available cameras: %s", err, exc_info=True)
            return web.json_response({"error": str(err)}, status=500)


def setup_api(hass: HomeAssistant) -> None:
    """Set up the API views."""
    hass.http.register_view(CameraSnapshotProcessorCamerasView(hass))
    hass.http.register_view(CameraSnapshotProcessorCameraView(hass))
    hass.http.register_view(CameraSnapshotProcessorPreviewView(hass))
    hass.http.register_view(CameraSnapshotProcessorSourceView(hass))
    hass.http.register_view(CameraSnapshotProcessorEntitiesView(hass))
    hass.http.register_view(CameraSnapshotProcessorAvailableCamerasView(hass))
    _LOGGER.info("Camera Snapshot Processor API endpoints registered")
