# RoadIQ frontend

React + TypeScript + Vite dashboard for the RoadIQ prototype.

## Current experience

- Interactive schematic map of demo road segments with Road Quality and five travel-profile overlays.
- Everyday and Engineer detail views, searchable/filtered rankings, quality and profile charts, and segment evidence details.
- Local-only road-image preview with explicit Unrated/unavailable report states. The selected file is not sent anywhere and no inference runs.
- API badge checks `GET /api/v1/health`; segment retrieval and image-analysis endpoints are not implemented.

The segment network and numeric values are isolated in `src/data/demoRoadSegments.ts` and marked as illustrative `demo_fixture` data. There is no live basemap, model result, travel-safety rating, or scoring engine behind those values. Map-provider selection remains open. The SVG map displays fixture GeoJSON geometry and supports segment selection and zoom.

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
- `src/components/ImageReportPanel.tsx` — local preview and honest unavailable report shell.
- `src/data/demoRoadSegments.ts` — typed, clearly marked demo fixture records.
- `src/types/road-segment.ts` — shared road-segment TypeScript contract.
- `src/lib/api.ts` — health-only API client.
