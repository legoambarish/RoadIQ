"""Actual source-coordinate, tile deduplication and dataset split algorithms."""
import pytest

from app.services.india_detector import class_nms, tile_windows
from backend.scripts.prepare_rdd_india import HashTree, DuplicateGroups


def test_overlapping_tiles_cover_extreme_aspect_without_stretching():
    windows = tile_windows(1800, 300, 640)
    assert windows[0] == (0, 0, 640, 300)
    assert windows[-1][2:] == (1800, 300)
    assert all(a[2] >= b[0] for a, b in zip(windows, windows[1:]))


def test_tiling_bounds_resource_use():
    with pytest.raises(ValueError, match="resource limit"):
        tile_windows(10000, 10000, 320)


def test_class_nms_deduplicates_overlap_without_merging_different_classes():
    kept = class_nms([(0, .7, [0, 0, 10, 10]), (0, .8, [1, 1, 11, 11]), (3, .5, [1, 1, 11, 11])])
    assert len(kept) == 2
    assert kept[0][1] == .8
    assert {row[0] for row in kept} == {0, 3}


def test_complete_hash_tree_matches_exhaustive_hamming_neighbors():
    import random
    random.seed(7)
    values = [random.getrandbits(64) for _ in range(100)]
    values += [values[3] ^ 0b10101, values[8] ^ 0b1111, values[3]]
    tree = HashTree()
    for i, value in enumerate(values):
        expected = [j for j, old in enumerate(values[:i]) if (old ^ value).bit_count() <= 4]
        assert sorted(tree.neighbors(value)) == expected
        tree.add(value, i)


def test_groups_merge_transitively_before_split_assignment():
    groups = DuplicateGroups(4)
    groups.union(0, 2)
    groups.union(2, 3)
    assert groups.find(0) == groups.find(3)
    assert groups.find(1) != groups.find(0)
