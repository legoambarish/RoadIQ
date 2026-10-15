import type { DemoRoadRecord } from '../data/demoRoadSegments'
import { scoreTone, travelModes } from '../data/demoRoadSegments'
import { travelProfileGuides } from '../data/travelProfiles'
import type { PedestrianContext, RoadMeasurements, TravelMode } from '../types/road-segment'

type ModeAssessmentPanelProps = {
  record: DemoRoadRecord
  mode: TravelMode
  view: 'everyday' | 'engineer'
}

function scoreText(value: number | null) {
  return value === null ? '—' : `${Math.round(value)}`
}

function formatMeasurement(measurement: RoadMeasurements[keyof RoadMeasurements]) {
  return measurement.value === null ? 'Unavailable' : `${measurement.value} ${measurement.unit}`
}

function formatPedestrianValue(key: keyof PedestrianContext, value: boolean | number | null) {
  if (value === null) return 'Unknown / not observed'
  if (key === 'footpath_present' || key === 'crossings_observed') return value ? 'Observed present' : 'Observed absent'
  return `${value}/100`
}

function EvidenceLedger({ record, mode }: { record: DemoRoadRecord; mode: TravelMode }) {
  const profile = travelProfileGuides[mode]
  const rows = profile.evidence.map(({ label, field }) => {
    if (field.kind === 'measurement') {
      const measurement = record.segment.measurements[field.key]
      return { label, value: formatMeasurement(measurement), status: measurement.status, source: measurement.source ?? '—' }
    }
    if (field.kind === 'pedestrian') {
      const value = record.segment.pedestrian_context[field.key]
      return { label, value: formatPedestrianValue(field.key, value), status: value === null ? 'unavailable' : 'estimated', source: value === null ? '—' : 'segment contract' }
    }
    if (field.kind === 'confidence') {
      const confidence = record.segment.confidence
      return { label, value: confidence === null ? 'Unavailable' : `${Math.round(confidence * 100)}%`, status: confidence === null ? 'unavailable' : 'uncalibrated', source: 'segment-level field' }
    }
    return { label, value: field.detail, status: 'not represented', source: '—' }
  })

  return (
    <div className="mode-evidence-table-wrap">
      <table className="mode-evidence-table">
        <thead><tr><th scope="col">Signal</th><th scope="col">Current record</th><th scope="col">Status</th><th scope="col">Source</th></tr></thead>
        <tbody>{rows.map((row) => <tr key={row.label}><th scope="row">{row.label}</th><td>{row.value}</td><td><span className={`evidence-status ${row.status.replaceAll(' ', '-')}`}>{row.status}</span></td><td>{row.source}</td></tr>)}</tbody>
      </table>
    </div>
  )
}

function PedestrianContext({ record, view }: { record: DemoRoadRecord; view: 'everyday' | 'engineer' }) {
  const context = record.segment.pedestrian_context
  const unknownCount = Object.values(context).filter((value) => value === null).length
  const fields: { label: string; key: keyof PedestrianContext }[] = [
    { label: 'Footpath', key: 'footpath_present' },
    { label: 'Crossings', key: 'crossings_observed' },
    { label: 'Comfort', key: 'comfort_score' },
  ]

  return (
    <section className={`pedestrian-context-card ${view}`} aria-labelledby="pedestrian-context-heading">
      <div className="mode-panel-heading">
        <div><div className="section-kicker">Separate assessment</div><h3 id="pedestrian-context-heading">Pedestrian infrastructure & comfort</h3></div>
        <span className="data-state-tag">{view === 'everyday' ? (unknownCount ? 'Not observed' : 'Observed') : `${unknownCount} unknown ${unknownCount === 1 ? 'field' : 'fields'}`}</span>
      </div>
      <p>{view === 'everyday'
        ? 'A smooth surface does not prove a comfortable or accessible walk. Sidewalks, crossings, accessible space, and traffic exposure need their own observations.'
        : 'Pedestrian suitability is not derived from RSQI. Lane markings are explicitly excluded as a proxy; traffic exposure and accessible width are not represented in this contract.'}</p>
      <div className="pedestrian-facts">
        {fields.map(({ label, key }) => <div key={key}><span>{label}</span><strong>{formatPedestrianValue(key, context[key])}</strong></div>)}
      </div>
    </section>
  )
}

