import { useMemo, useState } from 'react'
import type { DemoRoadRecord, OverlayKey } from '../data/demoRoadSegments'
import { demoRoadRecords, getOverlayValue, overlayLabel, scoreTone } from '../data/demoRoadSegments'

type SegmentMapProps = {
  records: DemoRoadRecord[]
  selectedId: string
  overlay: OverlayKey
  onSelect: (segmentId: string) => void
}

const MAP_WIDTH = 800
const MAP_HEIGHT = 510
const MAP_PADDING = 68

function projectRecords(records: DemoRoadRecord[]) {
  const coordinates = records.flatMap(({ segment }) => segment.geometry.coordinates)
  const longitudes = coordinates.map(([longitude]) => longitude)
  const latitudes = coordinates.map(([, latitude]) => latitude)
  const minLongitude = Math.min(...longitudes)
  const maxLongitude = Math.max(...longitudes)
  const minLatitude = Math.min(...latitudes)
  const maxLatitude = Math.max(...latitudes)
  const longitudeSpan = Math.max(maxLongitude - minLongitude, 0.0001)
  const latitudeSpan = Math.max(maxLatitude - minLatitude, 0.0001)
  const scale = Math.min(
    (MAP_WIDTH - MAP_PADDING * 2) / longitudeSpan,
    (MAP_HEIGHT - MAP_PADDING * 2) / latitudeSpan,
  )
  const drawnWidth = longitudeSpan * scale
  const drawnHeight = latitudeSpan * scale
  const offsetX = (MAP_WIDTH - drawnWidth) / 2
  const offsetY = (MAP_HEIGHT - drawnHeight) / 2

  return (longitude: number, latitude: number) => ({
    x: offsetX + (longitude - minLongitude) * scale,
    y: MAP_HEIGHT - offsetY - (latitude - minLatitude) * scale,
  })
}

function toneColor(tone: ReturnType<typeof scoreTone>) {
  return {
    good: '#168264',
    fair: '#c38d2d',
    poor: '#d66d45',
    critical: '#b74e57',
    unrated: '#8b9793',
  }[tone]
}

