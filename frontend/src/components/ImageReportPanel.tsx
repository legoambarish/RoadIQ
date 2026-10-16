import { useEffect, useState, type ChangeEvent, type DragEvent } from 'react'

type JsonObject = Record<string, unknown>
type TaskCReport = JsonObject & {
  analysis_status: string
  image: JsonObject
  image_quality: JsonObject
  aggregate_analysis: JsonObject
  texture_features: unknown
}

const rsqiComponents = [
  { label: 'Visible defect burden', weight: '35%' },
  { label: 'Aggregate loss', weight: '20%' },
  { label: 'Gap anomaly', weight: '15%' },
  { label: 'Texture anomaly', weight: '15%' },
  { label: 'Aggregate distribution anomaly', weight: '15%' },
]

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

function displayValue(value: unknown): string {
  if (value === null || value === undefined || value === '') return 'Unavailable'
  if (typeof value === 'number') return Number.isFinite(value) ? String(value) : 'Unavailable'
  if (typeof value === 'string' || typeof value === 'boolean') return String(value)
  return 'Available in imported report'
}

function nested(object: unknown, key: string): unknown {
  return isObject(object) ? object[key] : undefined
}

export function ImageReportPanel() {
  const [file, setFile] = useState<File | null>(null)
  const [previewUrl, setPreviewUrl] = useState<string | null>(null)
  const [report, setReport] = useState<TaskCReport | null>(null)
  const [reportName, setReportName] = useState<string | null>(null)
  const [annotationUrl, setAnnotationUrl] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => () => {
    if (previewUrl) URL.revokeObjectURL(previewUrl)
  }, [previewUrl])
  useEffect(() => () => {
    if (annotationUrl?.startsWith('blob:')) URL.revokeObjectURL(annotationUrl)
  }, [annotationUrl])

  const acceptFile = (candidate: File | undefined) => {
    if (!candidate?.type.startsWith('image/')) return
    setFile(candidate)
    setPreviewUrl(URL.createObjectURL(candidate))
  }
  const onFileChange = (event: ChangeEvent<HTMLInputElement>) => acceptFile(event.target.files?.[0])
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
      if (typeof annotation === 'string' && /^data:image\/(jpeg|png|webp);base64,[a-z\d+/=]+$/i.test(annotation)) {
        setAnnotationUrl(annotation)
      } else {
        setAnnotationUrl(null)
      }
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
    }
    event.target.value = ''
  }

  const image = report?.image
  const quality = report?.image_quality
  const aggregateAnalysis = report?.aggregate_analysis
  const surfaceRegion = nested(aggregateAnalysis, 'surface_region')
  const reportedTextureFeatures = nested(report?.texture_features, 'features')
  const textureList = Array.isArray(reportedTextureFeatures) ? reportedTextureFeatures : []
  const sourceName = displayValue(image?.source_name)
  const roiApplied = nested(surfaceRegion, 'road_roi_applied')
  const roiStatus = roiApplied === true
    ? 'Applied · experimental, uncalibrated'
    : roiApplied === false ? 'Not applied' : 'Not reported'
  const runtimeMs = nested(aggregateAnalysis, 'inference_time_ms')

  return (
    <section className="image-report-section" id="image-report" aria-labelledby="image-report-heading">
      <div className="image-report-heading">
        <div>
          <div className="section-kicker">Road inspection</div>
          <h2 id="image-report-heading">Image analysis workspace</h2>
          <p>Preview an image or import a report created by Task C’s local CLI.</p>
        </div>
        <span className="unavailable-tag"><i /> Local report import · no API</span>
      </div>

      <div className="image-report-grid">
        <div className="image-input-card">
          <div className="subsection-heading"><strong>Road image</strong><span>Local preview</span></div>
          {previewUrl || annotationUrl ? (
            <div className="image-preview-frame">
              {previewUrl
                ? <img src={previewUrl} alt="Selected road image preview" />
                : <img src={annotationUrl ?? undefined} alt="Task C annotated texture-candidate preview" />}
              {previewUrl && annotationUrl && <img className="annotation-preview" src={annotationUrl} alt="Task C texture candidate annotation overlay" />}
              {previewUrl && !annotationUrl && <span className="annotation-placeholder">Annotation not imported</span>}
              {annotationUrl && <span className="annotation-label">{previewUrl ? 'Task C annotation overlay' : 'Task C annotated preview'}</span>}
            </div>
          ) : (
            <label className="image-dropzone" htmlFor="road-image-input" onDragOver={(event) => event.preventDefault()} onDrop={onDrop}>
              <input id="road-image-input" type="file" accept="image/*" onChange={onFileChange} />
              <span className="upload-glyph">↑</span>
              <strong>Choose a road image</strong>
              <small>or drag one here to preview locally</small>
              <span className="file-hint">JPEG, PNG, WebP · stays in this browser</span>
            </label>
          )}
          {file && (
            <div className="selected-file-row">
              <span className="file-image-icon">▧</span>
              <span><strong>{file.name}</strong><small>{Math.max(1, Math.round(file.size / 1024))} KB · local preview</small></span>
              <button type="button" onClick={() => { setFile(null); setPreviewUrl(null) }} aria-label="Remove selected image">×</button>
            </div>
          )}
          <label className="report-file-picker" htmlFor="task-c-report-input">
            <span>Import Task C analysis report (.json)</span>
            <small>Loads saved image quality, texture, and candidate-region results. It does not run analysis.</small>
            <input id="task-c-report-input" type="file" accept=".json,application/json" onChange={importReport} />
          </label>
          <label className="report-file-picker" htmlFor="task-c-annotation-input">
            <span>Import annotated preview image (optional)</span>
            <small>Displays Task C’s saved texture-candidate visualization. The CLI report stores a local path, so select this image separately.</small>
            <input id="task-c-annotation-input" type="file" accept="image/jpeg,image/png,image/webp" onChange={importAnnotation} />
          </label>
          <div className="image-status-row"><span>Analysis report</span><strong>{report ? 'Imported · local CLI' : 'Not imported'}</strong></div>
          {error && <p className="report-import-error" role="alert">{error}</p>}
          <p className="image-local-note">The Task C CLI creates both files. Import the JSON to fill the report; import the preview to see its annotation. Neither file picker runs analysis or sends your road image anywhere.</p>
        </div>

        <div className="image-result-card">
          <div className="result-header">
            <div><div className="section-kicker">Analysis report</div><h3>{report ? 'Unrated' : 'No report imported'}</h3></div>
            <span className="unrated-pill">{report ? `TASK C · ${report.analysis_status.toUpperCase()}` : 'RSQI UNAVAILABLE'}</span>
          </div>
          <p className="result-explanation">{report
            ? `Showing fields from ${reportName}. Source image: ${sourceName}. This is a local Task C report; importing it does not rerun analysis.`
            : 'Task C can analyze a local image through its CLI and save structured observations. Import that JSON here to inspect the available results; the browser does not call the CLI or an analysis API.'}</p>
          <div className="pipeline-status-grid" aria-label="Current RoadIQ analysis capabilities">
            <div><span>Task C · local vision</span><strong>{report ? displayValue(nested(report.aggregate_analysis, 'training_status')) : 'CLI MVP available'}</strong><small>Texture-region candidates are not individual aggregate instances.</small></div>
            <div><span>Task A · surface scoring</span><strong>Unrated</strong><small>Required evidence and fixed normalization references are not available.</small></div>
            <div><span>Task D · runtime</span><strong>No image API</strong><small>Dashboard health service does not expose image analysis.</small></div>
          </div>
          <div className="result-index-row"><span>Road Surface Quality Index</span><strong>— <small>/100 · unavailable</small></strong></div>
          <div className="report-evidence-grid">
            <div><span>Source image</span><strong>{report ? sourceName : 'No imported report'}</strong></div>
            <div><span>Image dimensions</span><strong>{report ? `${displayValue(image?.width_px)} × ${displayValue(image?.height_px)} px` : 'Unavailable'}</strong></div>
            <div><span>Image quality usable</span><strong>{report ? displayValue(quality?.usable) : 'Unavailable'}</strong></div>
            <div><span>Quality issues</span><strong>{report && Array.isArray(quality?.issues) ? (quality.issues.length ? quality.issues.join(', ') : 'None reported') : 'Unavailable'}</strong></div>
            <div><span>Texture candidate area</span><strong>{report ? `${displayValue(nested(surfaceRegion, 'candidate_area_ratio'))} ratio` : 'Unavailable'}</strong></div>
            <div><span>Candidate pixels</span><strong>{report ? displayValue(nested(surfaceRegion, 'candidate_area_px')) : 'Unavailable'}</strong></div>
            <div><span>Candidate method</span><strong>{report ? displayValue(nested(aggregateAnalysis, 'method')) : 'Unavailable'}</strong></div>
            <div><span>Analysis path</span><strong>{report ? displayValue(nested(aggregateAnalysis, 'analysis_type')) : 'Unavailable'}</strong></div>
            <div><span>Road region gate</span><strong>{report ? roiStatus : 'Unavailable'}</strong></div>
            <div><span>Candidate confidence</span><strong>{report ? displayValue(nested(surfaceRegion, 'confidence_status')) : 'Unavailable'}</strong></div>
            <div><span>Analysis runtime</span><strong>{report ? `${displayValue(runtimeMs)} ms` : 'Unavailable'}</strong></div>
            <div><span>Texture features</span><strong>{report ? `${textureList.length} reported` : 'Unavailable'}</strong></div>
            <div><span>Aggregate instances</span><strong>{report ? displayValue(nested(nested(report.aggregate_analysis, 'aggregate_count'), 'value')) : 'Unavailable'}</strong></div>
            <div><span>Surface type</span><strong>{report ? displayValue(nested(report.surface_type, 'value')) : 'Unavailable'}</strong></div>
          </div>
          {textureList.length > 0 && <div className="imported-texture-list" aria-label="Imported texture features">
            {textureList.map((item, index) => <div key={index}><strong>{displayValue(nested(item, 'name'))}</strong><span>{displayValue(nested(item, 'value'))} {displayValue(nested(item, 'unit'))}</span></div>)}
          </div>}
          <div className="rsqi-breakdown">
            <div className="rsqi-breakdown-heading"><strong>Candidate RSQI weighting</strong><span>Provisional · not validated</span></div>
            <ul>{rsqiComponents.map((component) => <li key={component.label}><span>{component.label}</span><strong>{component.weight}</strong><small>Contribution unavailable</small></li>)}</ul>
            <p>RSQI = 100 − weighted damage. Missing evidence stays unavailable; weights are not redistributed.</p>
          </div>
          <p className="report-limitation">Texture candidates are not verified pavement, aggregate, or defect segmentation. Pixel measurements are not physical dimensions; image texture is not IRI or physical roughness. The saved CLI annotation path must be supplied above as a file.</p>
        </div>
      </div>
    </section>
  )
}
