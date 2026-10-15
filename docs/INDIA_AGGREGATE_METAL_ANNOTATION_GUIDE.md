# India road aggregate and metal-fragment annotation guide

This guide defines the manual data needed to train and evaluate RoadIQ's two still-missing visual targets. It does not introduce another downloaded dataset. Use only photographs captured in India, with a free and documented right to use them for this non-commercial prototype.

## Capture and provenance

- Prefer close, sharp road-surface photographs where individual stone boundaries and small metal fragments can be distinguished. Wide driving-scene frames generally do not resolve individual aggregate grains well enough for instance counts.
- Keep the original image bytes. Do not upsample an image to make a small fragment appear more detailed.
- Record a manifest row per image with a stable image ID, relative path, Indian state/city or capture area, capture/source description, license or permission basis, and a route/sequence/session group ID.
- Keep all images from the same continuous drive, burst, road segment, or near-duplicate group in one split. Use train, validation, and test groups that are disjoint by route/session; never randomly split adjacent video frames across them.
- If ground-scale calibration is unavailable, retain image pixels and do not provide physical sizes or counts per square metre.

## Instance labels

Use a polygon-capable annotation tool and export COCO instance segmentation (polygon masks or RLE masks). Keep one annotation per visible object:

| Label | What to annotate | What not to include |
| --- | --- | --- |
| `stone_aggregate` | Each visually distinct, exposed stone grain/particle at the pavement surface, only when its boundary is resolvable in the image. | General asphalt/concrete texture, unresolved speckle, painted markings, shadows, pothole boundaries, or a single polygon covering a whole patch of texture. |
| `metal_fragment` | Each visible loose metal chip, shard, or fragment on the road surface, with the visible fragment boundary. | Manhole/utility covers, embedded road hardware, vehicles, foil/plastic/glass, or ambiguous shiny pixels. |

Do not relabel a generic debris object as metal. Leave uncertain objects unannotated and record an image-level review note rather than guessing. Include images with no target objects as verified negatives only when the relevant pavement area was reviewed.

## Review and evaluation

- Have a second reviewer inspect a sample of images and every ambiguous label before training. Resolve label definitions before expanding the annotation set.
- Check that polygons fit visible boundaries, same-class instances remain separate, and no visible target is accidentally omitted in images marked as reviewed negatives.
- Check image hashes and capture-group IDs across splits. Keep a final test split untouched until model and thresholds are frozen.
- Report instance precision/recall/AP for boxes or masks, and mask IoU/Dice for segmentation, per class and on the untouched test split. Do not infer real-world aggregate size or density from pixels without matching scale and usable pavement area.

## File handoff

Provide the original India-only images, the COCO JSON, and the provenance/split manifest together. Include license/permission evidence. RoadIQ currently has a road/pothole semantic-mask trainer; it does **not** yet have an aggregate/metal instance-training adapter. The annotations can be reviewed first, then an adapter and held-out evaluation can be implemented without changing the class definitions.