export function ModeAssessmentPanel({ record, mode, view }: ModeAssessmentPanelProps) {
  const { segment } = record
  const profile = travelProfileGuides[mode]
  const profileLabel = travelModes.find((item) => item.key === mode)?.label ?? mode
  const modeValue = segment.mode_suitability[mode]
  const source = segment.data_provenance.find((item) => item.field_path === 'mode_suitability')?.source ?? 'unavailable'
  const surfaceSource = segment.data_provenance.find((item) => item.field_path === 'surface_quality_score')?.source ?? 'unavailable'

  return (
    <div className={`mode-assessment-panel ${view}`}>
      <div className="assessment-score-grid" aria-label="Separate surface and travel assessments">
        <article className={`assessment-score-card surface-score ${scoreTone(segment.surface_quality_score)}`}>
          <div><span>01 · Surface condition</span><small>{surfaceSource === 'demo_fixture' ? 'Illustrative fixture' : surfaceSource}</small></div>
          <strong>{scoreText(segment.surface_quality_score)}<small>{segment.surface_quality_score === null ? '' : '/100'}</small></strong>
          <p>How damaged or irregular the surface appears. It does not measure route safety.</p>
        </article>
        <article className={`assessment-score-card mode-score ${scoreTone(modeValue)}`}>
          <div><span>02 · {profileLabel} suitability</span><small>{source === 'demo_fixture' ? 'Illustrative fixture' : source}</small></div>
          <strong>{scoreText(modeValue)}<small>{modeValue === null ? '' : '/100'}</small></strong>
          <p>A separate travel-profile assessment. No mode formula is currently agreed.</p>
        </article>
      </div>

      {view === 'everyday' ? (
        <section className="profile-guide everyday" aria-labelledby="profile-guide-heading">
          <div className="mode-panel-heading">
            <div><div className="section-kicker">Traveler brief · {profileLabel}</div><h3 id="profile-guide-heading">{profile.everydayTitle}</h3></div>
            <span className="data-state-tag">Plain language</span>
          </div>
          <p>{profile.everydayDescription}</p>
          <div className="everyday-checks"><strong>What matters for this profile</strong><ul>{profile.everydayChecks.map((check) => <li key={check}>{check}</li>)}</ul></div>
          <p className="fixture-interpretation">The value above is a demonstration fixture, not a route recommendation or safety rating.</p>
        </section>
      ) : (
        <section className="profile-guide engineer" aria-labelledby="profile-guide-heading">
          <div className="mode-panel-heading">
            <div><div className="section-kicker">Profile specification · {profileLabel}</div><h3 id="profile-guide-heading">Evidence and scoring audit</h3></div>
            <span className="data-state-tag">Formula not agreed</span>
          </div>
          <p>{profile.engineerDefinition}</p>
          <EvidenceLedger record={record} mode={mode} />
          <div className="engineer-gates">
            <div><span>Mode value provenance</span><strong>{source}</strong></div>
            <div><span>Calibrated confidence</span><strong>{segment.confidence === null ? 'Unavailable' : `${Math.round(segment.confidence * 100)}%`}</strong></div>
            <div><span>Evidence coverage</span><strong>{segment.evidence_coverage === null ? 'Unavailable' : `${Math.round(segment.evidence_coverage * 100)}%`}</strong></div>
            <div><span>Assessment status</span><strong>{segment.assessment_status} · fixture record</strong></div>
          </div>
          <p className="fixture-interpretation">This audit shows contract fields only. Demo values are not measurements or output from Task A’s scoring service.</p>
        </section>
      )}

      <PedestrianContext record={record} view={view} />
    </div>
  )
}
