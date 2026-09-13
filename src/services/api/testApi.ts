import {
    API_ENDPOINTS,
    apiGet,
  } from "./index";
  
  import type {
    HealthResponse,
  } from "./index";
  
  export async function testApiConnection() {
    const response =
      await apiGet<HealthResponse>(
        API_ENDPOINTS.health,
      );
  
    console.log(
      "GeneMirror API:",
      response,
    );
  
    return response;
  }