export function SegmentMap({ records, selectedId, overlay, onSelect }: SegmentMapProps) {
  const [zoom, setZoom] = useState(1)
  const frameRecords = records.length > 0 ? records : demoRoadRecords
  const project = useMemo(() => projectRecords(frameRecords), [frameRecords])
  const zoomLabel = `${Math.round(zoom * 100)}%`

  return (
    <section className="map-card" aria-labelledby="map-heading">
      <div className="map-card-header">
        <div>
          <div className="section-kicker">Interactive network map</div>
          <h2 id="map-heading">Road segments</h2>
          <p className="map-description">Select a colored route to inspect its demo record. Geometry is schematic; no basemap is connected.</p>
        </div>
        <div className="map-tools" aria-label="Map controls">
          <span className="map-tool-label">Illustrative geometry</span>
          <button type="button" aria-label="Zoom out" onClick={() => setZoom((value) => Math.max(0.8, value - 0.1))}>−</button>
          <span className="zoom-value" aria-live="polite">{zoomLabel}</span>
          <button type="button" aria-label="Zoom in" onClick={() => setZoom((value) => Math.min(1.6, value + 0.1))}>+</button>
        </div>
      </div>

      <div className="map-canvas">
        <svg className="network-map" viewBox={`0 0 ${MAP_WIDTH} ${MAP_HEIGHT}`} role="group" aria-label={`Interactive road segment map colored by ${overlayLabel(overlay)}. Select a segment for details.`}>
          <defs>
            <pattern id="map-grid" width="42" height="42" patternUnits="userSpaceOnUse">
              <path d="M 42 0 L 0 0 0 42" fill="none" stroke="#e7ece8" strokeWidth="1" />
            </pattern>
            <filter id="road-shadow" x="-20%" y="-20%" width="140%" height="140%">
              <feDropShadow dx="0" dy="2" stdDeviation="2" floodColor="#73837d" floodOpacity="0.2" />
            </filter>
          </defs>
          <rect width={MAP_WIDTH} height={MAP_HEIGHT} rx="18" fill="#f7f9f5" />
          <rect width={MAP_WIDTH} height={MAP_HEIGHT} rx="18" fill="url(#map-grid)" />
          <g className="map-blocks" aria-hidden="true">
            <path d="M90 94h126v68H90zM283 75h105v68H283zM495 88h135v78H495zM658 235h83v82h-83zM77 329h145v76H77zM301 355h113v73H301zM520 334h119v88H520z" />
            <path d="M238 223h110v61H238zM438 220h92v66h-92z" />
          </g>
          <g transform={`translate(${MAP_WIDTH / 2} ${MAP_HEIGHT / 2}) scale(${zoom}) translate(${-MAP_WIDTH / 2} ${-MAP_HEIGHT / 2})`}>
            {records.map((record) => {
              const points = record.segment.geometry.coordinates.map(([longitude, latitude]) => project(longitude, latitude))
              const path = points.map(({ x, y }, index) => `${index === 0 ? 'M' : 'L'} ${x} ${y}`).join(' ')
              const value = getOverlayValue(record, overlay)
              const tone = scoreTone(value)
              const selected = record.segment.segment_id === selectedId
              const midPoint = points[Math.floor(points.length / 2)]
              const title = `${record.roadName}: ${value === null ? 'unrated' : `${Math.round(value)} out of 100`}`

              return (
                <g
                  key={record.segment.segment_id}
                  className={`map-segment ${selected ? 'selected' : ''}`}
                  role="button"
                  tabIndex={0}
                  aria-label={`${title}. Select to open segment details.`}
                  aria-pressed={selected}
                  onClick={() => onSelect(record.segment.segment_id)}
                  onKeyDown={(event) => {
                    if (event.key === 'Enter' || event.key === ' ') {
                      event.preventDefault()
                      onSelect(record.segment.segment_id)
                    }
                  }}
                >
                  <title>{title}</title>
                  <path className="segment-shadow" d={path} />
                  <path className="segment-halo" d={path} stroke={toneColor(tone)} />
                  <path className="segment-line" d={path} stroke={toneColor(tone)} />
                  {midPoint && <circle className="segment-point" cx={midPoint.x} cy={midPoint.y} r={selected ? 8 : 6} fill={toneColor(tone)} />}
                  {selected && midPoint && (
                    <g className="map-label" transform={`translate(${midPoint.x + 12} ${midPoint.y - 20})`}>
                      <rect width={Math.min(174, record.roadName.length * 7 + 24)} height="28" rx="8" />
                      <text x="12" y="18">{record.roadName}</text>
                    </g>
                  )}
                </g>
              )
            })}
          </g>
          <text className="map-caption" x="22" y="482">DEMO NETWORK · NO LIVE BASEMAP</text>
          <g className="north-indicator" transform="translate(752 50)" aria-hidden="true">
            <text x="0" y="0">N</text>
            <path d="M0 8v24" />
            <path d="m0 8-5 9h10z" />
          </g>
        </svg>
        <div className="map-empty-state" hidden={records.length > 0}>
          <strong>No roads match these filters</strong>
          <span>Clear a filter to show the demo network again.</span>
        </div>
        <div className="map-legend" aria-label="Overlay score legend">
          <span><i className="legend-dot good" />80–100</span>
          <span><i className="legend-dot fair" />60–79</span>
          <span><i className="legend-dot poor" />40–59</span>
          <span><i className="legend-dot critical" />0–39</span>
          <span><i className="legend-dot unrated" />Unrated</span>
        </div>
      </div>
      <div className="map-footer">
        <span><strong>{records.length}</strong> segments in view</span>
        <span>Values are illustrative fixtures, not live road measurements.</span>
      </div>
    </section>
  )
}
