import type { Detection, ImageAnalysisResult } from '../lib/api'

const statusLabels = {
  defects_detected: 'Visible defect candidates',
  no_defect_detected: 'No supported defect detected',
  low_confidence: 'Limited image evidence',
  unusable: 'Image unsuitable for assessment',
  unavailable: 'Defect model unavailable',
}

export function DetectionOverlay({ detections, width, height }: { detections: Detection[]; width: number; height: number }) {
  return (
    <svg className="detection-overlay" viewBox={`0 0 ${width} ${height}`} preserveAspectRatio="xMidYMid meet" role="img" aria-label="Model predicted defect boxes; not ground truth">
      {detections.map((item, index) => {
        const b = item.bbox_xyxy_px
        const color = item.class === 'pothole' ? '#ffac33' : '#ef5555'
        return <g key={item.instance_id ?? index}>
          <title>{`${item.model_label.replaceAll('_', ' ')} · raw model score ${item.confidence.toFixed(3)}`}</title>
          <rect x={b.x_min} y={b.y_min} width={b.x_max - b.x_min} height={b.y_max - b.y_min} fill="none" stroke={color} strokeWidth="2" vectorEffect="non-scaling-stroke" strokeDasharray="6 3" />
          <text x={b.x_min + 3} y={Math.max(15, b.y_min - 5)} fill={color} stroke="#101a20" strokeWidth="3" paintOrder="stroke" fontSize={Math.max(14, width / 45)}>{item.model_label.replaceAll('_', ' ')}</text>
        </g>
      })}
    </svg>
  )
}

export function DefectFindings({ result, view }: { result: ImageAnalysisResult; view: 'everyday' | 'engineer' }) {
  const vda = result.visual_distress
  if (!vda) return null
  const detections = result.defects?.flatMap((item) => item.detections ?? []) ?? []
  return <section className="defect-findings" aria-label="Visual Distress Assessment">
    <div className="subsection-heading"><strong>{statusLabels[vda.status]}</strong><span>{vda.version}</span></div>
    <p role="status">{vda.summary}</p>
    {Object.entries(vda.counts_by_model_class).length > 0 && <ul className="defect-counts">
      {Object.entries(vda.counts_by_model_class).map(([name, count]) => <li key={name}><strong>{count}</strong> {name.replaceAll('_', ' ')}</li>)}
    </ul>}
    {vda.caution_flags.length > 0 && <div className="localized-cautions" role="note"><strong>Localized findings need inspection</strong><ul>
      {vda.caution_flags.map((flag) => <li key={flag}>{flag.replaceAll('_', ' ').replaceAll(':', ' · ')}</li>)}
    </ul><p>A small affected region can still matter. Depth and operational severity are unknown.</p></div>}
    <p>Physical defect dimensions: unavailable. RSQI reference percentile: unavailable because no eligible, compatible scored cohort exists. No engineering condition grade is assigned.</p>
    {result.defects?.filter((item) => typeof item.mask_geometry?.heldout_pothole_iou_model_input_resolution === 'number').map((item) =>
      <p key={item.class} className="image-local-note" role="note">Experimental pothole mask: source held-out IoU {(item.mask_geometry!.heldout_pothole_iou_model_input_resolution as number).toFixed(3)} at model-input resolution. Predicted areas are not validated measurements.</p>)}
    <details open={view === 'engineer'}><summary>Evidence reliability: {vda.reliability}</summary><ul>
      {vda.reliability_reasons.map((reason) => <li key={reason}>{reason}</li>)}
    </ul></details>
    {view === 'engineer' && <>
      {result.defects?.filter((item) => item.mask_geometry).map((item) => <details key={item.class}><summary>{item.class}: semantic mask geometry (pixels; experimental)</summary><pre className="model-ledger">{JSON.stringify(item.mask_geometry, null, 2)}</pre></details>)}
      {detections.length > 0 && <div className="defect-table-wrap"><table className="defect-table"><thead><tr><th>Prediction / raw score</th><th>Source box (px)</th><th>Geometry</th></tr></thead><tbody>
        {detections.map((item, index) => <tr key={item.instance_id ?? index}><td>{item.model_label}<br />{item.confidence.toFixed(4)} (uncalibrated)<br /><small>{item.instance_id}</small></td>
          <td>{Object.values(item.bbox_xyxy_px).map((n) => n.toFixed(1)).join(', ')}<br />extent {item.box_extent_width_px?.toFixed(1)} × {item.box_extent_height_px?.toFixed(1)} px</td>
          <td>Mask area / crack length: unavailable<br />{item.edge_clipped ? 'Edge-clipped candidate' : 'Box within frame'}<br />{item.small_box_resolution ? 'Small extent; detail unresolved' : 'Box extent is not defect width'}</td></tr>)}
      </tbody></table></div>}
      <details><summary>Model, timing, calibration and provenance</summary><pre className="model-ledger">{JSON.stringify({ image: result.image, model: result.model, processing_time_ms: result.processing_time_ms, calibration: result.calibration, pavement_region: result.pavement_region ? { usable_area_ratio: result.pavement_region.usable_area_ratio, mask_available: Boolean(result.pavement_region.mask_rle) } : null, data_provenance: result.data_provenance }, null, 2)}</pre></details>
    </>}
  </section>
}
