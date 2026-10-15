export type QualityClass = 'poor' | 'fair' | 'good' | 'excellent'

export type Coordinate = {
  latitude: number
  longitude: number
}

export type RoadSegment = {
  segment_id: string
  start: Coordinate
  end: Coordinate
  quality_score: number
  quality_class: QualityClass
  scoring_method?: string
  observed_at?: string
  metadata?: Record<string, unknown>
}
