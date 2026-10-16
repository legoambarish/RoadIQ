# RoadIQ frontend

React + TypeScript + Vite dashboard for the RoadIQ prototype.

## Current experience

- Interactive Leaflet/OpenStreetMap map restricted to the OSM-mapped India boundary, opening on nine mapped streets in central Bengaluru. OSM supplies the displayed street geometry/name only; RoadIQ scores and profile values remain illustrative fixtures and are not surveys of those streets. Tiles require internet access.
- Everyday traveler briefs explain profile-specific road impacts in plain language. Engineer views replace those briefs with a contract-field evidence ledger, source and survey timestamp, provenance, confidence and scoring gates; fixture timestamps are identified as metadata, not real surveys.
- Surface condition, selected travel-profile suitability, and pedestrian infrastructure/comfort appear as separate assessments. Walking context includes footpath, crossing, and comfort fields; lane markings are not treated as walkability evidence.
- Searchable/filtered rankings and separate insight panels: Everyday sees network distributions; Engineer sees measurement-availability, provenance, and scoring-readiness audits. Insights summarize all currently filtered demo records, not only the selected map segment or an imported image.
- A sticky, responsive control dock keeps the five travel profiles and Everyday/Engineer view switch available during scrolling.
- Local-only road-image preview plus manual import of Task C's saved JSON report and optional annotated preview. Import the JSON to show saved quality/texture/candidate-region results; import the annotated image to see the CLI's texture-candidate visualization. The CLI JSON stores the annotation as a local path, so that image is selected separately. Selecting files does not run inference or send them anywhere. RSQI remains Unrated until complete evidence and fixed normalization references are available.
- API badge checks `GET /api/v1/health`; segment retrieval and image-analysis endpoints are not implemented.

The segment records are isolated in `src/data/demoRoadSegments.ts`. Their street names and line geometry reference OpenStreetMap ways; the geometry snapshot is in the frontend bundle and does not make runtime geocoding requests. The map mask uses the simplified OSM India boundary relation in `src/data/indiaBoundary.ts`. Both datasets are ODbL/OpenStreetMap contributor data and are attributed in the UI and source. The boundary is a display constraint, not a legal border reference or a nationwide road inventory. RoadIQ surface scores and travel-profile values remain `demo_fixture` values; they are not OSM measurements or condition surveys of these streets. Tile connectivity is needed for street context; the OSM street lines remain interactive if tiles fail. There is no model result, travel-safety rating, or backend scoring result behind those values. Task A's provisional scorer is present in the backend, but it is not connected to the dashboard and its default normalization profiles are empty. Production map-provider selection remains open.

Task C's local image-analysis service is merged into `main` and has no HTTP endpoint. It includes India-only dataset-manifest validation, an untrained texture-region heuristic, and optional experimental semantic road-ROI gating when a checkpoint is explicitly configured. No active trained checkpoint or held-out RoadIQ evaluation is available. The multi-country RDD2022 detector remains disabled under the India-only dataset policy. Validated pavement/material classification, stone-aggregate and separate metal-fragment models, and physical measurements are unavailable; the report labels these outputs unavailable rather than inventing results.

## Development

From this directory, install the npm dependencies and run:

```bash
npm run dev
npm run build
npm run lint
npm run test
```

Set `VITE_API_BASE_URL` to the FastAPI `/api/v1` base URL to change the health-check target. The frontend currently sends only the health request; it does not upload images or retrieve road segments.

The default basemap uses `https://tile.openstreetmap.org/{z}/{x}/{y}.png`. Set `VITE_MAP_TILE_URL` and `VITE_MAP_TILE_ATTRIBUTION` in the frontend environment when configuring another tile provider. Keep that provider's visible attribution. For OpenStreetMap tiles, follow the [OSM tile usage policy](https://operations.osmfoundation.org/policies/tiles/); do not prefetch tiles. Browser caching is left at its default.

## Structure

- `src/components/SegmentMap.tsx` — India-bounded Leaflet basemap, interactive OSM street lines, and overlay legend.
- `src/components/DashboardCharts.tsx` — fixture-based quality and travel-profile summaries.
- `src/components/ImageReportPanel.tsx` — local preview, Task C CLI report/annotation import, report-backed observations and provenance, scorer status, candidate RSQI weights, and unavailable report states.
- `src/components/ModeAssessmentPanel.tsx` — separate surface/profile summaries, plain-language traveler briefs, engineer evidence ledger, and pedestrian-context panel.
- `src/data/travelProfiles.ts` — profile-specific explanations and intended evidence categories; does not implement mode scoring.
- `src/data/demoRoadSegments.ts` — typed, clearly marked demo fixture records.
- `src/types/road-segment.ts` — shared road-segment TypeScript contract.
- `src/lib/api.ts` — health-only API client.
- `src/lib/roadSegments.ts` — dashboard record filtering, ranking, and selection helpers.
- `src/lib/roadSegments.test.ts` — overlay, status, filter, ranking, and selection tests.
