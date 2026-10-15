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
          <p>Preview a road image and see the report states the future analysis API will provide.</p>
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
          <p className="image-local-note">Files stay in this browser preview. RoadIQ has no image-analysis HTTP endpoint yet.</p>
        </div>

        <div className="image-result-card">
          <div className="result-header">
            <div><div className="section-kicker">Analysis report</div><h3>Unrated</h3></div>
            <span className="unrated-pill">SCORER NOT CONNECTED</span>
          </div>
          <p className="result-explanation">The backend now contains a provisional, evidence-gated RSQI scorer. This dashboard does not call it: there is no image-analysis API, and the default scorer has no fixed normalization references. It returns Unrated until all required evidence and reviewed references are available.</p>
          <div className="result-index-row"><span>Road Surface Quality Index</span><strong>— <small>/100</small></strong></div>
          <div className="report-evidence-grid">
            <div><span>Image quality / pavement region</span><strong>Not analyzed</strong></div>
            <div><span>Surface type</span><strong>Not classified</strong></div>
            <div><span>Stone aggregates</span><strong>No validated model</strong></div>
            <div><span>Metal fragments</span><strong>Separate target · unavailable</strong></div>
            <div><span>Defects / texture proxies</span><strong>Not connected</strong></div>
            <div><span>Confidence / coverage / overlay</span><strong>Unavailable</strong></div>
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
          <p className="report-limitation">Image texture is not physical roughness or IRI. A 2D image cannot establish strength, skid resistance, or travel safety.</p>
        </div>
      </div>
    </section>
  )
}
