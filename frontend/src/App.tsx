import { useEffect, useMemo, useState } from 'react'
import './App.css'
import { DashboardCharts } from './components/DashboardCharts'
import { ImageReportPanel } from './components/ImageReportPanel'
import { SegmentMap } from './components/SegmentMap'
import { demoRoadRecords, getOverlayValue, overlayLabel, scoreTone, travelModes, type DemoRoadRecord, type OverlayKey } from './data/demoRoadSegments'
import { fetchHealth } from './lib/api'
import type { QualityLabel, RoadSegment } from './types/road-segment'

type DashboardView = 'everyday' | 'engineer'
type HealthStatus = 'loading' | 'ok' | 'error'

const qualityOptions: { value: QualityLabel | 'unrated'; label: string }[] = [
  { value: 'Good', label: 'Good · 80–100' },
  { value: 'Fair', label: 'Fair · 60–79' },
  { value: 'Poor', label: 'Poor · 40–59' },
  { value: 'Very Poor', label: 'Very poor · 0–39' },
  { value: 'unrated', label: 'Unrated' },
]

const qualityLabel = (segment: RoadSegment) => segment.quality_label ?? 'Unrated'

function formatScore(value: number | null): string {
  return value === null ? '—' : `${Math.round(value)}`
}

function formatDate(value: string): string {
  return new Date(value).toLocaleDateString('en', { day: '2-digit', month: 'short', year: 'numeric' })
}

function HealthBadge({ status }: { status: HealthStatus }) {
  const label = status === 'ok' ? 'API online · health only' : status === 'error' ? 'API offline · demo mode' : 'Checking API…'
  return <span className={`health-badge ${status}`}><i />{label}</span>
}

function MetricCard({ label, value, detail, icon, tone = '' }: { label: string; value: string; detail: string; icon: string; tone?: string }) {
  return (
    <article className={`metric-card ${tone}`}>
      <div className="metric-topline"><span>{label}</span><span className="metric-icon" aria-hidden="true">{icon}</span></div>
      <strong>{value}</strong>
      <small>{detail}</small>
    </article>
  )
}

