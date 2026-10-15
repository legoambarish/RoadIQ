# RoadIQ scoring specification

## Status
This document defines a placeholder scoring model for the initial scaffold. It intentionally does not represent an approved production algorithm or a finalized field measurement protocol.

## Score scale
Road quality is defined on a 0-100 scale:
- 0 = worst observed condition
- 100 = best observed condition

This scale is intentionally simple and human-readable. It is suitable for scaffolding but must be replaced by a validated operational model before production use.

## Placeholder classification rules
The initial schema maps score ranges to a quality class using the following rules:
- 0.0-24.9: `poor`
- 25.0-49.9: `fair`
- 50.0-74.9: `good`
- 75.0-100.0: `excellent`

These thresholds are planning assumptions rather than verified road-condition research.

## Unresolved decisions
- Whether the final scoring model should be supervised or heuristic-driven
- Whether image-derived defect counts should be weighted differently by road class
- Whether `quality_score` should be derived from GNSS, camera, or mixed-sensor input
- How to calibrate thresholds against real road data

## Assumptions
- Score ranges are based on a placeholder interpretation of road health and should be treated as demo logic.
- The road segment sample data is intentionally deterministic and is not meant to represent real geographic conditions.
- Any future algorithm must validate all assumptions with domain-specific data and stakeholder review before deployment.
