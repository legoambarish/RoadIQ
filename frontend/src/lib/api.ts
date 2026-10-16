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
    mask_rle?: unknown
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
    quality_label?: string | null
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
  mode_suitability?: ModeSuitabilityScores | null
  annotated_image?: {
    value: string | null
    unit?: string
    status?: string
  }
  data_provenance?: Array<{ field_path: string; source: string }>
  model?: Record<string, unknown>
  processing_errors?: string[] | null
}

const defaultBaseUrl = 'http://localhost:8000/api/v1'
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
      if (parsed.detail) {
        throw new Error(parsed.detail)
      }
    } catch (parseError) {
      if (parseError instanceof Error && parseError.message !== errorBody) {
        // use errorBody below
      }
    }
    throw new Error(`Analysis failed (${response.status}): ${errorBody}`)
  }

  return (await response.json()) as ImageAnalysisResult
}
