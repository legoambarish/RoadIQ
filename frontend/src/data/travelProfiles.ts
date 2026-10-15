import type { PedestrianContext, RoadMeasurements, TravelMode } from '../types/road-segment'

type ProfileEvidenceField =
  | { kind: 'measurement'; key: keyof RoadMeasurements }
  | { kind: 'pedestrian'; key: keyof PedestrianContext }
  | { kind: 'confidence' }
  | { kind: 'not-represented'; detail: string }

type ProfileEvidence = { label: string; field: ProfileEvidenceField }

export type TravelProfileGuide = {
  everydayTitle: string
  everydayDescription: string
  everydayChecks: string[]
  engineerDefinition: string
  evidence: ProfileEvidence[]
}

export const travelProfileGuides: Record<TravelMode, TravelProfileGuide> = {
  walking: {
    everydayTitle: 'A smoother road is not automatically a better walk.',
    everydayDescription: 'Walking comfort depends on accessible space and exposure to traffic as well as the pavement surface. This demo has no verified pedestrian observations.',
    everydayChecks: ['Footpath presence and continuity', 'Crossings and accessible space', 'Traffic exposure and personal comfort'],
    engineerDefinition: 'Keep pedestrian infrastructure and exposure separate from surface condition. Lane markings are not a proxy for pedestrian suitability.',
    evidence: [
      { label: 'Footpath observed', field: { kind: 'pedestrian', key: 'footpath_present' } },
      { label: 'Crossings observed', field: { kind: 'pedestrian', key: 'crossings_observed' } },
      { label: 'Pedestrian comfort', field: { kind: 'pedestrian', key: 'comfort_score' } },
      { label: 'Traffic exposure / accessible width', field: { kind: 'not-represented', detail: 'Not in the current segment contract' } },
    ],
  },
  cycling: {
    everydayTitle: 'Surface breaks can make a ride harder to hold steady.',
    everydayDescription: 'Potholes, broken edges, and loose material can affect ride comfort. This example does not show verified cycle access or traffic separation.',
    everydayChecks: ['Potholes and broken edges', 'Surface continuity', 'Cycle access and traffic separation'],
    engineerDefinition: 'Consider defect frequency, roughness, and grade alongside cycling access and traffic separation; no mode-specific score formula is agreed.',
    evidence: [
      { label: 'Defect count', field: { kind: 'measurement', key: 'defect_count' } },
      { label: 'Defect density', field: { kind: 'measurement', key: 'defect_density' } },
      { label: 'IRI roughness', field: { kind: 'measurement', key: 'roughness_iri' } },
      { label: 'Longitudinal grade', field: { kind: 'measurement', key: 'longitudinal_grade' } },
      { label: 'Cycle separation / access', field: { kind: 'not-represented', detail: 'Not in the current segment contract' } },
    ],
  },
  two_wheeler: {
    everydayTitle: 'Small bumps can matter when they are abrupt or hard to see.',
    everydayDescription: 'Larger potholes and rough patches deserve attention too. This is a profile explanation, not advice about the safety of this demo road.',
    everydayChecks: ['Surface irregularities and abrupt bumps', 'Potholes and cracks', 'Grip-related warnings only when observable'],
    engineerDefinition: 'Track pothole and crack density, defect dimensions only where calibrated, repeated surface irregularities, and confidence in image visibility. Grip is not inferred from a still image.',
    evidence: [
      { label: 'Defect count', field: { kind: 'measurement', key: 'defect_count' } },
      { label: 'Pothole / crack density', field: { kind: 'measurement', key: 'defect_density' } },
      { label: 'Calibrated defect dimensions', field: { kind: 'not-represented', detail: 'No dimension field or image calibration is available' } },
      { label: 'Repeated irregularities', field: { kind: 'not-represented', detail: 'No repeated-event or vibration series is available' } },
      { label: 'Image visibility confidence', field: { kind: 'confidence' } },
      { label: 'Grip / skid resistance', field: { kind: 'not-represented', detail: 'Not measured; cannot be established from a 2D image' } },
    ],
  },
  car: {
    everydayTitle: 'Surface damage can affect comfort and vehicle wear.',
    everydayDescription: 'Potholes and uneven patches matter, but a surface score alone cannot tell you about traffic, access, or whether a route is safe.',
    everydayChecks: ['Potholes and damaged surface', 'Ride roughness', 'Grade and crossfall where measured'],
    engineerDefinition: 'Review defect evidence, calibrated roughness, longitudinal grade, and crossfall. The current mode formula and minimum evidence gate are unresolved.',
    evidence: [
      { label: 'Defect density', field: { kind: 'measurement', key: 'defect_density' } },
      { label: 'IRI roughness', field: { kind: 'measurement', key: 'roughness_iri' } },
      { label: 'Longitudinal grade', field: { kind: 'measurement', key: 'longitudinal_grade' } },
      { label: 'Crossfall', field: { kind: 'measurement', key: 'crossfall' } },
      { label: 'Traffic / access conditions', field: { kind: 'not-represented', detail: 'Not in the current segment contract' } },
    ],
  },
  bus: {
    everydayTitle: 'Uneven patches can affect ride comfort for everyone onboard.',
    everydayDescription: 'Pavement condition is only one part of a bus journey. This demo does not assess stop access, vehicle clearance, or passenger boarding.',
    everydayChecks: ['Potholes and roughness', 'Grade and crossfall where measured', 'Stop access and boarding conditions'],
    engineerDefinition: 'Review defect density, calibrated roughness, grade, and crossfall separately from bus-stop access and vehicle-envelope constraints.',
    evidence: [
      { label: 'Defect density', field: { kind: 'measurement', key: 'defect_density' } },
      { label: 'IRI roughness', field: { kind: 'measurement', key: 'roughness_iri' } },
      { label: 'Longitudinal grade', field: { kind: 'measurement', key: 'longitudinal_grade' } },
      { label: 'Crossfall', field: { kind: 'measurement', key: 'crossfall' } },
      { label: 'Stop access / vehicle envelope', field: { kind: 'not-represented', detail: 'Not in the current segment contract' } },
    ],
  },
}
