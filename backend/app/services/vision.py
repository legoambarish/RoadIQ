"""Computer-vision boundary for future defect inference.

This is intentionally a placeholder module. The production implementation will accept an image
or frame and return a structured defect report, but the initial scaffold does not download
any weights or run live inference.
"""


class VisionInferenceError(RuntimeError):
    """Raised when a future inference call cannot produce a valid result."""


def infer_road_defects(image_bytes: bytes, *, source_name: str = 'unknown') -> dict[str, object]:
    raise NotImplementedError(
        'Road defect inference is intentionally not implemented in the initial scaffold. '
        'A model, preprocessing pipeline, and error contract will be added later.'
    )
