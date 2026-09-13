import type {
  UnifiedAnalysisResponse,
  VariantRequest,
  XAIResponse,
  ProteinContextResponse,
  ScientistResponse,
} from "./index";

export type ApiContractSmokeTest = {
  request: VariantRequest;
  analysis: UnifiedAnalysisResponse;
  xai: XAIResponse;
  protein: ProteinContextResponse;
  scientist: ScientistResponse;
};