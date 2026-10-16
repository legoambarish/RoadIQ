import type { RoadSegment, TravelMode } from '../types/road-segment'

export type DemoRoadRecord = {
  segment: RoadSegment
  roadName: string
  area: string
  note: string
  osmWayId: number
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
  osmWayId: number,
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
    area: 'Central Bengaluru, Karnataka',
    note,
    osmWayId,
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
        : 'No illustrative score or measured condition evidence is available.',
      data_provenance: [
        ...(rated ? [{ field_path: 'surface_quality_score', source: 'demo_fixture' as const }] : []),
        { field_path: 'mode_suitability', source: 'demo_fixture' },
      ],
    },
  }
}

export const demoRoadRecords: DemoRoadRecord[] = [
  // Road geometry/name snapshots from these OSM ways; score and profile values remain fixtures.
  // © OpenStreetMap contributors, ODbL 1.0. Nominatim lookup on 2026-10-16.
  makeRecord('demo-001', 1125542416, 'Mahatma Gandhi Road', 86, { walking: 78, cycling: 84, two_wheeler: 89, car: 91, bus: 82 }, [[77.6082541, 12.9751131], [77.6087811, 12.9749918], [77.6110102, 12.9744669], [77.6110365, 12.9744611], [77.6110658, 12.9744536], [77.6111115, 12.9744418]], 'Illustrative score only; no condition survey of this road is available.', 1),
  makeRecord('demo-002', 1125542419, 'Brigade Road', 72, { walking: 74, cycling: 71, two_wheeler: 76, car: 80, bus: 69 }, [[77.6079254, 12.9749558], [77.6077326, 12.9743274], [77.6077228, 12.9742935], [77.6077113, 12.9742552], [77.6075185, 12.9735977], [77.60733, 12.9730694], [77.6072761, 12.972921], [77.6071457, 12.9725335], [77.6070825, 12.9723313]], 'Illustrative score only; no condition survey of this road is available.', 3),
  makeRecord('demo-003', 48166762, 'Church Street', 58, { walking: 52, cycling: 61, two_wheeler: 65, car: 69, bus: 62 }, [[77.6077326, 12.9743274], [77.6076409, 12.9743483], [77.6069506, 12.9745113], [77.6069187, 12.9745188], [77.6068128, 12.9745439], [77.606542, 12.9746081], [77.6063194, 12.9746597], [77.6062613, 12.9746734], [77.6061309, 12.9747032], [77.605951, 12.9747468], [77.6057645, 12.9747918], [77.6057121, 12.9748034], [77.6055843, 12.9748324], [77.6055212, 12.9748465], [77.6053438, 12.9748887], [77.6051418, 12.9749413], [77.6051351, 12.9749431], [77.6047852, 12.9750244], [77.6046942, 12.9750479], [77.6046678, 12.975054], [77.6042812, 12.9751524], [77.6041502, 12.9751867], [77.6040731, 12.9752046], [77.6035633, 12.9753321], [77.6033625, 12.9753824], [77.6030624, 12.9754575], [77.6028006, 12.9755231], [77.6027863, 12.9755262]], 'Illustrative score only; no condition survey of this road is available.', 5),
  makeRecord('demo-004', 461556535, 'Residency Road', 43, { walking: 46, cycling: 48, two_wheeler: 54, car: 60, bus: 57 }, [[77.5996988, 12.9675244], [77.5999243, 12.967706], [77.6001938, 12.9679072], [77.600212, 12.9679192], [77.6002368, 12.9679353], [77.6003351, 12.968], [77.6004396, 12.9680441], [77.6010695, 12.9684304], [77.601116, 12.9684592], [77.6013686, 12.968622], [77.6016717, 12.9688391], [77.6018476, 12.968965], [77.6019578, 12.9690533], [77.6020679, 12.9691415], [77.6024023, 12.9694188], [77.6024469, 12.9694552], [77.6024848, 12.9694839], [77.6029278, 12.9698196], [77.6029825, 12.9698611], [77.6029865, 12.9698639], [77.6037113, 12.9703682], [77.604087, 12.9705619], [77.6042893, 12.970658], [77.6046571, 12.9708359], [77.6046777, 12.9708459], [77.6048071, 12.9709016]], 'Illustrative score only; no condition survey of this road is available.', 7),
  makeRecord('demo-005', 107215079, 'Cubbon Road', 91, { walking: 94, cycling: 89, two_wheeler: 84, car: 79, bus: 73 }, [[77.6034542, 12.978999], [77.6037535, 12.978898], [77.6043145, 12.9787121], [77.6049429, 12.9785076], [77.605438, 12.9783446], [77.6054847, 12.9783292], [77.6059049, 12.9782033]], 'Illustrative score only; no condition survey of this road is available.', 0),
  makeRecord('demo-006', 36913434, 'Kasturba Road', 67, { walking: 66, cycling: 74, two_wheeler: 78, car: 82, bus: 77 }, [[77.5992296, 12.9765722], [77.5991521, 12.9765135], [77.5991167, 12.9764894], [77.5987758, 12.976243], [77.5985482, 12.9760757], [77.5984411, 12.975997], [77.5982649, 12.9758675], [77.5976688, 12.9754346], [77.5975811, 12.9753732], [77.5973362, 12.9752005], [77.5971708, 12.9750868], [77.5969938, 12.974963], [77.5968764, 12.9748764], [77.5966076, 12.9746556], [77.5960041, 12.9741523], [77.5959319, 12.9740925], [77.595774, 12.973962], [77.595425, 12.9736733], [77.5952849, 12.9735589], [77.5950978, 12.9733879], [77.5949249, 12.9731793], [77.5948818, 12.9731258], [77.5942499, 12.9723557]], 'Illustrative score only; no condition survey of this road is available.', 2),
  makeRecord('demo-007', 52246044, 'Infantry Road', 34, { walking: 42, cycling: 39, two_wheeler: 48, car: 55, bus: 51 }, [[77.5971513, 12.9827271], [77.5972842, 12.9826708], [77.5974734, 12.9826053], [77.597875, 12.9824663], [77.5980314, 12.982415], [77.5983672, 12.9823021], [77.5988597, 12.9821412], [77.5989486, 12.9821105], [77.5993292, 12.9819793], [77.5995606, 12.9818995], [77.5998602, 12.9817962], [77.5998887, 12.9817864], [77.6001577, 12.981694], [77.6002213, 12.9816721], [77.6004298, 12.9816005], [77.6006644, 12.9815199], [77.6007293, 12.9814976], [77.6009838, 12.9814101], [77.6012441, 12.9813207], [77.6013577, 12.9812816]], 'Illustrative score only; no condition survey of this road is available.', 9),
  makeRecord('demo-008', 112657835, 'Lavelle Road', 79, { walking: 82, cycling: 88, two_wheeler: 83, car: 86, bus: 80 }, [[77.5977545, 12.9712043], [77.5977142, 12.9711455], [77.5976912, 12.9710601], [77.597687, 12.9710266], [77.5976076, 12.9703961], [77.597521, 12.9697962], [77.5974964, 12.9696251], [77.5972801, 12.969343], [77.5971996, 12.9692286], [77.5969772, 12.968991], [77.5968014, 12.9687859], [77.5966132, 12.9685534], [77.5964879, 12.9683025], [77.5964192, 12.9680663], [77.5964309, 12.9675143], [77.596436, 12.9674562], [77.5964813, 12.9669374], [77.5965095, 12.9666729], [77.5965335, 12.9664436], [77.5965955, 12.9658521], [77.5966039, 12.9657718], [77.5967368, 12.9651907], [77.5967546, 12.965145]], 'Illustrative score only; no condition survey of this road is available.', 2),
  makeRecord('demo-009', 36853688, 'Richmond Road', null, { walking: null, cycling: null, two_wheeler: null, car: null, bus: null }, [[77.6142406, 12.9684789], [77.6143081, 12.9685062], [77.614346, 12.9685245], [77.6144118, 12.9685625], [77.6146784, 12.9687152], [77.6153598, 12.9691223], [77.6154849, 12.9691943], [77.6160422, 12.9695152], [77.6162645, 12.9696401], [77.6164738, 12.9697639], [77.6165079, 12.9697838], [77.6166564, 12.9698724], [77.6170367, 12.9700926], [77.6170796, 12.9701171], [77.6176667, 12.970469], [77.6180173, 12.9706938], [77.6180955, 12.9707362], [77.6193053, 12.9714627], [77.6193459, 12.9715128], [77.6193776, 12.9715564], [77.6194245, 12.9716361], [77.6194357, 12.9716735], [77.6194581, 12.9717456], [77.6194954, 12.9718218]], 'No illustrative score is available. Missing evidence is not zero.', null),
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
