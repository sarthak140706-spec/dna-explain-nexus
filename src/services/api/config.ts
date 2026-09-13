export const API_CONFIG = {
    baseUrl:
      import.meta.env.VITE_GENEMIRROR_API_URL ??
      "http://127.0.0.1:8000/api/v1",
  
    timeoutMs: 60_000,
  } as const;
  
  export const API_ENDPOINTS = {
    health: "/health",
    validateVariant: "/variants/validate",
    predict: "/predict",
    xai: "/xai",
    proteinContext: "/protein-context",
    scientist: "/scientist",
    analysis: "/analysis",
  } as const;