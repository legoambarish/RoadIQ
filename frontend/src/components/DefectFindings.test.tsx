import { renderToStaticMarkup } from 'react-dom/server'
import { describe, expect, it } from 'vitest'
import { DefectFindings, DetectionOverlay } from './DefectFindings'
import type { Detection, ImageAnalysisResult } from '../lib/api'

const detection: Detection = {
  class: 'pothole', model_label: 'pothole', instance_id: 'image-hole-1', confidence: 0.73,
  confidence_kind: 'raw_model_score', coordinate_system: 'exif_oriented_source_pixels',
  bbox_xyxy_px: { x_min: 10, y_min: 20, x_max: 50, y_max: 60 },
  bbox_xyxy_normalized: { x_min: .1, y_min: .2, x_max: .5, y_max: .6 },
  box_extent_width_px: 40, box_extent_height_px: 40, edge_clipped: false, small_box_resolution: false,
  segmented_area_px: null, crack_length_px: null, physical_width_mm: null,
  geometry_unavailable_reason: 'Boxes are not masks',
}

const result: ImageAnalysisResult = {
  analysis_id: 'contract-fixture', analysis_status: 'unrated',
  defects: [{ class: 'pothole', detections: [detection] }],
  visual_distress: {
    version: 'vda-observations-v1', status: 'defects_detected', summary: 'One localized candidate; depth unknown.',
    detection_count: 1, counts_by_model_class: { pothole: 1 }, caution_flags: ['localized_pothole_candidate:image-hole-1'],
    reliability: 'limited', reliability_reasons: ['Raw model score is uncalibrated.'], score_eligible: false,
    grade: null, score: null, confidence: null, physical_measurements: { pothole_depth_mm: null },
    reference_percentile: { value: null, status: 'unavailable', reason: 'No scored reference' },
  },
}

describe('backend prediction presentation', () => {
  it('renders source boxes with aligned aspect ratio and prediction labeling', () => {
    const output = renderToStaticMarkup(<DetectionOverlay detections={[detection]} width={100} height={100} />)
    expect(output).toContain('viewBox="0 0 100 100"')
    expect(output).toContain('x="10" y="20" width="40" height="40"')
    expect(output).toContain('not ground truth')
    expect(output).toContain('raw model score 0.730')
  })

  it('keeps physical unknowns and localized cautions in Everyday', () => {
    const output = renderToStaticMarkup(<DefectFindings result={result} view="everyday" />)
    expect(output).toContain('Localized findings need inspection')
    expect(output).toContain('Physical defect dimensions: unavailable')
    expect(output).not.toContain('Model, timing, calibration and provenance')
    expect(output).not.toContain('Good')
  })

  it('shows raw geometry and provenance separately in Engineer', () => {
    const output = renderToStaticMarkup(<DefectFindings result={result} view="engineer" />)
    expect(output).toContain('extent 40.0 × 40.0 px')
    expect(output).toContain('0.7300 (uncalibrated)')
    expect(output).toContain('Model, timing, calibration and provenance')
    expect(output).toContain('Box extent is not defect width')
  })
})
