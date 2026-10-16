import { describe, expect, it } from 'vitest'
import { demoRoadRecords, getOverlayValue, scoreTone, travelModes, type OverlayKey } from '../data/demoRoadSegments'
import { filterRoadRecords, rankRoadRecords, selectVisibleRecord } from './roadSegments'

describe('dashboard segment behavior', () => {
  it('uses the selected travel profile value for each map overlay', () => {
    const record = demoRoadRecords[0]

    for (const mode of travelModes) {
      expect(getOverlayValue(record, mode.key)).toBe(record.segment.mode_suitability[mode.key])
    }
    expect(getOverlayValue(record, 'surface_quality_score')).toBe(record.segment.surface_quality_score)
  })

  it('maps configured score bands and missing values to the correct legend tone', () => {
    expect([80, 60, 40, 39, null].map(scoreTone)).toEqual(['good', 'fair', 'poor', 'critical', 'unrated'])
  })

  it('combines text, quality, and active-overlay minimum filters', () => {
    const result = filterRoadRecords(demoRoadRecords, {
      search: 'ROAD',
      quality: 'all',
      minimumScore: '70',
      overlay: 'cycling',
    })

    expect(result.map(({ roadName }) => roadName)).toEqual(['Station Road'])
  })

  it('keeps unrated records out of numeric thresholds and at the end of rankings', () => {
    const overlay: OverlayKey = 'surface_quality_score'
    const filtered = filterRoadRecords(demoRoadRecords, {
      search: '', quality: 'all', minimumScore: '60', overlay,
    })

    expect(filtered.every((record) => record.segment.surface_quality_score !== null)).toBe(true)
    expect(getOverlayValue(demoRoadRecords[8], overlay)).toBeNull()
    expect(scoreTone(getOverlayValue(demoRoadRecords[8], overlay))).toBe('unrated')
    expect(rankRoadRecords(demoRoadRecords, overlay).at(-1)?.roadName).toBe('Unrated Connector')
  })

  it('ranks the current overlay highest-first without mutating the source list', () => {
    const records = [...demoRoadRecords]
    const ranked = rankRoadRecords(records, 'walking')

    expect(ranked.slice(0, 2).map(({ roadName }) => roadName)).toEqual(['Garden Way', 'Riverside Drive'])
    expect(records).toEqual(demoRoadRecords)
  })

  it('selects the requested visible segment or falls back to the first visible record', () => {
    const visible = filterRoadRecords(demoRoadRecords, {
      search: '', quality: 'Good', minimumScore: 'all', overlay: 'surface_quality_score',
    })

    expect(selectVisibleRecord(visible, 'demo-005')?.roadName).toBe('Garden Way')
    expect(selectVisibleRecord(visible, 'hidden-id')?.roadName).toBe('Cedar Avenue')
    expect(selectVisibleRecord([], 'demo-005')).toBeUndefined()
  })
})
