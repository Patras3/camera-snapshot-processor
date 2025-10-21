"""API endpoints for Camera Snapshot Processor configuration panel."""

from __future__ import annotations

import io
import logging
import uuid

from aiohttp import web
from homeassistant.components.http import HomeAssistantView
from homeassistant.core import HomeAssistant

from .const import (
    CONF_ENTITY_NAME,
    CONF_HEIGHT,
    CONF_KEEP_RATIO,
    CONF_QUALITY,
    CONF_SOURCE_CAMERA,
    CONF_SOURCE_HEIGHT,
    CONF_SOURCE_WIDTH,
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

            # Enrich camera configs with actual entity IDs from HA registry
            from homeassistant.helpers import entity_registry as er

            entity_registry = er.async_get(self.hass)

            enriched_cameras = {}
            for camera_id, config in cameras.items():
                enriched_config = dict(config)

                # Get actual entity ID from HA registry
                unique_id = f"{DOMAIN}_{camera_id}"
                entity_id = entity_registry.async_get_entity_id(
                    "camera", DOMAIN, unique_id
                )

                if entity_id:
                    # Extract the object_id (part after camera.)
                    actual_entity_name = entity_id.replace("camera.", "")
                    enriched_config["actual_entity_id"] = entity_id
                    enriched_config["actual_entity_name"] = actual_entity_name

                enriched_cameras[camera_id] = enriched_config

            return web.json_response({"success": True, "cameras": enriched_cameras})

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

            # Get existing cameras (allow duplicates for multi-processing same source)
            cameras = dict(entry.data.get("cameras", {}))

            # Get camera entity to fetch source dimensions
            camera_entity = self._get_camera_entity(source_camera)
            if not camera_entity:
                return web.json_response(
                    {"error": f"Camera entity not found: {source_camera}"}, status=404
                )

            # Fetch source image to get dimensions
            try:
                from PIL import Image

                source_image = await camera_entity.async_camera_image()
                if not source_image:
                    return web.json_response(
                        {"error": f"Could not get image from camera: {source_camera}"},
                        status=500,
                    )

                img = Image.open(io.BytesIO(source_image))
                source_width, source_height = img.size

                _LOGGER.info(
                    "Adding camera %s with source dimensions: %dx%d",
                    source_camera,
                    source_width,
                    source_height,
                )

                # Set smart defaults: min(source_size, 1920x1080) to prevent upscaling
                default_width = min(source_width, DEFAULT_WIDTH)
                default_height = min(source_height, DEFAULT_HEIGHT)

            except Exception as err:
                _LOGGER.warning(
                    "Could not fetch source dimensions for %s: %s. Using fallback defaults.",
                    source_camera,
                    err,
                )
                # Fallback to static defaults if we can't get source dimensions
                source_width = DEFAULT_WIDTH
                source_height = DEFAULT_HEIGHT
                default_width = DEFAULT_WIDTH
                default_height = DEFAULT_HEIGHT

            # Generate unique entity name if same source camera is used multiple times
            source_name = source_camera.replace("camera.", "")
            base_entity_name = f"{source_name}_processed"

            # Count existing cameras with the same source
            same_source_count = sum(
                1 for cam_config in cameras.values()
                if cam_config.get(CONF_SOURCE_CAMERA) == source_camera
            )

            # If this is a duplicate source, add suffix (_2, _3, etc.)
            if same_source_count > 0:
                entity_name = f"{base_entity_name}_{same_source_count + 1}"
                _LOGGER.info(
                    "Multiple cameras from same source %s detected. Using entity name: %s",
                    source_camera,
                    entity_name,
                )
            else:
                entity_name = base_entity_name

            # Create new camera with smart default config
            camera_id = str(uuid.uuid4())
            cameras[camera_id] = {
                CONF_SOURCE_CAMERA: source_camera,
                CONF_SOURCE_WIDTH: source_width,
                CONF_SOURCE_HEIGHT: source_height,
                CONF_WIDTH: default_width,
                CONF_HEIGHT: default_height,
                CONF_KEEP_RATIO: DEFAULT_KEEP_RATIO,
                CONF_QUALITY: DEFAULT_QUALITY,
                CONF_STATE_ICONS: [],
                CONF_ENTITY_NAME: entity_name,  # Set custom entity name for duplicates
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

    def _get_camera_entity(self, entity_id: str):
        """Get camera entity from entity_id."""
        component = self.hass.data.get("camera")
        if not component:
            return None

        for entity in component.entities:
            if entity.entity_id == entity_id:
                return entity
        return None


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

            # Check for duplicate entity ID if entity_name is being changed
            from homeassistant.helpers import entity_registry as er

            from .const import CONF_ENTITY_NAME

            if CONF_ENTITY_NAME in new_config and new_config[CONF_ENTITY_NAME]:
                entity_name = new_config[CONF_ENTITY_NAME]
                desired_entity_id = f"camera.{entity_name}"

                # Get entity registry
                entity_registry = er.async_get(self.hass)

                # Check if entity ID already exists
                existing_entry = entity_registry.async_get(desired_entity_id)
                if existing_entry:
                    # Get our unique_id to check if it's our own entity
                    our_unique_id = f"{DOMAIN}_{camera_id}"

                    if existing_entry.unique_id != our_unique_id:
                        # Entity ID exists and belongs to a different entity
                        error_msg = (
                            f"Entity ID '{desired_entity_id}' already exists. "
                            "Please choose a different name."
                        )
                        return web.json_response(
                            {
                                "success": False,
                                "error": error_msg,
                            },
                            status=400,
                        )

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
