import { describe, expect, it } from 'vitest'
import { dashboardSectionForHash } from './dashboardNavigation'

describe('dashboard navigation state', () => {
  it('selects the section matching the current URL hash', () => {
    expect(dashboardSectionForHash('#network')).toBe('network')
    expect(dashboardSectionForHash('#insights')).toBe('insights')
    expect(dashboardSectionForHash('#image-report')).toBe('image-report')
  })

  it('defaults to Network for the home page or an unknown hash', () => {
    expect(dashboardSectionForHash('')).toBe('network')
    expect(dashboardSectionForHash('#top')).toBe('network')
    expect(dashboardSectionForHash('#unknown')).toBe('network')
  })
})