function SegmentDetail({ record, view, overlay }: { record: DemoRoadRecord; view: DashboardView; overlay: OverlayKey }) {
  const { segment } = record
  const qualityTone = scoreTone(segment.surface_quality_score)
  const activeValue = getOverlayValue(record, overlay)

  return (
    <section className="detail-card" aria-labelledby="detail-heading">
      <div className="detail-heading-row">
        <div>
          <div className="section-kicker">Selected segment</div>
          <h2 id="detail-heading">{record.roadName}</h2>
          <p className="detail-subtitle">{record.area} <span>·</span> {segment.segment_id}</p>
        </div>
        <span className={`quality-chip ${qualityTone}`}>{qualityLabel(segment)}</span>
      </div>

      <div className={`detail-score ${qualityTone}`}>
        <div>
          <span>{overlay === 'surface_quality_score' ? 'Road quality' : `${overlayLabel(overlay)} profile`}</span>
          <small>{segment.assessment_status === 'unrated' ? 'No assessment available' : 'Illustrative demo score · out of 100'}</small>
        </div>
        <strong>{activeValue === null ? '—' : Math.round(activeValue)}<small>{activeValue === null ? '' : '/100'}</small></strong>
      </div>

      <p className="detail-note">{record.note}</p>

      <div className="profile-list">
        <div className="subsection-heading"><strong>Travel profiles</strong><span>Illustrative fixtures</span></div>
        {travelModes.map((mode) => {
          const value = segment.mode_suitability[mode.key]
          return (
            <div className="profile-row" key={mode.key}>
              <span className="profile-name"><i>{mode.icon}</i>{mode.label}</span>
              <div className="profile-track"><span className={`profile-fill ${scoreTone(value)}`} style={{ width: `${value ?? 0}%` }} /></div>
              <strong>{value === null ? '—' : Math.round(value)}</strong>
            </div>
          )
        })}
      </div>

      {view === 'everyday' ? (
        <div className="everyday-callout">
          <span className="callout-icon">i</span>
          <p>Condition and travel suitability are separate. These demo values do not establish safety or accessibility.</p>
        </div>
      ) : (
        <div className="engineer-detail">
          <div className="subsection-heading"><strong>Evidence & provenance</strong><span>Contract fields</span></div>
          <div className="evidence-grid">
            <div><span>Assessment</span><strong>{segment.assessment_status}</strong></div>
            <div><span>Surveyed</span><strong>{formatDate(segment.surveyed_at)}</strong></div>
            <div><span>Confidence</span><strong>{segment.confidence === null ? 'Unavailable' : `${Math.round(segment.confidence * 100)}%`}</strong></div>
            <div><span>Coverage</span><strong>{segment.evidence_coverage === null ? 'Unavailable' : `${Math.round(segment.evidence_coverage * 100)}%`}</strong></div>
            <div><span>Defects / image</span><strong>{segment.measurements.defect_count.value ?? 'Unavailable'}</strong></div>
            <div><span>IRI / roughness</span><strong>{segment.measurements.roughness_iri.value === null ? 'Unavailable' : `${segment.measurements.roughness_iri.value} m/km`}</strong></div>
          </div>
          <div className="provenance-note"><strong>Source:</strong> {segment.survey_source}. Numeric demo values are illustrative only; no live segment API is connected.</div>
          <div className="component-strip" aria-label="Illustrative damage component values">
            {Object.entries(segment.damage_components).map(([key, value]) => (
              <span key={key}><small>{key.replaceAll('_', ' ')}</small><strong>{value === null ? '—' : `${Math.round(value)}`}</strong></span>
            ))}
          </div>
          <p className="chart-note">Component values are arbitrary UI fixtures; they are not produced by Task A’s scoring engine.</p>
        </div>
      )}

      <div className="detail-footer"><span>Geometry: GeoJSON LineString</span><span>Source tag: demo_fixture</span></div>
    </section>
  )
}

