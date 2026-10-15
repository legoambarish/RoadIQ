export type DataSource = 'sensor' | 'image_inference' | 'user_input' | 'demo_fixture'

export type MeasurementStatus = 'observed' | 'estimated' | 'unavailable'

export type MeasurementUnit =
  | 'defects'
  | 'defects_per_km'
  | 'ratio'
  | 'severity_index_0_100'
  | 'm_per_km'
  | 'percent'

export type QualityLabel = 'Good' | 'Fair' | 'Poor' | 'Very Poor'

export type TravelMode = 'walking' | 'cycling' | 'two_wheeler' | 'car' | 'bus'

export type GeoJSONLineString = {
  type: 'LineString'
  coordinates: [longitude: number, latitude: number][]
}

export type Measurement = {
  value: number | null
  unit: MeasurementUnit
  status: MeasurementStatus
  source: DataSource | null
}

export type RoadMeasurements = {
  defect_count: Measurement
  defect_density: Measurement
  damaged_area_ratio: Measurement
  severity: Measurement
  roughness_iri: Measurement
  longitudinal_grade: Measurement
  crossfall: Measurement
}

export type DamageComponents = {
  damaged_area: number | null
  defect_density: number | null
  severity: number | null
  roughness: number | null
}

export type ModeSuitability = Record<TravelMode, number | null>

export type PedestrianContext = {
  footpath_present: boolean | null
  crossings_observed: boolean | null
  comfort_score: number | null
}

export type ProvenanceEntry = {
  field_path: string
  source: DataSource
}

export type RoadSegment = {
  segment_id: string
  geometry: GeoJSONLineString
  survey_source: string
  surveyed_at: string
  measurements: RoadMeasurements
  damage_components: DamageComponents
  surface_quality_score: number | null
  quality_label: QualityLabel | null
  mode_suitability: ModeSuitability
  pedestrian_context: PedestrianContext
  confidence: number | null
  evidence_coverage: number | null
  assessment_status: 'rated' | 'unrated'
  explanation: string
  data_provenance: ProvenanceEntry[]
}
