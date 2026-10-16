import { useEffect, useState, type ChangeEvent, type DragEvent } from 'react'
import { analyzeImage, type ImageAnalysisResult } from '../lib/api'
import { scoreTone } from '../data/demoRoadSegments'

type JsonObject = Record<string, unknown>
type TaskCReport = JsonObject & {
  analysis_status: string
  image: JsonObject
  image_quality: JsonObject
  aggregate_analysis: JsonObject
  texture_features: unknown
}

const rsqiComponents = [
  { key: 'visible_defect_burden', label: 'Visible defect burden', weight: '35%' },
  { key: 'aggregate_loss', label: 'Aggregate loss', weight: '20%' },
  { key: 'gap_anomaly', label: 'Gap anomaly', weight: '15%' },
  { key: 'texture_anomaly', label: 'Texture anomaly', weight: '15%' },
  { key: 'aggregate_distribution_anomaly', label: 'Aggregate distribution anomaly', weight: '15%' },
] as const

const travelModes = [
  { key: 'walking', label: 'Walking' },
  { key: 'cycling', label: 'Cycling' },
  { key: 'two_wheeler', label: 'Two-wheeler' },
  { key: 'car', label: 'Car' },
  { key: 'bus', label: 'Bus' },
] as const

function isObject(value: unknown): value is JsonObject {
  return typeof value === 'object' && value !== null && !Array.isArray(value)
}

function parseReport(value: unknown): TaskCReport {
  if (!isObject(value) || typeof value.analysis_status !== 'string' || !isObject(value.image) ||
    !isObject(value.image_quality) || !isObject(value.aggregate_analysis) || !('texture_features' in value)) {
    throw new Error('This file does not match the Task C analysis-report.json format.')
  }
  return value as TaskCReport
}

function nested(object: unknown, key: string): unknown {
  return isObject(object) ? object[key] : undefined
}

function displayValue(value: unknown): string {
  if (value === null || value === undefined || value === '') return 'Unavailable'
  if (typeof value === 'number') return Number.isFinite(value) ? String(value) : 'Unavailable'
  if (typeof value === 'string' || typeof value === 'boolean') return String(value)
  return 'Available'
}

function describeProcessingError(error: JsonObject): string {
  return typeof error.message === 'string' ? error.message : 'An image-processing step was unavailable.'
}

