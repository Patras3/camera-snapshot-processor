#!/usr/bin/env python3
"""Performance benchmarking for image processing optimizations.

This script tests the performance improvements from:
1. Request deduplication
2. Thread pool execution
3. Event loop non-blocking behavior
"""

import asyncio
import io
import time
from pathlib import Path
from typing import Any

from PIL import Image


class ImageProcessorOld:
    """Old synchronous blocking implementation."""

    def __init__(self, config: dict[str, Any]):
        self.config = config

    async def process_image(self, image_bytes: bytes) -> bytes:
        """Old implementation - runs synchronously, blocks event loop."""
        # Simulate the old blocking behavior
        image = Image.open(io.BytesIO(image_bytes))
        if image.mode != "RGB":
            image = image.convert("RGB")

        # Resize (blocking operation)
        width = self.config.get("width", 1920)
        height = self.config.get("height", 1080)
        image = image.resize((width, height), Image.Resampling.LANCZOS)

        # Encode (blocking operation)
        output = io.BytesIO()
        image.save(output, format="JPEG", quality=85, optimize=True)
        return output.getvalue()


class ImageProcessorNew:
    """New optimized implementation with thread pool."""

    def __init__(self, config: dict[str, Any]):
        self.config = config

    async def process_image(self, image_bytes: bytes) -> bytes:
        """New implementation - offloads to thread pool."""
        # Offload CPU-intensive operations to thread pool
        image = await asyncio.to_thread(self._decode_and_transform, image_bytes)
        processed_bytes = await asyncio.to_thread(self._encode, image)
        return processed_bytes

    def _decode_and_transform(self, image_bytes: bytes) -> Image.Image:
        """Decode and transform in thread pool."""
        image = Image.open(io.BytesIO(image_bytes))
        if image.mode != "RGB":
            image = image.convert("RGB")

        width = self.config.get("width", 1920)
        height = self.config.get("height", 1080)
        image = image.resize((width, height), Image.Resampling.LANCZOS)
        return image

    def _encode(self, image: Image.Image) -> bytes:
        """Encode in thread pool."""
        output = io.BytesIO()
        image.save(output, format="JPEG", quality=85, optimize=True)
        return output.getvalue()


class CameraOld:
    """Old camera implementation without request deduplication."""

    def __init__(self, image_processor: ImageProcessorOld):
        self._image_processor = image_processor
        self._source_image = None

    async def async_camera_image(self) -> bytes:
        """Old implementation - no deduplication."""
        # Each request triggers a full render
        return await self._image_processor.process_image(self._source_image)


class CameraNew:
    """New camera implementation with request deduplication."""

    def __init__(self, image_processor: ImageProcessorNew):
        self._image_processor = image_processor
        self._source_image = None
        self._render_lock = asyncio.Lock()
        self._pending_render: asyncio.Future[bytes | None] | None = None
        self._concurrent_requests = 0

    async def async_camera_image(self) -> bytes:
        """New implementation - with deduplication."""
        # Check if render is in progress
        if self._pending_render is not None and not self._pending_render.done():
            self._concurrent_requests += 1
            try:
                return await self._pending_render
            finally:
                self._concurrent_requests -= 1

        # Start new render
        async with self._render_lock:
            if self._pending_render is not None and not self._pending_render.done():
                self._concurrent_requests += 1
                try:
                    return await self._pending_render
                finally:
                    self._concurrent_requests -= 1

            self._pending_render = asyncio.get_event_loop().create_future()

            try:
                result = await self._image_processor.process_image(self._source_image)
                self._pending_render.set_result(result)
                return result
            except Exception as err:
                self._pending_render.set_exception(err)
                raise
            finally:
                await asyncio.sleep(0.01)
                self._pending_render = None


def create_test_image(width: int = 2560, height: int = 1440) -> bytes:
    """Create a test image."""
    image = Image.new("RGB", (width, height), color=(100, 150, 200))
    output = io.BytesIO()
    image.save(output, format="JPEG", quality=95)
    return output.getvalue()


async def benchmark_single_request(camera, name: str) -> float:
    """Benchmark single request performance."""
    start = time.time()
    await camera.async_camera_image()
    duration = (time.time() - start) * 1000
    print(f"  {name}: Single request took {duration:.1f}ms")
    return duration


async def benchmark_concurrent_requests(camera, name: str, count: int = 3) -> float:
    """Benchmark concurrent request performance."""
    start = time.time()

    # Launch concurrent requests
    tasks = [camera.async_camera_image() for _ in range(count)]
    await asyncio.gather(*tasks)

    duration = (time.time() - start) * 1000
    print(
        f"  {name}: {count} concurrent requests took {duration:.1f}ms "
        f"({duration/count:.1f}ms avg per request)"
    )
    return duration


