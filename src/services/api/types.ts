// ============================================================
// Common API types
// ============================================================

export type ImpactClass =
  | "LOW"
  | "MODERATE"
  | "HIGH";

export type ConfidenceBand =
  | "LOW"
  | "MODERATE"
  | "HIGH";

export type PredictedClassName =
  | "benign_like"
  | "pathogenic_like";

export type VerificationStatus =
  | "full_match"
  | "protein_match_only"
  | "dna_match_only"
  | "mismatch"
  | "not_verified";


// ============================================================
// Variant request / identity
// ============================================================

export interface VariantRequest {
  gene_symbol: string;

  chromosome?: string | null;

  position?: number | null;

  reference_allele: string;

  alternate_allele: string;

  protein_position: number;

  reference_amino_acid: string;

  alternate_amino_acid: string;

  dna_change?: string | null;

  protein_change?: string | null;
}

export interface VariantIdentity {
  gene_symbol: string;

  chromosome?: string | null;

  position?: number | null;

  reference_allele: string;

  alternate_allele: string;

  protein_position: number;

  reference_amino_acid: string;

  alternate_amino_acid: string;

  dna_change?: string | null;

  protein_change?: string | null;
}


// ============================================================
// Variant validation
// ============================================================

export interface VariantValidationResponse {
  success: boolean;

  variant: VariantIdentity;

  genomic_validation_performed: boolean;

  protein_validation_performed: boolean;

  genomic_variant_valid: boolean | null;

  protein_variant_valid: boolean | null;

  verification_status?: VerificationStatus | null;

  selected_transcript_id?: string | null;

  selected_transcript_reason?: string | null;

  expected_reference_amino_acid?: string | null;

  observed_reference_amino_acid?: string | null;

  warnings: string[];

  research_only: boolean;

  disclaimer: string;
}


// ============================================================
// Prediction
// ============================================================

export interface PredictionResult {
  predicted_class: number;

  predicted_class_name: PredictedClassName;

  raw_model_score: number;

  calibrated_probability:
    | number
    | null;

  confidence_score:
    | number
    | null;

  uncertainty_score:
    | number
    | null;

  confidence_band:
    | ConfidenceBand
    | null;

  impact_class:
    | ImpactClass
    | null;

  model_name: string;

  model_version: string;

  target_interpretation: string;

  score_interpretation: string;
}

export interface PredictionResponse {
  success: boolean;

  variant: VariantIdentity;

  prediction: PredictionResult;

  research_only: boolean;

  disclaimer: string;
}


// ============================================================
// XAI
// ============================================================

export interface FeatureContribution {
  feature_name: string;

  feature_value:
    | number
    | string
    | boolean
    | null;

  raw_contribution: number;

  absolute_contribution: number;

  normalized_share: number;

  normalized_percent: number;

  signed_normalized_percent: number;

  direction:
    | "supports_higher_impact"
    | "supports_lower_impact"
    | "neutral";

  rank: number;
}

export interface DirectionSummary {
  supporting_higher_impact_percent: number;

  supporting_lower_impact_percent: number;

  neutral_percent: number;

  total_percent: number;
}

export interface LocalExplanation {
  normalization_version: string;

  explanation_version: string;

  model_name: string;

  model_version: string;

  target_interpretation: string;

  normalization_method: string;

  normalization_formula: string;

  total_absolute_contribution: number;

  feature_count: number;

  feature_contributions: FeatureContribution[];

  top_features: FeatureContribution[];

  direction_summary: DirectionSummary;

  percentage_interpretation: string;

  test_set_used: boolean;

  research_only: boolean;
}

export interface XAIResult {
  predicted_class: number;

  predicted_class_name: PredictedClassName;

  raw_model_score: number;

  calibrated_probability: number;

  confidence_score: number;

  uncertainty_score: number;

  confidence_band: ConfidenceBand;

  impact_class: ImpactClass;
}

export interface XAIResponse {
  success: boolean;

  variant: VariantIdentity;

  result: XAIResult;

  explanation: LocalExplanation;

  research_only: boolean;

  disclaimer: string;
}


// ============================================================
// Protein Context
// ============================================================

export interface ProteinIdentity {
  accession: string;

  gene_symbol: string;

  protein_name: string;

  organism: string;

  reviewed: boolean;

  sequence_length: number;
}

export interface ProteinFeature {
  feature_type: string;

  start: number;

  end: number;

  start_fraction?: number | null;

  end_fraction?: number | null;

  description?: string | null;

  feature_id?: string | null;

  evidence: string[];

  overlaps_variant: boolean;

  distance_to_variant: number;
}

export interface ProteinSequenceContext {
  protein_position: number;

  reference_amino_acid: string;

  alternate_amino_acid: string;

  sequence_reference_amino_acid: string;

  position_matches_reference: boolean;

  window_start: number;

  window_end: number;

  sequence_window: string;
}

export interface ProteinVariantMarker {
  position: number;

  reference_amino_acid: string;

  alternate_amino_acid: string;

  label: string;
}

export interface VisualizationFeature {
  feature_type: string;

  start: number;

  end: number;

  start_fraction: number;

  end_fraction: number;

  description?: string | null;

  feature_id?: string | null;

  evidence: string[];

  overlaps_variant: boolean;

  distance_to_variant: number;
}

export interface VisualizationTrack {
  track_type: string;

  label: string;

  features: VisualizationFeature[];
}

export interface ProteinContextResponse {
  success: boolean;

  variant: VariantIdentity;

  protein: ProteinIdentity;

  sequence_context: ProteinSequenceContext;

  overlapping_features: ProteinFeature[];

  nearby_features: ProteinFeature[];

  visualization_tracks: VisualizationTrack[];

  variant_marker: ProteinVariantMarker;

  protein_context_version: string;

  visualization_version: string;

  interpretation: string;

  research_only: boolean;

  disclaimer: string;
}


// ============================================================
// GeneMirror Scientist
// ============================================================

export interface ScientistExplanationSections {
  overview: string;

  prediction: string;

  evidence: string;

  protein_context: string;

  limitations: string;
}

export interface ScientistGroundedFact {
  source: string;

  category: string;

  statement: string;

  value: unknown;

  supports?: string | null;
}

export interface ScientistExecutionMetadata {
  requested_provider?: string | null;

  provider_used: string;

  used_llm_response: boolean;

  fallback_used: boolean;

  fallback_reason?: string | null;

  validation_errors: string[];
}

export interface ScientistResponse {
  success: boolean;

  variant: VariantIdentity;

  sections: ScientistExplanationSections;

  grounded_facts: ScientistGroundedFact[];

  scientist_name: string;

  scientist_version: string;

  contract_version: string;

  provider: string;

  language_model?: string | null;

  execution: ScientistExecutionMetadata;

  research_only: boolean;

  disclaimer: string;
}


// ============================================================
// Unified Analysis
// ============================================================

export interface UnifiedAnalysisResponse {
  success: boolean;

  variant: VariantIdentity;

  validation: VariantValidationResponse;

  prediction: PredictionResult;

  xai: XAIResponse;

  protein_context: ProteinContextResponse;

  scientist: ScientistResponse;

  research_only: boolean;

  disclaimer: string;
}


// ============================================================
// Health endpoint
// ============================================================

export interface HealthResponse {
  status: string;

  service: string;

  version: string;

  api_version: string;

  environment: string;

  research_only: boolean;
}


// ============================================================
// Generic backend error shape
// ============================================================

export interface ApiErrorDetail {
  code?: string;

  message: string;

  research_only?: boolean;
}

export interface ApiErrorResponse {
  detail:
    | string
    | ApiErrorDetail;
}