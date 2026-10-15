import type { DemoRoadRecord } from '../data/demoRoadSegments'
import { scoreTone, travelModes } from '../data/demoRoadSegments'

type DashboardChartsProps = {
  records: DemoRoadRecord[]
  view: 'everyday' | 'engineer'
}

const qualityBands = [
  { key: 'good', label: 'Good', range: '80–100' },
  { key: 'fair', label: 'Fair', range: '60–79' },
  { key: 'poor', label: 'Poor', range: '40–59' },
  { key: 'critical', label: 'Very poor', range: '0–39' },
  { key: 'unrated', label: 'Unrated', range: '—' },
] as const

function EverydayCharts({ records }: { records: DemoRoadRecord[] }) {
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

  return <>
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
  </>
}

const measurementFields = [
  { key: 'defect_count', label: 'Defect count' },
  { key: 'defect_density', label: 'Defect density' },
  { key: 'damaged_area_ratio', label: 'Damaged area ratio' },
  { key: 'severity', label: 'Severity index' },
  { key: 'roughness_iri', label: 'IRI roughness' },
  { key: 'longitudinal_grade', label: 'Longitudinal grade' },
  { key: 'crossfall', label: 'Crossfall' },
] as const

function EngineerEvidenceCharts({ records }: { records: DemoRoadRecord[] }) {
  const measurements = records.flatMap((record) => Object.values(record.segment.measurements))
  const observed = measurements.filter((measurement) => measurement.status === 'observed').length
  const estimated = measurements.filter((measurement) => measurement.status === 'estimated').length
  const unavailable = measurements.filter((measurement) => measurement.status === 'unavailable').length
  const fixtureValues = measurements.filter((measurement) => measurement.source === 'demo_fixture').length
  const fixtureScores = records.filter((record) => record.segment.data_provenance.some((entry) => entry.field_path === 'surface_quality_score' && entry.source === 'demo_fixture')).length
  const nonFixtureSurfaceValues = records.filter((record) => record.segment.surface_quality_score !== null && !record.segment.data_provenance.some((entry) => entry.field_path === 'surface_quality_score' && entry.source === 'demo_fixture')).length
  const availableModeValues = records.reduce((count, record) => count + Object.values(record.segment.mode_suitability).filter((value) => value !== null).length, 0)
  const pedestrianValues = records.reduce((count, record) => count + Object.values(record.segment.pedestrian_context).filter((value) => value !== null).length, 0)
  const confidenceValues = records.filter((record) => record.segment.confidence !== null).length
  const rows = measurementFields.map(({ key, label }) => {
    const values = records.map((record) => record.segment.measurements[key])
    return {
      key,
      label,
      observed: values.filter((value) => value.status === 'observed').length,
      estimated: values.filter((value) => value.status === 'estimated').length,
      unavailable: values.filter((value) => value.status === 'unavailable').length,
    }
  })

  return <>
    <article className="chart-card evidence-audit-card">
      <div className="chart-heading">
        <div><div className="section-kicker">Engineer · measurement ledger</div><h2>Evidence availability</h2></div>
        <span className="chart-subtitle">{records.length} selected records</span>
      </div>
      <div className="audit-summary-grid">
        <div><span>Observed</span><strong>{observed}</strong></div>
        <div><span>Estimated</span><strong>{estimated}</strong></div>
        <div><span>Unavailable</span><strong>{unavailable}</strong></div>
        <div><span>Fixture values</span><strong>{fixtureValues}</strong></div>
      </div>
      <div className="measurement-audit-table-wrap">
        <table className="measurement-audit-table">
          <thead><tr><th scope="col">Contract field</th><th scope="col">Observed</th><th scope="col">Estimated</th><th scope="col">Unavailable</th></tr></thead>
          <tbody>{rows.map((row) => <tr key={row.key}><th scope="row">{row.label}</th><td>{row.observed}</td><td>{row.estimated}</td><td>{row.unavailable}</td></tr>)}</tbody>
        </table>
      </div>
      <p className="chart-note">Counts reflect the current demo records. Non-null fixture values are not measured evidence.</p>
    </article>

    <article className="chart-card gate-audit-card">
      <div className="chart-heading">
        <div><div className="section-kicker">Scoring separation</div><h2>What this dataset can support</h2></div>
        <span className="chart-subtitle">Availability audit</span>
      </div>
      <div className="gate-audit-list">
        <div><span>Non-fixture surface values</span><strong>{nonFixtureSurfaceValues}</strong><small>The dashboard currently does not call Task A’s scorer.</small></div>
        <div><span>Illustrative surface values</span><strong>{fixtureScores}</strong><small>Fixture rows with a non-null surface value; not model output.</small></div>
        <div><span>Available profile values</span><strong>{availableModeValues}/{records.length * 5}</strong><small>All current mode values are illustrative fixtures; no mode formula is agreed.</small></div>
        <div><span>Pedestrian observations</span><strong>{pedestrianValues}/{records.length * 3}</strong><small>Footpath, crossing, and comfort remain separate from surface quality.</small></div>
        <div><span>Calibrated confidence values</span><strong>{confidenceValues}/{records.length}</strong><small>Null confidence stays unavailable; no confidence calibration is claimed.</small></div>
      </div>
      <p className="chart-note">This view audits provenance and missing-data gates. It is not a model-performance chart.</p>
    </article>
  </>
}

export function DashboardCharts({ records, view }: DashboardChartsProps) {
  return (
    <section className={`charts-grid ${view}`} id="insights" aria-label={view === 'engineer' ? 'Evidence and scoring audit' : 'Everyday network insights'}>
      {view === 'everyday' ? <EverydayCharts records={records} /> : <EngineerEvidenceCharts records={records} />}
    </section>
  )
}
