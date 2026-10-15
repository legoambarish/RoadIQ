import { useEffect, useState, type ChangeEvent, type DragEvent } from 'react'

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
            <span className="unrated-pill">NO RESULT</span>
          </div>
          <p className="result-explanation">No inference has run. A selected image does not produce a road score until a reviewed image-analysis API and scorer are connected.</p>
          <div className="result-index-row"><span>Road Surface Quality Index</span><strong>— <small>/100</small></strong></div>
          <div className="report-evidence-grid">
            <div><span>Image quality / pavement region</span><strong>Unavailable</strong></div>
            <div><span>Surface type</span><strong>Unknown</strong></div>
            <div><span>Aggregates / metal fragments</span><strong>Unavailable</strong></div>
            <div><span>Defects / texture proxies</span><strong>Unavailable</strong></div>
            <div><span>Confidence / coverage</span><strong>Unavailable</strong></div>
            <div><span>Annotated overlay</span><strong>Unavailable</strong></div>
          </div>
          <div className="component-unavailable"><strong>Score contributions</strong><span>Every component is unavailable. Missing evidence is not treated as zero.</span></div>
          <p className="report-limitation">Image texture is not physical roughness or IRI. A 2D image cannot establish strength, skid resistance, or travel safety.</p>
        </div>
      </div>
    </section>
  )
}