export function ImageReportPanel() {
  const [file, setFile] = useState<File | null>(null)
  const [previewUrl, setPreviewUrl] = useState<string | null>(null)
  const [report, setReport] = useState<TaskCReport | null>(null)
  const [reportName, setReportName] = useState<string | null>(null)
  const [annotationUrl, setAnnotationUrl] = useState<string | null>(null)
  const [result, setResult] = useState<ImageAnalysisResult | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => () => {
    if (previewUrl) URL.revokeObjectURL(previewUrl)
  }, [previewUrl])
  useEffect(() => () => {
    if (annotationUrl?.startsWith('blob:')) URL.revokeObjectURL(annotationUrl)
  }, [annotationUrl])

  const runEvaluation = async (candidate: File) => {
    setLoading(true)
    setError(null)
    setResult(null)
    try {
      setResult(await analyzeImage(candidate))
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Image analysis request failed.')
    } finally {
      setLoading(false)
    }
  }

  const acceptFile = (candidate: File | undefined) => {
    if (!candidate) return
    if (!candidate.type.startsWith('image/')) {
      setError('Select a JPEG, PNG, or WebP image.')
      return
    }
    setFile(candidate)
    setPreviewUrl(URL.createObjectURL(candidate))
    setAnnotationUrl(null)
    void runEvaluation(candidate)
  }

  const onFileChange = (event: ChangeEvent<HTMLInputElement>) => {
    acceptFile(event.target.files?.[0])
    event.target.value = ''
  }

  const onDrop = (event: DragEvent<HTMLLabelElement>) => {
    event.preventDefault()
    acceptFile(event.dataTransfer.files[0])
  }

  const importReport = async (event: ChangeEvent<HTMLInputElement>) => {
    const selected = event.target.files?.[0]
    if (!selected) return
    try {
      const parsed = parseReport(JSON.parse(await selected.text()) as unknown)
      setReport(parsed)
      setReportName(selected.name)
      setError(null)
      const annotation = nested(parsed.annotated_image, 'value')
      setAnnotationUrl(
        typeof annotation === 'string' &&
          /^data:image\/(jpeg|png|webp);base64,[a-z\d+/=]+$/i.test(annotation)
          ? annotation
          : null,
      )
    } catch (cause) {
      setReport(null)
      setReportName(null)
      setAnnotationUrl(null)
      setError(cause instanceof Error ? cause.message : 'Could not read this report file.')
    }
    event.target.value = ''
  }

  const importAnnotation = (event: ChangeEvent<HTMLInputElement>) => {
    const selected = event.target.files?.[0]
    if (selected && selected.type.startsWith('image/')) {
      setAnnotationUrl(URL.createObjectURL(selected))
      setError(null)
    } else if (selected) {
      setError('Select an image file for the annotation preview.')
    }
    event.target.value = ''
  }

  const clearSelection = () => {
    setFile(null)
    setPreviewUrl(null)
    setResult(null)
    setError(null)
  }

  const reportImage = result?.image ?? report?.image
  const reportQuality = result?.image_quality ?? report?.image_quality
  const reportAggregate = result?.aggregate_analysis ?? report?.aggregate_analysis
  const reportTexture = result?.texture_features ?? report?.texture_features
  const textureFeatures = nested(reportTexture, 'features')
  const textureList = Array.isArray(textureFeatures) ? textureFeatures : []
  const surfaceRegion = nested(reportAggregate, 'surface_region')
  const rsqi = result?.rsqi
  const rsqiValue = rsqi?.value ?? null
  const rsqiStatus = rsqi?.status ?? 'unrated'
  const qualityLabel = result
    ? result.quality_label ?? 'Unrated'
    : report ? 'Unrated' : 'No analysis'
  const analysisTag = loading
    ? 'Analyzing image…'
    : result ? `Backend analysis · ${rsqiStatus}`
    : report ? 'Imported local report · no rescoring'
    : 'Local image analysis'

  return (
    <section className="image-report-section" id="image-report" aria-labelledby="image-report-heading">
      <div className="image-report-heading">
        <div>
          <div className="section-kicker">Road inspection</div>
          <h2 id="image-report-heading">Image analysis workspace</h2>
          <p>Analyze an image through the local backend or inspect a saved Task C report.</p>
        </div>
        <span className="unavailable-tag"><i /> {analysisTag}</span>
      </div>

      <div className="image-report-grid">
        <div className="image-input-card">
          <div className="subsection-heading">
            <strong>Road image</strong>
            <span>{loading ? 'Evaluating…' : previewUrl ? 'Local preview' : 'No image selected'}</span>
          </div>
          {previewUrl || annotationUrl ? (
            <div className="image-preview-frame">
              {previewUrl
                ? <img src={previewUrl} alt="Selected road image preview" />
                : <img src={annotationUrl ?? undefined} alt="Task C annotated texture-candidate preview" />}
              {previewUrl && annotationUrl && (
                <img className="annotation-preview" src={annotationUrl} alt="Imported Task C annotation overlay" />
              )}
              {annotationUrl && (
                <span className="annotation-label">
                  {previewUrl ? 'Imported Task C annotation overlay' : 'Task C annotated preview'}
                </span>
              )}
            </div>
          ) : null}
          <label
            className="image-dropzone"
            htmlFor="road-image-input"
            onDragOver={(event) => event.preventDefault()}
            onDrop={onDrop}
          >
            <input id="road-image-input" type="file" accept="image/jpeg,image/png,image/webp" onChange={onFileChange} />
            <span className="upload-glyph">↑</span>
            <strong>{file ? 'Choose another road image' : 'Choose a road image'}</strong>
            <small>or drag one here to analyze</small>
            <span className="file-hint">JPEG, PNG, WebP · sent to this local RoadIQ app</span>
          </label>
          {file && (
            <div className="selected-file-row">
              <span className="file-image-icon">▧</span>
              <span><strong>{file.name}</strong><small>{Math.max(1, Math.round(file.size / 1024))} KB {loading ? '· analyzing' : ''}</small></span>
              <button type="button" onClick={clearSelection} aria-label="Remove selected image">×</button>
            </div>
          )}
          <label className="report-file-picker" htmlFor="task-c-report-input">
            <span>Import Task C analysis report (.json)</span>
            <small>Inspects saved local observations; importing does not rerun analysis.</small>
            <input id="task-c-report-input" type="file" accept=".json,application/json" onChange={importReport} />
          </label>
          <label className="report-file-picker" htmlFor="task-c-annotation-input">
            <span>Import annotated preview image (optional)</span>
            <small>Displays the saved Task C texture-candidate visualization.</small>
            <input id="task-c-annotation-input" type="file" accept="image/jpeg,image/png,image/webp" onChange={importAnnotation} />
          </label>
          <div className="image-status-row">
            <span>Analysis status</span>
            <strong>{loading ? 'Processing…' : result?.analysis_status ?? (report ? 'Imported local report' : 'Waiting for image')}</strong>
          </div>
          {reportName && <div className="image-status-row"><span>Imported report</span><strong>{reportName}</strong></div>}
          {error && <p className="report-import-error" role="alert">{error}</p>}
          {result?.processing_errors?.map((item, index) => (
            <p className="image-local-note" key={index}>{describeProcessingError(item)}</p>
          ))}
          <p className="image-local-note">
            Uploaded images are analyzed by the local backend. Imported CLI reports and annotations remain local to this browser and do not run analysis.
          </p>
        </div>

        <div className="image-result-card">
          <div className="result-header">
            <div><div className="section-kicker">Analysis report</div><h3>{loading ? 'Evaluating…' : qualityLabel}</h3></div>
            <span className={`quality-chip ${scoreTone(rsqiValue)}`}>
              {loading ? 'ANALYZING' : result ? result.quality_label ?? rsqiStatus.toUpperCase() : report ? 'UNRATED' : 'WAITING'}
            </span>
          </div>
          <p className="result-explanation">
            {result?.rsqi?.explanation ??
              (report
                ? `Showing saved fields from ${reportName ?? 'the Task C report'}. Importing a report does not calculate RSQI.`
                : 'Current image observations do not establish all required RSQI components and fixed normalization references. The scorer will report Unrated rather than infer missing evidence.')}
          </p>
          <div className="result-index-row">
            <span>Road Surface Quality Index</span>
            <strong>{rsqiValue === null ? '—' : rsqiValue.toFixed(1)} <small>/100</small></strong>
          </div>

          <div className="report-evidence-grid">
            <div><span>Source image</span><strong>{file?.name ?? displayValue(nested(reportImage, 'source_name'))}</strong></div>
            <div><span>Image dimensions</span><strong>
              {result?.image?.size_px
                ? `${result.image.size_px[0]} × ${result.image.size_px[1]} px`
                : report
                  ? `${displayValue(nested(reportImage, 'width_px'))} × ${displayValue(nested(reportImage, 'height_px'))} px`
                  : 'Unavailable'}
            </strong></div>
            <div><span>Image quality usable</span><strong>{displayValue(nested(reportQuality, 'usable'))}</strong></div>
            <div><span>Quality issues</span><strong>
              {Array.isArray(nested(reportQuality, 'issues'))
                ? (nested(reportQuality, 'issues') as string[]).join(', ') || 'None reported'
                : 'Unavailable'}
            </strong></div>
            <div><span>Texture candidate area</span><strong>{displayValue(nested(surfaceRegion, 'candidate_area_ratio'))}</strong></div>
            <div><span>Candidate method</span><strong>{displayValue(nested(reportAggregate, 'method'))}</strong></div>
            <div><span>Surface type</span><strong>{displayValue(nested(result?.surface_type ?? report?.surface_type, 'value'))}</strong></div>
            <div><span>Scoring version</span><strong>{result?.scoring_version ?? 'Unavailable'}</strong></div>
          </div>

          {textureList.length > 0 && (
            <div className="imported-texture-list" aria-label="Reported texture features">
              {textureList.map((item, index) => (
                <div key={index}>
                  <strong>{displayValue(nested(item, 'name'))}</strong>
                  <span>{displayValue(nested(item, 'value'))} {displayValue(nested(item, 'unit'))}</span>
                </div>
              ))}
            </div>
          )}

          <div className="rsqi-breakdown">
            <div className="rsqi-breakdown-heading">
              <strong>RSQI component breakdown</strong>
              <span>{result ? 'Scorer output' : 'Unavailable until analyzed'}</span>
            </div>
            <ul>
              {rsqiComponents.map((component) => {
                const data = rsqi?.components?.[component.key]
                return (
                  <li key={component.key}>
                    <span>{component.label}</span>
                    <strong>{component.weight}</strong>
                    <small>{data?.value == null ? data?.status ?? 'Unavailable' : `Damage: ${data.value.toFixed(1)} / 100`}</small>
                  </li>
                )
              })}
            </ul>
            <p>Visible-defect score guardrails apply to normalized evidence. Missing evidence is not treated as zero.</p>
          </div>

          <div className="profile-list" style={{ marginTop: '14px', marginBottom: '14px' }}>
            <div className="subsection-heading"><strong>Travel mode suitability</strong><span>Not scored</span></div>
            {travelModes.map((mode) => (
              <div className="profile-row" key={mode.key}>
                <span className="profile-name">{mode.label}</span>
                <div className="profile-track"><span className="profile-fill" style={{ width: '0%' }} /></div>
                <strong>{displayValue(result?.mode_suitability?.[mode.key])}</strong>
              </div>
            ))}
          </div>
          <p className="report-limitation">
            Texture candidates are not verified pavement, aggregate, or defect segmentation. Image texture is not physical roughness or IRI. Confidence and mode-suitability formulas remain unavailable.
          </p>
        </div>
      </div>
    </section>
  )
}