function App() {
  const [view, setView] = useState<DashboardView>('everyday')
  const [overlay, setOverlay] = useState<OverlayKey>('surface_quality_score')
  const [search, setSearch] = useState('')
  const [qualityFilter, setQualityFilter] = useState('all')
  const [minimumScore, setMinimumScore] = useState('all')
  const [selectedId, setSelectedId] = useState(demoRoadRecords[0].segment.segment_id)
  const [healthStatus, setHealthStatus] = useState<HealthStatus>('loading')

  useEffect(() => {
    const controller = new AbortController()
    fetchHealth(controller.signal)
      .then(() => setHealthStatus('ok'))
      .catch(() => setHealthStatus('error'))
    return () => controller.abort()
  }, [])

  const filteredRecords = useMemo(() => {
    const query = search.trim().toLocaleLowerCase()
    return demoRoadRecords.filter((record) => {
      const matchesSearch = !query
        || record.roadName.toLocaleLowerCase().includes(query)
        || record.segment.segment_id.toLocaleLowerCase().includes(query)
      const matchesQuality = qualityFilter === 'all'
        || (qualityFilter === 'unrated' ? record.segment.assessment_status === 'unrated' : record.segment.quality_label === qualityFilter)
      const value = getOverlayValue(record, overlay)
      const matchesMinimum = minimumScore === 'all' || (value !== null && value >= Number(minimumScore))
      return matchesSearch && matchesQuality && matchesMinimum
    })
  }, [search, qualityFilter, minimumScore, overlay])

  const selectedRecord = filteredRecords.find((record) => record.segment.segment_id === selectedId) ?? filteredRecords[0]
  const rankedRecords = [...filteredRecords].sort((left, right) => {
    const leftValue = getOverlayValue(left, overlay)
    const rightValue = getOverlayValue(right, overlay)
    if (leftValue === null && rightValue === null) return left.roadName.localeCompare(right.roadName)
    if (leftValue === null) return 1
    if (rightValue === null) return -1
    return rightValue - leftValue
  })
  const ratedRecords = filteredRecords.filter((record) => record.segment.surface_quality_score !== null)
  const averageQuality = ratedRecords.length > 0
    ? Math.round(ratedRecords.reduce((sum, record) => sum + (record.segment.surface_quality_score ?? 0), 0) / ratedRecords.length)
    : null
  const reviewCount = ratedRecords.filter((record) => (record.segment.surface_quality_score ?? 100) < 60).length
  const summaryCards = view === 'engineer'
    ? [
        { label: 'Segment records', value: `${filteredRecords.length}`, detail: 'Illustrative fixture rows', icon: '▤' },
        { label: 'Rated examples', value: `${ratedRecords.length}`, detail: 'Not scorer output', icon: '◒', tone: 'metric-green' },
        { label: 'Confidence fields', value: 'Unavailable', detail: 'No verified evidence source', icon: '∅', tone: 'metric-muted' },
        { label: 'Record provenance', value: 'demo_fixture', detail: 'No live segment API', icon: '⌁', tone: 'metric-amber' },
      ]
    : [
        { label: 'Roads in view', value: `${filteredRecords.length}`, detail: 'Illustrative segments', icon: '⌁' },
        { label: 'Average road quality', value: averageQuality === null ? '—' : `${averageQuality}`, detail: 'Rated fixtures only · /100', icon: '◒', tone: 'metric-green' },
        { label: 'Need a closer look', value: `${reviewCount}`, detail: 'Demo scores below 60', icon: '↗', tone: 'metric-amber' },
        { label: 'Evidence coverage', value: 'Unavailable', detail: 'No live survey feed connected', icon: '◌', tone: 'metric-muted' },
      ]

  const chooseSegment = (segmentId: string) => setSelectedId(segmentId)

  return (
    <main className={`app-shell ${view === 'engineer' ? 'engineer-view' : 'everyday-view'}`}>
      <header className="topbar">
        <a className="brand" href="#top" aria-label="RoadIQ home">
          <span className="brand-mark"><i /><i /><i /></span>
          <span>road<span>iq</span></span>
        </a>
        <nav className="primary-nav" aria-label="Main navigation">
          <a className="active" href="#network">Network</a>
          <a href="#insights">Insights</a>
          <a href="#image-report">Image report</a>
        </nav>
        <div className="topbar-right">
          <HealthBadge status={healthStatus} />
          <button className="avatar-button" type="button" aria-label="Demo account">D</button>
        </div>
      </header>

      <div className="page-content" id="top">
        <section className="page-heading">
          <div>
            <div className="eyebrow-line"><span className="live-dot" /> {view === 'engineer' ? 'ENGINEERING CONSOLE' : 'ROAD NETWORK INTELLIGENCE'} <span className="eyebrow-divider">/</span> DEMO WORKSPACE</div>
            <h1>{view === 'engineer' ? <>Inspect the <em>evidence.</em></> : <>Know the road <em>ahead.</em></>}</h1>
            <p>{view === 'engineer' ? 'Review record provenance, measurement availability, and contract fields for each fixture.' : 'Compare route examples and see how condition differs from travel-profile suitability.'}</p>
          </div>
          <div className="view-switch" role="group" aria-label="Dashboard view">
            <button type="button" className={view === 'everyday' ? 'selected' : ''} aria-pressed={view === 'everyday'} onClick={() => setView('everyday')}><span>◉</span> Everyday</button>
            <button type="button" className={view === 'engineer' ? 'selected' : ''} aria-pressed={view === 'engineer'} onClick={() => setView('engineer')}><span>⌘</span> Engineer</button>
          </div>
        </section>

        <section className="demo-notice" role="note">
          <span className="notice-icon">✳</span>
          <p><strong>Demo data:</strong> this workspace uses illustrative fixtures. The API currently exposes health status only; road scores and travel profiles below are not live measurements or safety ratings.</p>
          <span className="notice-tag">FIXTURE DATA</span>
        </section>

        <section className="workspace-section" id="network">
          <div className="section-toolbar">
            <div className="overlay-switch" role="group" aria-label="Map overlay">
              <button type="button" className={overlay === 'surface_quality_score' ? 'active' : ''} aria-pressed={overlay === 'surface_quality_score'} onClick={() => setOverlay('surface_quality_score')}>Road quality</button>
              {travelModes.map((mode) => (
                <button type="button" key={mode.key} className={overlay === mode.key ? 'active' : ''} aria-pressed={overlay === mode.key} onClick={() => setOverlay(mode.key)}><span>{mode.icon}</span>{mode.shortLabel}</button>
              ))}
            </div>
            <div className="filter-controls">
              <label className="search-field"><span aria-hidden="true">⌕</span><input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Search a road or ID" aria-label="Search road segments" /><kbd>⌘ K</kbd></label>
              <label className="select-field"><span className="sr-only">Filter by quality label</span><select value={qualityFilter} onChange={(event) => setQualityFilter(event.target.value)}><option value="all">All quality</option>{qualityOptions.map((option) => <option key={option.value} value={option.value}>{option.label}</option>)}</select></label>
              <label className="select-field"><span className="sr-only">Minimum active overlay value</span><select value={minimumScore} onChange={(event) => setMinimumScore(event.target.value)}><option value="all">Any score</option><option value="60">60+ only</option><option value="80">80+ only</option></select></label>
            </div>
          </div>

          <div className="main-grid">
            <SegmentMap records={filteredRecords} selectedId={selectedRecord?.segment.segment_id ?? ''} overlay={overlay} onSelect={chooseSegment} />

            <aside className="ranking-card" aria-labelledby="ranking-heading">
              <div className="ranking-header">
                <div><div className="section-kicker">Ranked segments</div><h2 id="ranking-heading">Top roads</h2></div>
                <span className="ranking-sort">↓ {overlayLabel(overlay)}</span>
              </div>
              {rankedRecords.length > 0 ? (
                <ol className="ranking-list">
                  {rankedRecords.map((record, index) => {
                    const value = getOverlayValue(record, overlay)
                    const active = record.segment.segment_id === selectedRecord?.segment.segment_id
                    return (
                      <li key={record.segment.segment_id}>
                        <button type="button" className={`ranking-row ${active ? 'active' : ''}`} onClick={() => chooseSegment(record.segment.segment_id)} aria-pressed={active}>
                          <span className="rank-number">{String(index + 1).padStart(2, '0')}</span>
                          <span className={`rank-indicator ${scoreTone(value)}`} />
                          <span className="rank-copy"><strong>{record.roadName}</strong><small>{record.segment.segment_id} · {qualityLabel(record.segment)}</small></span>
                          <strong className={`rank-score ${value === null ? 'unrated' : ''}`}>{formatScore(value)}</strong>
                        </button>
                      </li>
                    )
                  })}
                </ol>
              ) : (
                <div className="empty-list"><span>⌕</span><strong>No matching segments</strong><small>Try clearing a filter.</small></div>
              )}
              <div className="ranking-footer"><span>Ranked by active overlay</span><span>Fixtures only</span></div>
            </aside>
          </div>
        </section>

        <section className="metrics-grid" aria-label={view === 'engineer' ? 'Record inspection summary' : 'Network summary'}>
          {summaryCards.map((card) => <MetricCard key={card.label} {...card} />)}
        </section>

        <ImageReportPanel />

        {selectedRecord ? (
          <section className="insight-grid" aria-label="Segment details and insights">
            <SegmentDetail record={selectedRecord} view={view} overlay={overlay} />
            <DashboardCharts records={filteredRecords} />
          </section>
        ) : (
          <section className="filtered-empty"><strong>No segment selected</strong><span>Adjust your filters to explore the demo network.</span></section>
        )}

        <footer className="app-footer">
          <span>ROADIQ <i>·</i> PROTOTYPE DASHBOARD</span>
          <span>Condition is not a safety certification. Confirm access and local guidance before travel.</span>
        </footer>
      </div>
    </main>
  )
}

export default App
