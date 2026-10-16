import { describe, expect, it } from 'vitest'
import { demoRoadRecords, getOverlayValue, scoreTone, travelModes, type OverlayKey } from '../data/demoRoadSegments'
import { filterRoadRecords, rankRoadRecords, selectVisibleRecord } from './roadSegments'

describe('dashboard segment behavior', () => {
  it('keeps the map demo geometry within India and links each line to an OSM way', () => {
    expect(demoRoadRecords.map(({ osmWayId }) => osmWayId)).toEqual([
      1125542416, 1125542419, 48166762, 461556535, 107215079, 36913434, 52246044, 112657835, 36853688,
    ])

    for (const { segment, area } of demoRoadRecords) {
      expect(area).toBe('Central Bengaluru, Karnataka')
      expect(segment.data_provenance.some(({ field_path }) => field_path === 'geometry')).toBe(false)
      for (const [longitude, latitude] of segment.geometry.coordinates) {
        expect(longitude).toBeGreaterThanOrEqual(68)
        expect(longitude).toBeLessThanOrEqual(97.5)
        expect(latitude).toBeGreaterThanOrEqual(6.5)
        expect(latitude).toBeLessThanOrEqual(37.5)
      }
    }
  })

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
      search: 'Brigade',
      quality: 'all',
      minimumScore: '70',
      overlay: 'cycling',
    })

    expect(result.map(({ roadName }) => roadName)).toEqual(['Brigade Road'])
  })

  it('keeps unrated records out of numeric thresholds and at the end of rankings', () => {
    const overlay: OverlayKey = 'surface_quality_score'
    const filtered = filterRoadRecords(demoRoadRecords, {
      search: '', quality: 'all', minimumScore: '60', overlay,
    })

    expect(filtered.every((record) => record.segment.surface_quality_score !== null)).toBe(true)
    expect(getOverlayValue(demoRoadRecords[8], overlay)).toBeNull()
    expect(scoreTone(getOverlayValue(demoRoadRecords[8], overlay))).toBe('unrated')
    expect(rankRoadRecords(demoRoadRecords, overlay).at(-1)?.roadName).toBe('Richmond Road')
  })

  it('ranks the current overlay highest-first without mutating the source list', () => {
    const records = [...demoRoadRecords]
    const ranked = rankRoadRecords(records, 'walking')

    expect(ranked.slice(0, 2).map(({ roadName }) => roadName)).toEqual(['Cubbon Road', 'Lavelle Road'])
    expect(records).toEqual(demoRoadRecords)
  })

  it('selects the requested visible segment or falls back to the first visible record', () => {
    const visible = filterRoadRecords(demoRoadRecords, {
      search: '', quality: 'Good', minimumScore: 'all', overlay: 'surface_quality_score',
    })

    expect(selectVisibleRecord(visible, 'demo-005')?.roadName).toBe('Cubbon Road')
    expect(selectVisibleRecord(visible, 'hidden-id')?.roadName).toBe('Mahatma Gandhi Road')
    expect(selectVisibleRecord([], 'demo-005')).toBeUndefined()
  })
})
