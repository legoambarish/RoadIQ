# RoadIQ frontend

React + TypeScript + Vite dashboard for the RoadIQ prototype.

## Current experience

- Interactive schematic map of demo road segments with Road Quality and five travel-profile overlays.
- Everyday traveler briefs explain profile-specific road impacts in plain language. Engineer views replace those briefs with a contract-field evidence ledger, provenance, confidence and scoring gates; neither mode treats fixtures as model results.
- Surface condition, selected travel-profile suitability, and pedestrian infrastructure/comfort appear as separate assessments. Walking context includes footpath, crossing, and comfort fields; lane markings are not treated as walkability evidence.
- Searchable/filtered rankings and separate insight panels: Everyday sees network distributions; Engineer sees measurement-availability, provenance, and scoring-readiness audits. Insights summarize all currently filtered demo records, not only the selected map segment or an imported image.
- A sticky, responsive control dock keeps the five travel profiles and Everyday/Engineer view switch available during scrolling.
- Local-only road-image preview plus manual import of Task C's saved JSON report and optional annotated preview. Import the JSON to show saved quality/texture/candidate-region results; import the annotated image to see the CLI's texture-candidate visualization. The CLI JSON stores the annotation as a local path, so that image is selected separately. Selecting files does not run inference or send them anywhere. RSQI remains Unrated until complete evidence and fixed normalization references are available.
- API badge checks `GET /api/v1/health`; segment retrieval and image-analysis endpoints are not implemented.

The segment network and numeric values are isolated in `src/data/demoRoadSegments.ts` and marked as illustrative `demo_fixture` data. There is no live basemap, model result, travel-safety rating, or backend scoring result behind those values. Task A's provisional scorer is present in the backend, but it is not connected to the dashboard and its default normalization profiles are empty. Map-provider selection remains open. The prominent SVG map displays fixture GeoJSON geometry and supports segment selection and zoom; it is a schematic network view, not a tiled street map.

Task C's local image-analysis service is merged into `main` and has no HTTP endpoint. It includes India-only dataset-manifest validation, an untrained texture-region heuristic, and optional experimental semantic road-ROI gating when a checkpoint is explicitly configured. No active trained checkpoint or held-out RoadIQ evaluation is available. The multi-country RDD2022 detector remains disabled under the India-only dataset policy. Validated pavement/material classification, stone-aggregate and separate metal-fragment models, and physical measurements are unavailable; the report labels these outputs unavailable rather than inventing results.

## Development

From this directory, install the npm dependencies and run:

```bash
npm run dev
npm run build
npm run lint
```

Set `VITE_API_BASE_URL` to the FastAPI `/api/v1` base URL to change the health-check target. The frontend currently sends only the health request; it does not upload images or retrieve road segments.

## Structure

- `src/components/SegmentMap.tsx` — interactive fixture geometry and overlay.
- `src/components/DashboardCharts.tsx` — fixture-based quality and travel-profile summaries.
- `src/components/ImageReportPanel.tsx` — local preview, Task C CLI report/annotation import, report-backed observations and provenance, scorer status, candidate RSQI weights, and unavailable report states.
- `src/components/ModeAssessmentPanel.tsx` — separate surface/profile summaries, plain-language traveler briefs, engineer evidence ledger, and pedestrian-context panel.
- `src/data/travelProfiles.ts` — profile-specific explanations and intended evidence categories; does not implement mode scoring.
- `src/data/demoRoadSegments.ts` — typed, clearly marked demo fixture records.
- `src/types/road-segment.ts` — shared road-segment TypeScript contract.
- `src/lib/api.ts` — health-only API client.
