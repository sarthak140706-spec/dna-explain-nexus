import {
  API_ENDPOINTS,
  apiPost,
} from "./index";

import type {
  UnifiedAnalysisResponse,
  VariantRequest,
} from "./types";

export async function analyzeVariant(
  variant: VariantRequest,
): Promise<UnifiedAnalysisResponse> {
  return apiPost<
    VariantRequest,
    UnifiedAnalysisResponse
  >(
    API_ENDPOINTS.analysis,
    variant,
  );
}