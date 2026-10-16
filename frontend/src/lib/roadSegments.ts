import type { DemoRoadRecord, OverlayKey } from '../data/demoRoadSegments'
import { getOverlayValue } from '../data/demoRoadSegments'

export type SegmentFilters = {
  search: string
  quality: string
  minimumScore: string
  overlay: OverlayKey
}

export function filterRoadRecords(records: DemoRoadRecord[], filters: SegmentFilters): DemoRoadRecord[] {
  const query = filters.search.trim().toLocaleLowerCase()
  return records.filter((record) => {
    const matchesSearch = !query
      || record.roadName.toLocaleLowerCase().includes(query)
      || record.segment.segment_id.toLocaleLowerCase().includes(query)
    const matchesQuality = filters.quality === 'all'
      || (filters.quality === 'unrated'
        ? record.segment.assessment_status === 'unrated'
        : record.segment.quality_label === filters.quality)
    const value = getOverlayValue(record, filters.overlay)
    const matchesMinimum = filters.minimumScore === 'all'
      || (value !== null && value >= Number(filters.minimumScore))
    return matchesSearch && matchesQuality && matchesMinimum
  })
}

export function rankRoadRecords(records: DemoRoadRecord[], overlay: OverlayKey): DemoRoadRecord[] {
  return [...records].sort((left, right) => {
    const leftValue = getOverlayValue(left, overlay)
    const rightValue = getOverlayValue(right, overlay)
    if (leftValue === null && rightValue === null) return left.roadName.localeCompare(right.roadName)
    if (leftValue === null) return 1
    if (rightValue === null) return -1
    return rightValue - leftValue
  })
}

export function selectVisibleRecord(records: DemoRoadRecord[], selectedId: string): DemoRoadRecord | undefined {
  return records.find((record) => record.segment.segment_id === selectedId) ?? records[0]
}
