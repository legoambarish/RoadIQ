export type HealthResponse = {
  status: string
  service: string
}

export type MeasurementObject = {
  value: number | string | null
  unit?: string
  status?: string
  source?: string | null
  reason?: string | null
}

export type BinaryMaskRLE = {
  encoding: 'row_major_binary_rle_v1'
  size_px: [number, number]
  foreground_label: string
  counts: number[]
}

export type ModeSuitabilityScores = {
  walking: number | null
  cycling: number | null
  two_wheeler: number | null
  car: number | null
  bus: number | null
}

export type ImageAnalysisResult = {
  analysis_id: string
  analysis_status: string
  image?: {
    width_px?: number
    height_px?: number
    source_name?: string
    sha256?: string
    coordinate_system?: string
    format?: string
    size_px?: [number, number]
    byte_count?: number
  }
  image_quality?: {
    status?: string
    usable?: boolean
    issues?: string[]
    metrics?: {
      width_px?: number
      height_px?: number
      mean_luma_0_255?: number
      edge_detail_variance_proxy?: number
    }
    limitations?: string[]
  }
  pavement_region?: {
    usable_area_ratio?: MeasurementObject
    annotation?: MeasurementObject
    mask_rle?: BinaryMaskRLE | null
    usable_pavement_including_potholes_mask_rle?: BinaryMaskRLE | null
  }
  surface_type?: MeasurementObject
  aggregate_analysis?: {
    segmentation_status?: string
    aggregate_loss_indicator?: MeasurementObject
    surface_region?: {
      candidate_area_ratio?: number
      candidate_area_px?: number
      pixel_boundary_length?: number
      bbox_xyxy_px?: [number, number, number, number]
    }
  }
  defects?: Array<{
    class: string
    count?: MeasurementObject
    visible_area_ratio?: MeasurementObject
    confidence?: number | null
    detections?: Detection[]
    mask_rle?: BinaryMaskRLE | null
    mask_geometry?: Record<string, unknown> | null
  }>
  texture_features?: {
    features?: Array<{
      name: string
      value: number | null
      unit: string
      status: string
      source: string
      reason?: string
    }>
    is_physical_roughness?: boolean
  }
  rsqi?: {
    value: number | null
    unit: string
    status: string
    components?: Record<
      string,
      {
        value: number | null
        unit: string
        status: string
        source: string | null
        weight: number
        weighted_contribution: number | null
      }
    >
    explanation?: string
    limitations?: string[]
  }
  quality_label?: string | null
  scoring_version?: string
  mode_suitability?: ModeSuitabilityScores | null
  annotated_image?: {
    value: string | null
    unit?: string
    status?: string
  }
  data_provenance?: Array<{ field_path: string; source: string }>
  model?: Record<string, unknown>
  processing_errors?: Array<Record<string, unknown>> | null
  visual_distress?: VisualDistress
  calibration?: Record<string, unknown>
  processing_time_ms?: Record<string, number | null>
}

export type Detection = {
  class: string
  model_label: string
  instance_id: string | null
  confidence: number
  confidence_kind: 'raw_model_score'
  coordinate_system: 'exif_oriented_source_pixels'
  bbox_xyxy_px: { x_min: number; y_min: number; x_max: number; y_max: number }
  bbox_xyxy_normalized: { x_min: number; y_min: number; x_max: number; y_max: number }
  box_extent_width_px: number | null
  box_extent_height_px: number | null
  edge_clipped: boolean
  small_box_resolution: boolean
  segmented_area_px: null
  crack_length_px: null
  physical_width_mm: null
  geometry_unavailable_reason: string
}

export type VisualDistress = {
  version: string
  status: 'defects_detected' | 'no_defect_detected' | 'low_confidence' | 'unusable' | 'unavailable'
  summary: string
  detection_count: number | null
  counts_by_model_class: Record<string, number>
  caution_flags: string[]
  reliability: 'limited' | 'unavailable'
  reliability_reasons: string[]
  score_eligible: false
  grade: null
  score: null
  confidence: null
  physical_measurements: Record<string, unknown>
  reference_percentile: { value: null; status: 'unavailable'; reason: string }
}

const defaultBaseUrl = import.meta.env.DEV ? 'http://localhost:8000/api/v1' : '/api/v1'
const apiBaseUrl = import.meta.env.VITE_API_BASE_URL ?? defaultBaseUrl

export async function fetchHealth(signal?: AbortSignal): Promise<HealthResponse> {
  const response = await fetch(`${apiBaseUrl}/health`, {
    signal,
  })

  if (!response.ok) {
    throw new Error(`Health request failed with status ${response.status}`)
  }

  return (await response.json()) as HealthResponse
}

export async function analyzeImage(file: File, signal?: AbortSignal): Promise<ImageAnalysisResult> {
  const formData = new FormData()
  formData.append('image', file)

  const response = await fetch(`${apiBaseUrl}/image-analyses`, {
    method: 'POST',
    body: formData,
    signal,
  })

  if (!response.ok) {
    const errorBody = await response.text()
    try {
      const parsed = JSON.parse(errorBody)
      const detail = parsed && typeof parsed.detail === 'string' ? parsed.detail : errorBody
      throw new Error(`Analysis failed (${response.status}): ${detail}`)
    } catch (parseError) {
      if (parseError instanceof SyntaxError) {
        throw new Error(`Analysis failed (${response.status}): ${errorBody}`)
      }
      throw parseError
    }
  }

  return (await response.json()) as ImageAnalysisResult
}
