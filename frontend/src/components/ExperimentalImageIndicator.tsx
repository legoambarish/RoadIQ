import type { ExperimentalImageIndicator as IndicatorData } from '../lib/api'

export function ExperimentalImageIndicator({ indicator }: { indicator: IndicatorData }) {
  return (
    <div className="experimental-indicator" aria-label="Experimental model image measurements">
      <div className="subsection-heading"><strong>Experimental image measurements</strong><span>Model observations · not RSQI</span></div>
      {indicator.status !== 'unavailable' ? <>
        {indicator.status === 'limited' && <p className="image-local-note">Low-resolution preview only; do not interpret as a condition assessment.</p>}
        <div className="report-evidence-grid">
          <div><span>Detected candidate boxes</span><strong>{indicator.candidate_count}</strong></div>
          <div><span>Candidate box coverage of image</span><strong>{indicator.candidate_box_coverage_percent?.toFixed(2)}%</strong></div>
          <div><span>Predicted pothole pixels / predicted pavement</span><strong>
            {indicator.predicted_pothole_pixel_fraction_percent === null
              ? 'Unavailable'
              : `${indicator.predicted_pothole_pixel_fraction_percent.toFixed(2)}%`}
          </strong></div>
        </div>
        <p className="image-local-note">Box coverage is the union of detector candidate boxes divided by the full image area. Pothole fraction is an unvalidated semantic-mask prediction. Neither value is a condition score; zero candidates does not mean a clear road.</p>
      </> : <p className="image-local-note">{indicator.unavailable_reason ?? 'Experimental image measurements are unavailable.'}</p>}
    </div>
  )
}
