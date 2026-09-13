export {
  API_CONFIG,
  API_ENDPOINTS,
} from "./config";

export {
  ApiError,
  apiGet,
  apiPost,
  apiRequest,
} from "./client";

export type {
  ImpactClass,
  ConfidenceBand,
  PredictedClassName,
  VerificationStatus,

  VariantRequest,
  VariantIdentity,
  VariantValidationResponse,

  PredictionResult,
  PredictionResponse,

  FeatureContribution,
  DirectionSummary,
  LocalExplanation,
  XAIResult,
  XAIResponse,

  ProteinIdentity,
  ProteinFeature,
  ProteinSequenceContext,
  ProteinVariantMarker,
  VisualizationFeature,
  VisualizationTrack,
  ProteinContextResponse,

  ScientistExplanationSections,
  ScientistGroundedFact,
  ScientistExecutionMetadata,
  ScientistResponse,

  UnifiedAnalysisResponse,

  HealthResponse,

  ApiErrorDetail,
  ApiErrorResponse,
} from "./types";

export {
  analyzeVariant,
} from "./analysis";