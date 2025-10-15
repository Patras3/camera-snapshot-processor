"""Camera platform for Camera Snapshot Processor."""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Any

from homeassistant.components.camera import Camera, CameraEntityFeature
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import CONF_ENTITY_NAME, CONF_RTSP_URL, CONF_SOURCE_CAMERA, DOMAIN
from .image_processor import ImageProcessor

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Camera Snapshot Processor cameras from a config entry."""
    from homeassistant.helpers import entity_registry as er

    # Get all configured cameras
    cameras_config = config_entry.data.get("cameras", {})

    # Get entity registry
    entity_registry = er.async_get(hass)

    # Get all existing camera entities for this integration
    existing_entities = er.async_entries_for_config_entry(
        entity_registry, config_entry.entry_id
    )

    # Build set of current camera IDs that should exist
    current_camera_ids = set()
    for camera_id in cameras_config.keys():
        current_camera_ids.add(f"{DOMAIN}_{camera_id}")

    # Remove entities that are no longer in config
    for entity_entry in existing_entities:
        if entity_entry.unique_id not in current_camera_ids:
            _LOGGER.info(
                "Removing orphaned camera entity: %s (unique_id: %s)",
                entity_entry.entity_id,
                entity_entry.unique_id,
            )
            entity_registry.async_remove(entity_entry.entity_id)

    # Create camera entities for all configured cameras
    cameras = []
    for camera_id, config in cameras_config.items():
        camera = SnapshotProcessorCamera(hass, config_entry, camera_id, config)
        cameras.append(camera)

    async_add_entities(cameras)


class SnapshotProcessorCamera(Camera):
    """Representation of a Camera Snapshot Processor camera."""

    _attr_has_entity_name = False  # We manage the full entity name ourselves

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        camera_id: str,
        config: dict[str, Any],
    ) -> None:
        """Initialize the camera."""
        super().__init__()

        self.hass = hass
        self._config_entry = config_entry
        self._camera_id = camera_id
        self._config = config
        self._source_camera = config[CONF_SOURCE_CAMERA]
        # Only use RTSP URL if it's not empty
        rtsp_url = config.get(CONF_RTSP_URL, "")
        self._rtsp_url = rtsp_url.strip() if rtsp_url else None
        self._image_processor = ImageProcessor(hass, config)

        # Performance optimization: request deduplication
        self._render_lock = asyncio.Lock()
        self._pending_render: asyncio.Future[bytes | None] | None = None
        self._last_render_time = 0.0
        self._render_count = 0
        self._concurrent_requests = 0

        # Generate unique ID and entity name
        # If entity_name is provided, use it; otherwise generate from source camera
        if CONF_ENTITY_NAME in config and config[CONF_ENTITY_NAME]:
            entity_name = config[CONF_ENTITY_NAME]
        else:
            # Default: source_name_processed
            source_name = self._source_camera.replace("camera.", "")
            entity_name = f"{source_name}_processed"

        self._attr_unique_id = f"{DOMAIN}_{camera_id}"
        self._attr_name = entity_name  # Name without camera. prefix

        self._attr_device_info = {
            "identifiers": {(DOMAIN, self._attr_unique_id)},
            "name": f"{entity_name.replace('_', ' ').title()}",
            "manufacturer": "Camera Snapshot Processor",
            "model": "Processed Camera",
        }

        # Enable streaming if RTSP URL is provided or source camera has stream
        self._attr_supported_features = CameraEntityFeature.STREAM

    @callback
    def _handle_config_update(self) -> None:
        """Handle config updates."""
        # Get updated config from entry
        cameras_config = self._config_entry.data.get("cameras", {})
        if self._camera_id in cameras_config:
            self._config = cameras_config[self._camera_id]
            self._source_camera = self._config[CONF_SOURCE_CAMERA]
            rtsp_url = self._config.get(CONF_RTSP_URL, "")
            self._rtsp_url = rtsp_url.strip() if rtsp_url else None
            self._image_processor = ImageProcessor(self.hass, self._config)

            # Update entity name if changed
            if CONF_ENTITY_NAME in self._config and self._config[CONF_ENTITY_NAME]:
                new_name = self._config[CONF_ENTITY_NAME]
            else:
                # Default: source_name_processed
                source_name = self._source_camera.replace("camera.", "")
                new_name = f"{source_name}_processed"

            if self._attr_name != new_name:
                self._attr_name = new_name
                _LOGGER.info(
                    "Camera %s: Entity name updated to %s",
                    self._camera_id,
                    new_name,
                )

            self.async_write_ha_state()

    async def async_added_to_hass(self) -> None:
        """Run when entity is added to hass."""
        await super().async_added_to_hass()

        # Copy content type from source camera
        source_camera_entity = self._get_source_camera_entity()
        if source_camera_entity:
            self.content_type = source_camera_entity.content_type
            _LOGGER.debug(
                "Using content type from source camera: %s", self.content_type
            )

        # Listen for config updates
        self.async_on_remove(
            self._config_entry.add_update_listener(self._async_update_listener)
        )

    async def _async_update_listener(
        self, hass: HomeAssistant, entry: ConfigEntry
    ) -> None:
        """Handle config update."""
        self._handle_config_update()

    @property
    def available(self) -> bool:
        """Return if camera is available."""
        source_camera = self.hass.states.get(self._source_camera)
        return source_camera is not None and source_camera.state != "unavailable"

    @property
    def is_streaming(self) -> bool:
        """Forward streaming state from source camera."""
        source_camera_entity = self._get_source_camera_entity()
        return source_camera_entity.is_streaming if source_camera_entity else False

    @property
    def is_recording(self) -> bool:
        """Forward recording state from source camera."""
        source_camera_entity = self._get_source_camera_entity()
        return source_camera_entity.is_recording if source_camera_entity else False

    async def async_camera_image(
        self, width: int | None = None, height: int | None = None
    ) -> bytes | None:
        """Return processed camera image with request deduplication."""
        start_time = time.time()

        # Check if a render is already in progress
        if self._pending_render is not None and not self._pending_render.done():
            # Another render is in progress - wait for it instead of starting a new one
            self._concurrent_requests += 1
            _LOGGER.debug(
                "Camera %s: Render in progress, waiting (concurrent=%d)",
                self._camera_id,
                self._concurrent_requests,
            )
            try:
                result = await self._pending_render
                wait_time = (time.time() - start_time) * 1000
                _LOGGER.debug(
                    "Camera %s: Got deduplicated result in %.1fms",
                    self._camera_id,
                    wait_time,
                )
                return result
            finally:
                self._concurrent_requests -= 1

        # No render in progress - we'll start one
        async with self._render_lock:
            # Double-check: another task might have started a render while we waited for the lock
            if self._pending_render is not None and not self._pending_render.done():
                self._concurrent_requests += 1
                try:
                    result = await self._pending_render
                    wait_time = (time.time() - start_time) * 1000
                    _LOGGER.debug(
                        "Camera %s: Got deduplicated result in %.1fms (after lock)",
                        self._camera_id,
                        wait_time,
                    )
                    return result
                finally:
                    self._concurrent_requests -= 1

            # Create a new future for this render
            self._pending_render = asyncio.get_event_loop().create_future()

            try:
                # Perform the actual rendering
                result = await self._render_image()

                # Log performance metrics
                render_time = (time.time() - start_time) * 1000
                self._render_count += 1
                self._last_render_time = time.time()

                saved_requests = self._concurrent_requests
                if saved_requests > 0:
                    _LOGGER.debug(
                        "Camera %s: Rendered in %.1fms (served %d concurrent requests)",
                        self._camera_id,
                        render_time,
                        saved_requests + 1,
                    )
                else:
                    _LOGGER.debug(
                        "Camera %s: Rendered in %.1fms",
                        self._camera_id,
                        render_time,
                    )

                # Set the result for all waiting tasks
                self._pending_render.set_result(result)
                return result

            except Exception as err:
                _LOGGER.error(
                    "Camera %s: Error rendering image: %s", self._camera_id, err
                )
                # Set exception for all waiting tasks
                self._pending_render.set_exception(err)
                return None
            finally:
                # Clear the pending render after a short delay to allow concurrent requests
                # to pick up the result, but not cache it for too long
                await asyncio.sleep(0.01)
                self._pending_render = None

    async def _render_image(self) -> bytes | None:
        """Perform the actual image rendering (internal method)."""
        try:
            # Get the source camera entity
            source_camera_entity = self._get_source_camera_entity()
            if not source_camera_entity:
                _LOGGER.error("Source camera %s not found", self._source_camera)
                return None

            # Get the original image from source camera
            original_image = await source_camera_entity.async_camera_image()
            if not original_image:
                _LOGGER.error(
                    "Failed to get image from source camera %s", self._source_camera
                )
                return None

            # Process the image (offloaded to thread pool in image_processor)
            processed_image = await self._image_processor.process_image(original_image)
            return processed_image

        except Exception as err:
            _LOGGER.error("Error rendering image: %s", err)
            raise

    async def stream_source(self) -> str | None:
        """Return the stream source."""
        # If RTSP URL is provided, use it
        if self._rtsp_url:
            # Log without credentials for security
            sanitized_url = self._sanitize_url_for_logging(self._rtsp_url)
            _LOGGER.debug("Using custom RTSP URL: %s", sanitized_url)
            return self._rtsp_url

        # Otherwise, try to get stream from source camera
        source_camera_entity = self._get_source_camera_entity()
        if source_camera_entity:
            try:
                stream_url = await source_camera_entity.stream_source()
                if stream_url:
                    _LOGGER.info(
                        "Using stream from source camera %s: %s",
                        self._source_camera,
                        stream_url,
                    )
                else:
                    _LOGGER.warning(
                        "Source camera %s returned empty stream URL",
                        self._source_camera,
                    )
                return stream_url
            except Exception as err:
                _LOGGER.warning(
                    "Source camera %s does not support streaming: %s",
                    self._source_camera,
                    err,
                )

        _LOGGER.warning("No stream source available for camera %s", self._source_camera)
        return None

    def _get_source_camera_entity(self) -> Camera | None:
        """Get the source camera entity."""
        # Get all camera entities
        component = self.hass.data.get("camera")
        if not component:
            return None

        # Find the source camera entity
        for entity in component.entities:
            if entity.entity_id == self._source_camera:
                return entity

        return None

    @staticmethod
    def _sanitize_url_for_logging(url: str) -> str:
        """Remove credentials from URL for safe logging."""
        if not url:
            return url

        try:
            from urllib.parse import urlparse, urlunparse

            parsed = urlparse(url)
            if parsed.username or parsed.password:
                # Rebuild URL with credentials redacted
                sanitized = urlunparse(
                    (
                        parsed.scheme,
                        f"***:***@{parsed.hostname}"
                        + (f":{parsed.port}" if parsed.port else ""),
                        parsed.path,
                        parsed.params,
                        parsed.query,
                        parsed.fragment,
                    )
                )
                return sanitized
        except Exception:
            # Fallback: use simple regex if urlparse fails
            import re

            pattern = r"(rtsp://|rtsps://|http://|https://)([^:]+):([^@]+)@"
            return re.sub(pattern, r"\1***:***@", url)

        return url

    @property
    def brand(self) -> str:
        """Return the camera brand."""
        return "Camera Snapshot Processor"

    @property
    def model(self) -> str:
        """Return the camera model."""
        return "Processed Camera"

    @property
    def frame_interval(self) -> float:
        """Return the interval between frames of the stream."""
        # Forward frame interval from source camera
        source_camera_entity = self._get_source_camera_entity()
        if source_camera_entity:
            return source_camera_entity.frame_interval
        return 1.0  # Fallback to 1.0 second for smooth streaming
