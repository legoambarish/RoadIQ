"""Complete, uncapped Hamming-neighbor search for small local image corpora."""
from PIL import Image, ImageOps


class HashTree:
    def __init__(self):
        self.root = None

    def neighbors(self, value: int, distance: int = 4) -> list[int]:
        found, stack = [], [self.root] if self.root else []
        while stack:
            node = stack.pop()
            delta = (node[0] ^ value).bit_count()
            if delta <= distance:
                found.extend(node[1])
            stack.extend(child for edge, child in node[2].items() if delta - distance <= edge <= delta + distance)
        return found

    def add(self, value: int, index: int) -> None:
        if self.root is None:
            self.root = [value, [index], {}]
            return
        node = self.root
        while True:
            distance = (value ^ node[0]).bit_count()
            if distance == 0:
                node[1].append(index)
                return
            if distance not in node[2]:
                node[2][distance] = [value, [index], {}]
                return
            node = node[2][distance]


def dhash(image: Image.Image) -> int:
    gray = ImageOps.grayscale(image).resize((9, 8), Image.Resampling.LANCZOS).tobytes()
    result = 0
    for y in range(8):
        for x in range(8):
            result = (result << 1) | int(gray[y * 9 + x] > gray[y * 9 + x + 1])
    return result
