import { useEffect, useState, useCallback, type ChangeEvent, type DragEvent } from 'react'
import { analyzeImage, type ImageAnalysisResult } from '../lib/api'
import { scoreTone } from '../data/demoRoadSegments'

const rsqiComponentsConfig = [
  { key: 'visible_defect_burden', label: 'Visible defect burden', weight: '35%' },
  { key: 'aggregate_loss', label: 'Aggregate loss', weight: '20%' },
  { key: 'gap_anomaly', label: 'Gap anomaly', weight: '15%' },
  { key: 'texture_anomaly', label: 'Texture anomaly', weight: '15%' },
  { key: 'aggregate_distribution_anomaly', label: 'Aggregate distribution anomaly', weight: '15%' },
]

const travelModeItems = [
  { key: 'walking', label: 'Walking', icon: '↗' },
  { key: 'cycling', label: 'Cycling', icon: '◉' },
  { key: 'two_wheeler', label: 'Two-wheeler', icon: '⌁' },
  { key: 'car', label: 'Car', icon: '▰' },
  { key: 'bus', label: 'Bus', icon: '▥' },
] as const

export function ImageReportPanel() {
  const [file, setFile] = useState<File | null>(null)
  const [previewUrl, setPreviewUrl] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [result, setResult] = useState<ImageAnalysisResult | null>(null)

  useEffect(() => () => {
    if (previewUrl && !previewUrl.startsWith('data:')) {
      URL.revokeObjectURL(previewUrl)
    }
  }, [previewUrl])

  const runEvaluation = useCallback(async (selectedFile: File) => {
    setLoading(true)
    setError(null)
    setResult(null)
    try {
      const data = await analyzeImage(selectedFile)
      setResult(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Evaluation request failed.')
    } finally {
      setLoading(false)
    }
  }, [])

  const acceptFile = (candidate: File | undefined) => {
    if (!candidate?.type.startsWith('image/')) return
    setFile(candidate)
    setPreviewUrl(URL.createObjectURL(candidate))
    runEvaluation(candidate)
  }

  const onFileChange = (event: ChangeEvent<HTMLInputElement>) => acceptFile(event.target.files?.[0])
  const onDrop = (event: DragEvent<HTMLLabelElement>) => {
    event.preventDefault()
    acceptFile(event.dataTransfer.files[0])
  }

  const clearSelection = () => {
    setFile(null)
    setPreviewUrl(null)
    setResult(null)
    setError(null)
    setLoading(false)
  }

  const rsqi = result?.rsqi
  const rsqiValue = rsqi?.value
  const rsqiStatus = rsqi?.status ?? 'unrated'
  const qualityLabel = rsqi?.quality_label ?? (rsqiStatus === 'rated' ? 'Rated' : 'Unrated')
  const overlayUrl = result?.annotated_image?.value
  const modes = result?.mode_suitability

  const isUsable = result?.image_quality?.usable

  return (
    <section className="image-report-section" id="image-report" aria-labelledby="image-report-heading">
      <div className="image-report-heading">
        <div>
          <div className="section-kicker">Road inspection</div>
          <h2 id="image-report-heading">Image analysis workspace</h2>
          <p>Upload a road surface image to analyze pavement condition, compute RSQI, and evaluate vehicle mode suitability.</p>
        </div>
        <span className="unavailable-tag">
          <i />{' '}
          {loading
            ? 'Analyzing image…'
            : result
            ? `Analysis complete · ${rsqiStatus}`
            : 'Analysis API connected'}
        </span>
      </div>

      <div className="image-report-grid">
        <div className="image-input-card">
          <div className="subsection-heading">
            <strong>Road image</strong>
            <span>{loading ? 'Evaluating…' : result ? 'Analyzed' : 'Upload ready'}</span>
          </div>
          {previewUrl ? (
            <div className="image-preview-frame">
              <img src={overlayUrl || previewUrl} alt="Selected road surface preview" />
              {loading && <span className="annotation-placeholder">Evaluating road features…</span>}
              {!loading && overlayUrl && (
                <span className="annotation-placeholder" style={{ background: 'rgba(0,0,0,0.6)', color: '#38bdf8' }}>
                  Overlay applied
                </span>
              )}
            </div>
          ) : (
            <label className="image-dropzone" htmlFor="road-image-input" onDragOver={(event) => event.preventDefault()} onDrop={onDrop}>
              <input id="road-image-input" type="file" accept="image/*" onChange={onFileChange} />
              <span className="upload-glyph">↑</span>
              <strong>Choose a road image</strong>
              <small>or drag one here to evaluate</small>
              <span className="file-hint">JPEG, PNG, WebP · Evaluated on backend</span>
            </label>
          )}
          {file && (
            <div className="selected-file-row">
              <span className="file-image-icon">▧</span>
              <span>
                <strong>{file.name}</strong>
                <small>{Math.max(1, Math.round(file.size / 1024))} KB {loading ? '· Evaluating' : ''}</small>
              </span>
              <button type="button" onClick={clearSelection} aria-label="Remove selected image">×</button>
            </div>
          )}
          <div className="image-status-row">
            <span>Inference status</span>
            <strong>
              {loading
                ? 'Processing…'
                : result
                ? `${result.analysis_status} (${result.analysis_id})`
                : file
                ? 'Ready'
                : 'Waiting for image'}
            </strong>
          </div>
          {error && (
            <p className="image-local-note" style={{ color: '#ef4444' }}>
              <strong>Error:</strong> {error}
            </p>
          )}
          {!error && !result && (
            <p className="image-local-note">Select an image to transmit it to the backend for quality, texture, and RSQI scoring.</p>
          )}
          {result?.processing_errors && result.processing_errors.length > 0 && (
            <p className="image-local-note" style={{ color: '#f59e0b' }}>
              {result.processing_errors.join('; ')}
            </p>
          )}
        </div>

        <div className="image-result-card">
          <div className="result-header">
            <div>
              <div className="section-kicker">Analysis report</div>
              <h3>{loading ? 'Evaluating…' : qualityLabel}</h3>
            </div>
            <span className={`quality-chip ${scoreTone(rsqiValue ?? null)}`}>
              {loading ? 'ANALYZING' : result ? (rsqi?.quality_label ?? rsqiStatus.toUpperCase()) : 'WAITING'}
            </span>
          </div>

          <p className="result-explanation">
            {rsqi?.explanation ||
              'Upload a road surface image to calculate defect burdens, texture contrast proxies, and provisional RSQI score.'}
          </p>

          <div className="result-index-row">
            <span>Road Surface Quality Index</span>
            <strong>
              {rsqiValue !== null && rsqiValue !== undefined ? rsqiValue.toFixed(1) : '—'}{' '}
              <small>/100</small>
            </strong>
          </div>

          {/* Travel Profiles Suitability Section */}
          <div className="profile-list" style={{ marginTop: '14px', marginBottom: '14px' }}>
            <div className="subsection-heading">
              <strong>Travel mode suitability</strong>
              <span>Relative score</span>
            </div>
            {travelModeItems.map((mode) => {
              const val = modes ? modes[mode.key] : null
              return (
                <div className="profile-row" key={mode.key}>
                  <span className="profile-name">
                    <i>{mode.icon}</i>
                    {mode.label}
                  </span>
                  <div className="profile-track">
                    <span
                      className={`profile-fill ${scoreTone(val)}`}
                      style={{ width: `${val ?? 0}%` }}
                    />
                  </div>
                  <strong>{val === null || val === undefined ? '—' : Math.round(val)}</strong>
                </div>
              )
            })}
          </div>

          <div className="report-evidence-grid">
            <div>
              <span>Image quality / pavement</span>
              <strong>
                {result
                  ? isUsable
                    ? 'Quality gate passed'
                    : 'Low confidence / crop'
                  : 'Not analyzed'}
              </strong>
            </div>
            <div>
              <span>Surface type</span>
              <strong>
                {result
                  ? String(result.surface_type?.value ?? 'asphalt_bituminous')
                  : 'Not classified'}
              </strong>
            </div>
            <div>
              <span>Stone aggregates</span>
              <strong>
                {result?.aggregate_analysis?.surface_region
                  ? `Candidate ratio: ${(result.aggregate_analysis.surface_region.candidate_area_ratio ?? 0).toFixed(3)}`
                  : 'No validated model'}
              </strong>
            </div>
            <div>
              <span>Metal fragments</span>
              <strong>Separate target · unavailable</strong>
            </div>
            <div>
              <span>Defects / texture proxies</span>
              <strong>
                {result?.texture_features?.features?.length
                  ? `Contrast: ${result.texture_features.features[0].value?.toFixed(1) ?? '—'}`
                  : 'Not connected'}
              </strong>
            </div>
            <div>
              <span>Confidence / coverage</span>
              <strong>
                {overlayUrl ? 'Visual overlay available' : 'Standard proxy'}
              </strong>
            </div>
          </div>

          <div className="rsqi-breakdown">
            <div className="rsqi-breakdown-heading">
              <strong>RSQI component breakdown</strong>
              <span>{result ? 'Calibrated evaluation' : 'Candidate RSQI weighting'}</span>
            </div>
            <ul>
              {rsqiComponentsConfig.map((component) => {
                const compData = rsqi?.components?.[component.key]
                const compVal = compData?.value
                const compStatus = compData?.status
                return (
                  <li key={component.key}>
                    <span>{component.label}</span>
                    <strong>{component.weight}</strong>
                    <small>
                      {compVal !== null && compVal !== undefined
                        ? `Damage: ${compVal.toFixed(1)} / 100`
                        : compStatus === 'unavailable'
                        ? 'Unavailable'
                        : compStatus || 'Contribution unavailable'}
                    </small>
                  </li>
                )
              })}
            </ul>
            <p>RSQI = 100 − weighted damage. Missing evidence stays unavailable; weights are not redistributed.</p>
          </div>

          {rsqi?.limitations && rsqi.limitations.length > 0 ? (
            <p className="report-limitation">
              {rsqi.limitations[0]}
            </p>
          ) : (
            <p className="report-limitation">
              Image texture is not physical roughness or IRI. A 2D image cannot establish strength, skid resistance, or travel safety.
            </p>
          )}
        </div>
      </div>
    </section>
  )
}
