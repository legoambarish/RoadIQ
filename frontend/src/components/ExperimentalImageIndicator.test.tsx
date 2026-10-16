import { renderToStaticMarkup } from 'react-dom/server'
import { describe, expect, it } from 'vitest'
import { ExperimentalImageIndicator } from './ExperimentalImageIndicator'

describe('experimental image measurements', () => {
  it('renders calculated image coverage separately from RSQI', () => {
    const html = renderToStaticMarkup(<ExperimentalImageIndicator indicator={{
      version: 'candidate-coverage-v1',
      status: 'available',
      candidate_count: 2,
      candidate_box_coverage_percent: 12.345,
      predicted_pothole_pixel_fraction_percent: 4.5,
      unavailable_reason: null,
      limitations: [],
    }} />)

    expect(html).toContain('12.35%')
    expect(html).toContain('4.50%')
    expect(html).toContain('not RSQI')
    expect(html).toContain('zero candidates does not mean a clear road')
  })

  it('explains why measurements are missing when inference is unavailable', () => {
    const html = renderToStaticMarkup(<ExperimentalImageIndicator indicator={{
      version: 'candidate-coverage-v1',
      status: 'unavailable',
      candidate_count: null,
      candidate_box_coverage_percent: null,
      predicted_pothole_pixel_fraction_percent: null,
      unavailable_reason: 'Detector inference is unavailable.',
      limitations: [],
    }} />)

    expect(html).toContain('Detector inference is unavailable.')
  })
})