async def benchmark_event_loop_blocking(camera, name: str) -> None:
    """Test if event loop is blocked during rendering."""
    print(f"\n  {name}: Testing event loop blocking...")

    # Create a separate task that should run during rendering
    event_loop_free = []

    async def monitor_event_loop():
        """Monitor if event loop is responsive."""
        checks = 0
        while checks < 20:  # Check for 200ms
            event_loop_free.append(time.time())
            await asyncio.sleep(0.01)  # Check every 10ms
            checks += 1

    # Start monitoring
    monitor_task = asyncio.create_task(monitor_event_loop())

    # Trigger render
    render_task = asyncio.create_task(camera.async_camera_image())

    # Wait for both
    await asyncio.gather(monitor_task, render_task)

    # Analyze gaps in event loop checks
    if len(event_loop_free) >= 2:
        gaps = [
            (event_loop_free[i] - event_loop_free[i - 1]) * 1000
            for i in range(1, len(event_loop_free))
        ]
        max_gap = max(gaps)
        avg_gap = sum(gaps) / len(gaps)
        print(
            f"    Event loop gaps: max={max_gap:.1f}ms, avg={avg_gap:.1f}ms "
            f"(lower is better, <50ms is good)"
        )


async def run_benchmarks():
    """Run all performance benchmarks."""
    print("=" * 70)
    print("PERFORMANCE BENCHMARK: Before vs After Optimizations")
    print("=" * 70)

    # Create test image
    print("\nGenerating test image (2560x1440 → 1920x1080)...")
    test_image = create_test_image()
    print(f"Test image size: {len(test_image) / 1024:.1f}KB")

    config = {"width": 1920, "height": 1080}

    # Setup old implementation
    processor_old = ImageProcessorOld(config)
    camera_old = CameraOld(processor_old)
    camera_old._source_image = test_image

    # Setup new implementation
    processor_new = ImageProcessorNew(config)
    camera_new = CameraNew(processor_new)
    camera_new._source_image = test_image

    # Warm-up
    print("\nWarming up...")
    await camera_old.async_camera_image()
    await camera_new.async_camera_image()

    print("\n" + "=" * 70)
    print("TEST 1: Single Request Performance")
    print("=" * 70)
    old_single = await benchmark_single_request(camera_old, "BEFORE (blocking)")
    new_single = await benchmark_single_request(camera_new, "AFTER  (thread pool)")
    improvement = ((old_single - new_single) / old_single) * 100
    print(
        f"\n  → Improvement: {improvement:+.1f}% "
        f"({'faster' if improvement > 0 else 'slower'})"
    )
    print(
        "  Note: Single request may be similar, main benefit is non-blocking behavior"
    )

    print("\n" + "=" * 70)
    print("TEST 2: Concurrent Requests Performance (3 simultaneous clients)")
    print("=" * 70)
    old_concurrent = await benchmark_concurrent_requests(
        camera_old, "BEFORE (no deduplication)", 3
    )
    new_concurrent = await benchmark_concurrent_requests(
        camera_new, "AFTER  (with deduplication)", 3
    )
    improvement = ((old_concurrent - new_concurrent) / old_concurrent) * 100
    print(f"\n  → Improvement: {improvement:.1f}% faster")
    print(
        f"  → Time saved: {old_concurrent - new_concurrent:.1f}ms "
        f"({old_concurrent/new_concurrent:.1f}x speedup)"
    )

    print("\n" + "=" * 70)
    print("TEST 3: Event Loop Blocking (responsiveness during render)")
    print("=" * 70)
    await benchmark_event_loop_blocking(camera_old, "BEFORE (blocking)")
    await benchmark_event_loop_blocking(camera_new, "AFTER  (non-blocking)")

    print("\n" + "=" * 70)
    print("TEST 4: Sustained Load (10 requests over 5 seconds)")
    print("=" * 70)

    async def sustained_load_test(camera, name: str):
        """Simulate sustained load."""
        start = time.time()
        durations = []

        for i in range(10):
            req_start = time.time()
            await camera.async_camera_image()
            req_duration = (time.time() - req_start) * 1000
            durations.append(req_duration)
            await asyncio.sleep(0.5)  # 500ms between requests

        total_time = (time.time() - start) * 1000
        avg = sum(durations) / len(durations)
        min_time = min(durations)
        max_time = max(durations)

        print(f"  {name}:")
        print(
            f"    Avg: {avg:.1f}ms, Min: {min_time:.1f}ms, "
            f"Max: {max_time:.1f}ms, Total: {total_time:.1f}ms"
        )
        return avg

    old_sustained = await sustained_load_test(camera_old, "BEFORE")
    new_sustained = await sustained_load_test(camera_new, "AFTER ")
    improvement = ((old_sustained - new_sustained) / old_sustained) * 100
    print(f"\n  → Average response time improvement: {improvement:+.1f}%")

    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print("\nKey Improvements:")
    print("  1. Request Deduplication:")
    print(
        f"     - Concurrent requests: {old_concurrent:.0f}ms → {new_concurrent:.0f}ms "
        f"({improvement:.0f}% faster)"
    )
    print("     - Multiple clients now share a single render")
    print("\n  2. Thread Pool Execution:")
    print("     - Event loop remains responsive during rendering")
    print("     - Enables parallel processing across cameras")
    print("\n  3. Overall:")
    print("     - Better scalability for multiple concurrent clients")
    print("     - Non-blocking behavior improves system responsiveness")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(run_benchmarks())
