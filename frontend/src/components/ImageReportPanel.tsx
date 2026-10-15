import { useEffect, useState, type ChangeEvent, type DragEvent } from 'react'

const rsqiComponents = [
  { label: 'Visible defect burden', weight: '35%' },
  { label: 'Aggregate loss', weight: '20%' },
  { label: 'Gap anomaly', weight: '15%' },
  { label: 'Texture anomaly', weight: '15%' },
  { label: 'Aggregate distribution anomaly', weight: '15%' },
]

export function ImageReportPanel() {
  const [file, setFile] = useState<File | null>(null)
  const [previewUrl, setPreviewUrl] = useState<string | null>(null)

  useEffect(() => () => {
    if (previewUrl) URL.revokeObjectURL(previewUrl)
  }, [previewUrl])

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

  return (
    <section className="image-report-section" id="image-report" aria-labelledby="image-report-heading">
      <div className="image-report-heading">
        <div>
          <div className="section-kicker">Road inspection</div>
          <h2 id="image-report-heading">Image analysis workspace</h2>
          <p>Preview an image and review what the current local analysis and scoring services can provide.</p>
        </div>
        <span className="unavailable-tag"><i /> Analysis API unavailable</span>
      </div>

      <div className="image-report-grid">
        <div className="image-input-card">
          <div className="subsection-heading"><strong>Road image</strong><span>Local preview only</span></div>
          {previewUrl ? (
            <div className="image-preview-frame">
              <img src={previewUrl} alt="Selected road image preview" />
              <span className="annotation-placeholder">Annotation unavailable</span>
            </div>
          ) : (
            <label className="image-dropzone" htmlFor="road-image-input" onDragOver={(event) => event.preventDefault()} onDrop={onDrop}>
              <input id="road-image-input" type="file" accept="image/*" onChange={onFileChange} />
              <span className="upload-glyph">↑</span>
              <strong>Choose a road image</strong>
              <small>or drag one here to preview locally</small>
              <span className="file-hint">JPEG, PNG, WebP · no upload occurs</span>
            </label>
          )}
          {file && (
            <div className="selected-file-row">
              <span className="file-image-icon">▧</span>
              <span><strong>{file.name}</strong><small>{Math.max(1, Math.round(file.size / 1024))} KB · local preview</small></span>
              <button type="button" onClick={() => { setFile(null); setPreviewUrl(null) }} aria-label="Remove selected image">×</button>
            </div>
          )}
          <div className="image-status-row"><span>Inference status</span><strong>{file ? 'Not run' : 'Waiting for image'}</strong></div>
          <p className="image-local-note">Files stay in this browser preview. Selecting an image does not send it to the local CLI or run analysis.</p>
        </div>

        <div className="image-result-card">
          <div className="result-header">
            <div><div className="section-kicker">Analysis report</div><h3>Unrated</h3></div>
            <span className="unrated-pill">SCORER NOT CONNECTED</span>
          </div>
          <p className="result-explanation">This file is preview-only; no analysis ran. Task C provides a local CLI MVP with image-quality observations, a named texture proxy, and an untrained texture-region candidate annotation. Task A provides an evidence-gated scorer, but the dashboard cannot call either service because there is no image-analysis HTTP endpoint. The scorer remains Unrated without all required evidence and fixed normalization references.</p>
          <div className="pipeline-status-grid" aria-label="Current RoadIQ analysis capabilities">
            <div><span>Task C · local vision</span><strong>CLI MVP available</strong><small>Texture-region candidates and annotation; not aggregate instances.</small></div>
            <div><span>Task A · surface scoring</span><strong>Backend scorer available</strong><small>Default normalization references are empty; score stays Unrated.</small></div>
            <div><span>Task D · desktop runtime</span><strong>Windows package branch</strong><small>Bundles this dashboard and health service; no image-analysis route.</small></div>
          </div>
          <div className="result-index-row"><span>Road Surface Quality Index</span><strong>— <small>/100</small></strong></div>
          <div className="report-evidence-grid">
            <div><span>Image quality / pavement region</span><strong>Local quality gate · no browser result</strong></div>
            <div><span>Surface type</span><strong>Unknown · no active classifier</strong></div>
            <div><span>Stone aggregates</span><strong>Instance counts unavailable</strong></div>
            <div><span>Metal fragments</span><strong>Separate target · unavailable</strong></div>
            <div><span>Defects / texture proxies</span><strong>Texture proxy · CLI only</strong></div>
            <div><span>Confidence / physical values / overlay</span><strong>Unavailable in this preview</strong></div>
          </div>
          <div className="rsqi-breakdown">
            <div className="rsqi-breakdown-heading">
              <strong>Candidate RSQI weighting</strong>
              <span>Provisional · not validated</span>
            </div>
            <ul>
              {rsqiComponents.map((component) => (
                <li key={component.label}>
                  <span>{component.label}</span>
                  <strong>{component.weight}</strong>
                  <small>Contribution unavailable</small>
                </li>
              ))}
            </ul>
            <p>RSQI = 100 − weighted damage. Missing evidence stays unavailable; weights are not redistributed.</p>
          </div>
          <p className="report-limitation">The texture candidate mask is not verified pavement, aggregate, or defect segmentation. Image texture is not physical roughness or IRI. A 2D image cannot establish strength, skid resistance, or travel safety.</p>
        </div>
      </div>
    </section>
  )
}
