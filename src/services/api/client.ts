import {
    API_CONFIG,
  } from "./config";
  
  export class ApiError extends Error {
    status: number;
    code?: string;
    details?: unknown;
  
    constructor(
      message: string,
      status: number,
      code?: string,
      details?: unknown,
    ) {
      super(message);
  
      this.name = "ApiError";
      this.status = status;
      this.code = code;
      this.details = details;
    }
  }
  
  type ApiRequestOptions = RequestInit & {
    timeoutMs?: number;
  };
  
  function buildUrl(
    endpoint: string,
  ): string {
    return `${API_CONFIG.baseUrl}${endpoint}`;
  }
  
  async function parseResponseBody(
    response: Response,
  ): Promise<unknown> {
    const contentType =
      response.headers.get("content-type");
  
    if (
      contentType?.includes(
        "application/json",
      )
    ) {
      return response.json();
    }
  
    return response.text();
  }
  
  function extractApiError(
    body: unknown,
  ): {
    message: string;
    code?: string;
  } {
    if (
      typeof body === "object" &&
      body !== null
    ) {
      const record =
        body as Record<string, unknown>;
  
      const detail =
        record.detail;
  
      if (
        typeof detail === "object" &&
        detail !== null
      ) {
        const detailRecord =
          detail as Record<
            string,
            unknown
          >;
  
        return {
          message:
            typeof detailRecord.message ===
            "string"
              ? detailRecord.message
              : "GeneMirror API request failed.",
  
          code:
            typeof detailRecord.code ===
            "string"
              ? detailRecord.code
              : undefined,
        };
      }
  
      if (
        typeof detail === "string"
      ) {
        return {
          message: detail,
        };
      }
    }
  
    return {
      message:
        "GeneMirror API request failed.",
    };
  }
  
  export async function apiRequest<T>(
    endpoint: string,
    options: ApiRequestOptions = {},
  ): Promise<T> {
    const controller =
      new AbortController();
  
    const timeout =
      window.setTimeout(
        () => {
          controller.abort();
        },
        options.timeoutMs ??
          API_CONFIG.timeoutMs,
      );
  
    try {
      const response =
        await fetch(
          buildUrl(endpoint),
          {
            ...options,
  
            headers: {
              "Content-Type":
                "application/json",
  
              ...(options.headers ?? {}),
            },
  
            signal:
              controller.signal,
          },
        );
  
      const body =
        await parseResponseBody(
          response,
        );
  
      if (!response.ok) {
        const error =
          extractApiError(
            body,
          );
  
        throw new ApiError(
          error.message,
          response.status,
          error.code,
          body,
        );
      }
  
      return body as T;
    } catch (error) {
      if (
        error instanceof ApiError
      ) {
        throw error;
      }
  
      if (
        error instanceof DOMException &&
        error.name ===
          "AbortError"
      ) {
        throw new ApiError(
          "GeneMirror API request timed out.",
          408,
          "API_TIMEOUT",
        );
      }
  
      if (
        error instanceof Error
      ) {
        throw new ApiError(
          error.message,
          0,
          "NETWORK_ERROR",
        );
      }
  
      throw new ApiError(
        "Unable to communicate with GeneMirror API.",
        0,
        "NETWORK_ERROR",
      );
    } finally {
      window.clearTimeout(
        timeout,
      );
    }
  }
  
  export async function apiGet<T>(
    endpoint: string,
  ): Promise<T> {
    return apiRequest<T>(
      endpoint,
      {
        method: "GET",
      },
    );
  }
  
  export async function apiPost<
    TRequest,
    TResponse,
  >(
    endpoint: string,
    payload: TRequest,
  ): Promise<TResponse> {
    return apiRequest<TResponse>(
      endpoint,
      {
        method: "POST",
  
        body: JSON.stringify(
          payload,
        ),
      },
    );
  }