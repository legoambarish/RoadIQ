export type DashboardSection = 'network' | 'insights' | 'image-report'

const dashboardSections = new Set<DashboardSection>(['network', 'insights', 'image-report'])

export function dashboardSectionForHash(hash: string): DashboardSection {
  const section = hash.replace(/^#/, '') as DashboardSection
  return dashboardSections.has(section) ? section : 'network'
}
