import type { DemoRoadRecord } from '../data/demoRoadSegments'
import { scoreTone, travelModes } from '../data/demoRoadSegments'

type DashboardChartsProps = {
  records: DemoRoadRecord[]
}

const qualityBands = [
  { key: 'good', label: 'Good', range: '80–100' },
  { key: 'fair', label: 'Fair', range: '60–79' },
  { key: 'poor', label: 'Poor', range: '40–59' },
  { key: 'critical', label: 'Very poor', range: '0–39' },
  { key: 'unrated', label: 'Unrated', range: '—' },
] as const

export function DashboardCharts({ records }: DashboardChartsProps) {
  const bands = qualityBands.map((band) => ({
    ...band,
    count: records.filter((record) => scoreTone(record.segment.surface_quality_score) === band.key).length,
  }))
  const maxBandCount = Math.max(1, ...bands.map((band) => band.count))
  const modeAverages = travelModes.map((mode) => {
    const values = records
      .map((record) => record.segment.mode_suitability[mode.key])
      .filter((value): value is number => value !== null)
    const average = values.length > 0
      ? Math.round(values.reduce((sum, value) => sum + value, 0) / values.length)
      : null
    return { ...mode, average, count: values.length }
  })

  return (
    <section className="charts-grid" id="insights" aria-label="Network charts">
      <article className="chart-card">
        <div className="chart-heading">
          <div>
            <div className="section-kicker">Surface condition</div>
            <h2>Quality distribution</h2>
          </div>
          <span className="chart-subtitle">{records.length} segments</span>
        </div>
        <div className="quality-chart" role="img" aria-label={`Quality distribution: ${bands.map(({ label, count }) => `${count} ${label}`).join(', ')}`}>
          {bands.map((band) => (
            <div className="quality-bar-row" key={band.key}>
              <div className="quality-bar-label"><span>{band.label}</span><small>{band.range}</small></div>
              <div className="quality-bar-track"><span className={`quality-bar-fill ${band.key}`} style={{ width: `${(band.count / maxBandCount) * 100}%` }} /></div>
              <strong>{band.count}</strong>
            </div>
          ))}
        </div>
        <p className="chart-note">Unrated roads remain separate; missing evidence is never counted as zero quality.</p>
      </article>

      <article className="chart-card">
        <div className="chart-heading">
          <div>
            <div className="section-kicker">Travel profiles</div>
            <h2>Illustrative suitability</h2>
          </div>
          <span className="chart-subtitle">Average of available fixtures</span>
        </div>
        <div className="mode-chart" role="img" aria-label={`Illustrative average profile values: ${modeAverages.map(({ label, average }) => `${label} ${average ?? 'unavailable'}`).join(', ')}`}>
          {modeAverages.map((mode) => (
            <div className="mode-chart-row" key={mode.key}>
              <div className="mode-chart-label"><span>{mode.icon}</span>{mode.shortLabel}</div>
              <div className="mode-bar-track"><span className={`mode-bar-fill ${scoreTone(mode.average)}`} style={{ width: `${mode.average ?? 0}%` }} /></div>
              <strong>{mode.average ?? '—'}</strong>
            </div>
          ))}
        </div>
        <p className="chart-note">Demo-only values. These are not safety ratings or a live Task A score.</p>
      </article>
    </section>
  )
}
