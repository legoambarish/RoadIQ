import type { RoadSegment, TravelMode } from '../types/road-segment'

export type DemoRoadRecord = {
  segment: RoadSegment
  roadName: string
  area: string
  note: string
}

export type OverlayKey = 'surface_quality_score' | TravelMode

const unavailableMeasurement = (unit: RoadSegment['measurements']['defect_count']['unit']) => ({
  value: null,
  unit,
  status: 'unavailable' as const,
  source: null,
})

const geometry = (coordinates: [number, number][]): RoadSegment['geometry'] => ({
  type: 'LineString',
  coordinates,
})

function makeRecord(
  id: string,
  roadName: string,
  score: number | null,
  modes: RoadSegment['mode_suitability'],
  coordinates: [number, number][],
  note: string,
  defectCount: number | null,
): DemoRoadRecord {
  const label = score === null ? null : score >= 80 ? 'Good' : score >= 60 ? 'Fair' : score >= 40 ? 'Poor' : 'Very Poor'
  const rated = score !== null

  return {
    roadName,
    area: 'Example network',
    note,
    segment: {
      segment_id: id,
      geometry: geometry(coordinates),
      survey_source: 'RoadIQ illustrative demo fixture',
      surveyed_at: '2026-10-15T09:30:00+05:30',
      measurements: {
        defect_count: defectCount === null
          ? unavailableMeasurement('defects')
          : { value: defectCount, unit: 'defects', status: 'estimated', source: 'demo_fixture' },
        defect_density: unavailableMeasurement('defects_per_km'),
        damaged_area_ratio: unavailableMeasurement('ratio'),
        severity: unavailableMeasurement('severity_index_0_100'),
        roughness_iri: unavailableMeasurement('m_per_km'),
        longitudinal_grade: unavailableMeasurement('percent'),
        crossfall: unavailableMeasurement('percent'),
      },
      damage_components: rated
        ? { damaged_area: 100 - score, defect_density: 100 - score, severity: 100 - score, roughness: 100 - score }
        : { damaged_area: null, defect_density: null, severity: null, roughness: null },
      surface_quality_score: score,
      quality_label: label,
      mode_suitability: modes,
      pedestrian_context: { footpath_present: null, crossings_observed: null, comfort_score: null },
      confidence: null,
      evidence_coverage: null,
      assessment_status: rated ? 'rated' : 'unrated',
      explanation: rated
        ? 'Illustrative fixture value for dashboard behavior only. It is not a measured or validated road assessment.'
        : 'Demo geometry only. No measured evidence or quality rating is available.',
      data_provenance: [
        { field_path: 'geometry', source: 'demo_fixture' },
        ...(rated ? [{ field_path: 'surface_quality_score', source: 'demo_fixture' as const }] : []),
        { field_path: 'mode_suitability', source: 'demo_fixture' },
      ],
    },
  }
}

export const demoRoadRecords: DemoRoadRecord[] = [
  makeRecord('demo-001', 'Cedar Avenue', 86, { walking: 78, cycling: 84, two_wheeler: 89, car: 91, bus: 82 }, [[-74.009, 40.7112], [-74.006, 40.7141]], 'Continuous route with a strong demo surface score.', 1),
  makeRecord('demo-002', 'Canal Street', 72, { walking: 74, cycling: 71, two_wheeler: 76, car: 80, bus: 69 }, [[-74.006, 40.7141], [-74.0028, 40.7144]], 'Mid-range demo quality; inspect segment details for the available evidence.', 3),
  makeRecord('demo-003', 'Union Road', 58, { walking: 52, cycling: 61, two_wheeler: 65, car: 69, bus: 62 }, [[-74.006, 40.7141], [-74.004, 40.7113]], 'Lower demo surface score. Mode values are illustrative and are not safety advice.', 5),
  makeRecord('demo-004', 'Harbor Link', 43, { walking: 46, cycling: 48, two_wheeler: 54, car: 60, bus: 57 }, [[-74.0028, 40.7144], [-74.001, 40.7115]], 'Low demo score; numeric values are placeholders for interface testing.', 7),
  makeRecord('demo-005', 'Garden Way', 91, { walking: 94, cycling: 89, two_wheeler: 84, car: 79, bus: 73 }, [[-74.009, 40.7112], [-74.0061, 40.7101]], 'High demo surface score with separate illustrative walking context.', 0),
  makeRecord('demo-006', 'Station Road', 67, { walking: 66, cycling: 74, two_wheeler: 78, car: 82, bus: 77 }, [[-74.0061, 40.7101], [-74.004, 40.7113]], 'A mixed example for comparing condition and travel profiles.', 2),
  makeRecord('demo-007', 'Market Lane', 34, { walking: 42, cycling: 39, two_wheeler: 48, car: 55, bus: 51 }, [[-74.004, 40.7113], [-74.001, 40.7115]], 'Very low demo score; does not imply a certified closure or safety judgment.', 9),
  makeRecord('demo-008', 'Riverside Drive', 79, { walking: 82, cycling: 88, two_wheeler: 83, car: 86, bus: 80 }, [[-74.0028, 40.7144], [-74.0061, 40.7101]], 'Illustrative route with a stronger cycling profile.', 2),
  makeRecord('demo-009', 'Unrated Connector', null, { walking: null, cycling: null, two_wheeler: null, car: null, bus: null }, [[-74.009, 40.7112], [-74.001, 40.7115]], 'No score or suitability estimate is available. Missing evidence is not zero.', null),
]

export const travelModes: { key: TravelMode; label: string; shortLabel: string; icon: string }[] = [
  { key: 'walking', label: 'Walking', shortLabel: 'Walk', icon: '↗' },
  { key: 'cycling', label: 'Cycling', shortLabel: 'Cycle', icon: '◉' },
  { key: 'two_wheeler', label: 'Two-wheeler', shortLabel: '2-wheel', icon: '⌁' },
  { key: 'car', label: 'Car', shortLabel: 'Car', icon: '▰' },
  { key: 'bus', label: 'Bus', shortLabel: 'Bus', icon: '▥' },
]

export function getOverlayValue(record: DemoRoadRecord, overlay: OverlayKey): number | null {
  return overlay === 'surface_quality_score'
    ? record.segment.surface_quality_score
    : record.segment.mode_suitability[overlay]
}

export function overlayLabel(overlay: OverlayKey): string {
  return overlay === 'surface_quality_score'
    ? 'Road quality'
    : travelModes.find((mode) => mode.key === overlay)?.label ?? 'Travel profile'
}

export function scoreTone(value: number | null): 'good' | 'fair' | 'poor' | 'critical' | 'unrated' {
  if (value === null) return 'unrated'
  if (value >= 80) return 'good'
  if (value >= 60) return 'fair'
  if (value >= 40) return 'poor'
  return 'critical'
}
