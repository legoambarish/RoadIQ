import { useEffect, useRef, useState } from 'react'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import type { DemoRoadRecord, OverlayKey } from '../data/demoRoadSegments'
import { demoRoadRecords, getOverlayValue, overlayLabel, scoreTone } from '../data/demoRoadSegments'

type SegmentMapProps = {
  records: DemoRoadRecord[]
  selectedId: string
  overlay: OverlayKey
  onSelect: (segmentId: string) => void
}

const MAP_CENTER: L.LatLngExpression = [40.7128, -74.005]
const INITIAL_ZOOM = 15
const OSM_TILE_URL = 'https://tile.openstreetmap.org/{z}/{x}/{y}.png'
const OSM_ATTRIBUTION = '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap contributors</a>'

function toneColor(tone: ReturnType<typeof scoreTone>) {
  return {
    good: '#168264',
    fair: '#c38d2d',
    poor: '#d66d45',
    critical: '#b74e57',
    unrated: '#8b9793',
  }[tone]
}

function recordBounds(records: DemoRoadRecord[]) {
  const coordinates = records.flatMap(({ segment }) => segment.geometry.coordinates)
  return L.latLngBounds(coordinates.map(([longitude, latitude]) => [latitude, longitude] as L.LatLngTuple))
}

export function SegmentMap({ records, selectedId, overlay, onSelect }: SegmentMapProps) {
  const mapElement = useRef<HTMLDivElement>(null)
  const map = useRef<L.Map | null>(null)
  const selectedLabel = useRef<L.Tooltip | null>(null)
  const [zoom, setZoom] = useState(INITIAL_ZOOM)
  const [tileError, setTileError] = useState(false)
  const zoomLabel = `${zoom}×`

  useEffect(() => {
    if (!mapElement.current || map.current) return

    const instance = L.map(mapElement.current, {
      zoomControl: false,
      scrollWheelZoom: true,
      keyboard: true,
    }).setView(MAP_CENTER, INITIAL_ZOOM)

    const tiles = L.tileLayer(import.meta.env.VITE_MAP_TILE_URL || OSM_TILE_URL, {
      maxZoom: 19,
      attribution: import.meta.env.VITE_MAP_TILE_ATTRIBUTION || OSM_ATTRIBUTION,
    }).addTo(instance)
    tiles.on('tileerror', () => setTileError(true))
    instance.on('zoomend', () => setZoom(instance.getZoom()))
    map.current = instance

    const allBounds = recordBounds(demoRoadRecords)
    if (allBounds.isValid()) instance.fitBounds(allBounds.pad(0.2), { animate: false })
    const resize = window.setTimeout(() => instance.invalidateSize(), 0)

    return () => {
      window.clearTimeout(resize)
      instance.remove()
      map.current = null
    }
  }, [])

  useEffect(() => {
    const instance = map.current
    if (!instance) return

    if (selectedLabel.current) {
      instance.removeLayer(selectedLabel.current)
      selectedLabel.current = null
    }
    instance.eachLayer((layer) => {
      if (layer instanceof L.Polyline) instance.removeLayer(layer)
    })

    for (const record of records) {
      const value = getOverlayValue(record, overlay)
      const tone = scoreTone(value)
      const selected = record.segment.segment_id === selectedId
      const title = `${record.roadName}: ${value === null ? 'unrated' : `${Math.round(value)} out of 100`}`
      const positions = record.segment.geometry.coordinates.map(([longitude, latitude]) => [latitude, longitude] as L.LatLngTuple)
      const route = L.polyline(positions, {
        color: toneColor(tone),
        weight: selected ? 9 : 7,
        opacity: selected ? 1 : 0.82,
        lineCap: 'round',
        lineJoin: 'round',
        bubblingMouseEvents: false,
      }).addTo(instance)

      route.on('click', () => onSelect(record.segment.segment_id))
      const path = route.getElement()
      if (path) {
        path.setAttribute('role', 'button')
        path.setAttribute('tabindex', '0')
        path.setAttribute('aria-label', `${title}. Select to open segment details.`)
        path.setAttribute('aria-pressed', String(selected))
        path.addEventListener('keydown', (event) => {
          const keyEvent = event as KeyboardEvent
          if (keyEvent.key === 'Enter' || keyEvent.key === ' ') {
            keyEvent.preventDefault()
            onSelect(record.segment.segment_id)
          }
        })
      }

      if (selected) {
        const middle = positions[Math.floor(positions.length / 2)]
        if (middle) {
          selectedLabel.current = L.tooltip({ direction: 'top', offset: [0, -7], permanent: true, className: 'road-label' })
            .setLatLng(middle)
            .setContent(record.roadName)
            .addTo(instance)
        }
      }
    }

    const bounds = recordBounds(records)
    if (records.length > 0 && bounds.isValid()) instance.fitBounds(bounds.pad(0.2), { animate: false, maxZoom: 17 })
  }, [records, selectedId, overlay, onSelect])

  return (
    <section className="map-card" aria-labelledby="map-heading">
      <div className="map-card-header">
        <div>
          <div className="section-kicker">Interactive network map</div>
          <h2 id="map-heading">Road segments</h2>
          <p className="map-description">Select a colored route to inspect its demo record. Fixture routes and scores are illustrative; the OSM basemap is geographic context only.</p>
        </div>
        <div className="map-tools" aria-label="Map controls">
          <span className="map-tool-label">Map tiles</span>
          <button type="button" aria-label="Zoom out" onClick={() => map.current?.zoomOut()}>−</button>
          <span className="zoom-value" aria-live="polite">{zoomLabel}</span>
          <button type="button" aria-label="Zoom in" onClick={() => map.current?.zoomIn()}>+</button>
        </div>
      </div>

      <div className="map-canvas leaflet-map-canvas">
        <div ref={mapElement} className="leaflet-map" role="application" aria-label={`Interactive geographic map with illustrative road segments colored by ${overlayLabel(overlay)}. Select a route for details.`} />
        {tileError && <p className="map-tile-error" role="status">Basemap tiles are unavailable; fixture routes remain interactive. Check your connection.</p>}
        {records.length === 0 && <div className="map-empty-state"><strong>No roads match these filters</strong><span>Clear a filter to show the demo network again.</span></div>}
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
        <span>Fixture geometry and scores only</span>
      </div>
    </section>
  )
}
