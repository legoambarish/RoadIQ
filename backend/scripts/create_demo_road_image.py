"""Create a deterministic synthetic road-texture image for a safe local demo."""

from __future__ import annotations

import argparse
import math
import random
from pathlib import Path

from PIL import Image, ImageDraw


def create_synthetic_road_image(
    seed: int = 42,
    size: tuple[int, int] = (640, 480),
) -> Image.Image:
    """Draw a synthetic, uncalibrated asphalt-like texture with aggregate-like shapes."""
    rng = random.Random(seed)
    width, height = size
    image = Image.new("RGB", size)
    pixels = image.load()
    for y in range(height):
        for x in range(width):
            shade = 91 + rng.randint(-5, 5)
            pixels[x, y] = (shade, shade + rng.randint(-2, 2), shade - rng.randint(-2, 2))

    draw = ImageDraw.Draw(image)
    rows, columns = 7, 8
    cell_w, cell_h = width / columns, height / rows
    for row in range(rows):
        for column in range(columns):
            center_x = (column + 0.5 + rng.uniform(-0.18, 0.18)) * cell_w
            center_y = (row + 0.5 + rng.uniform(-0.18, 0.18)) * cell_h
            radius_x = rng.uniform(12, 28)
            radius_y = rng.uniform(9, 22)
            vertices = []
            for step in range(9):
                angle = step * 2 * 3.141592653589793 / 9
                jitter = rng.uniform(0.78, 1.18)
                vertices.append((
                    center_x + radius_x * jitter * math.cos(angle),
                    center_y + radius_y * jitter * math.sin(angle),
                ))
            stone = rng.randint(67, 118)
            draw.polygon(
                vertices,
                fill=(stone, stone + rng.randint(-2, 2), stone - rng.randint(-2, 2)),
                outline=(55, 58, 56),
            )
            for _ in range(18):
                x = int(center_x + rng.uniform(-radius_x * 0.7, radius_x * 0.7))
                y = int(center_y + rng.uniform(-radius_y * 0.7, radius_y * 0.7))
                dot = rng.randint(max(0, stone - 28), min(255, stone + 24))
                draw.ellipse((x, y, x + 1, y + 1), fill=(dot, dot, dot))
    return image


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("/tmp/roadiq-synthetic-road-texture.png"))
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    create_synthetic_road_image(seed=args.seed).save(args.output, format="PNG")
    print(f"Synthetic demo image written to {args.output} (seed={args.seed}); not a real road photograph.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
