/**
 * Chatrio Core API Client.
 *
 * Provides typed fetch wrapper with:
 * 1. Automatic Authorization: Bearer <access_token> header injection.
 * 2. Unified error handling matching FastAPI's AppException JSON response structure:
 *    { "error": { "code": "...", "message": "...", "details": {...} } }
 * 3. Base URL resolution from NEXT_PUBLIC_API_URL or default http://localhost:8000/api/v1.
 */

export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

export class ApiError extends Error {
  status: number;
  code?: string;
  details?: unknown;

  constructor(message: string, status: number, code?: string, details?: unknown) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.code = code;
    this.details = details;
  }
}

export async function apiClient<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const token =
    typeof window !== "undefined"
      ? localStorage.getItem("chatrio_access_token")
      : null;

  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string>),
  };

  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const url = `${API_BASE_URL}${endpoint}`;

  let response: Response;
  try {
    response = await fetch(url, {
      ...options,
      headers,
    });
  } catch (networkError) {
    throw new ApiError(
      "Unable to connect to Chatrio backend server. Make sure the FastAPI service is running on http://localhost:8000.",
      0,
      "NETWORK_ERROR",
      networkError
    );
  }

  // Handle Unauthorized (401)
  if (response.status === 401) {
    if (typeof window !== "undefined" && !window.location.pathname.startsWith("/login")) {
      localStorage.removeItem("chatrio_access_token");
      localStorage.removeItem("chatrio_user");
      localStorage.removeItem("chatrio_org");
      window.location.href = "/login";
    }
  }

  if (response.status === 204) {
    return null as T;
  }

  const responseText = await response.text();
  let responseData: any = null;

  try {
    if (responseText) {
      responseData = JSON.parse(responseText);
    }
  } catch {
    responseData = responseText;
  }

  if (!response.ok) {
    let message = `API request failed with status ${response.status}`;
    let code: string | undefined;
    let details: unknown;

    if (responseData && typeof responseData === "object") {
      if (responseData.error) {
        message = responseData.error.message || message;
        code = responseData.error.code;
        details = responseData.error.details;
      } else if (responseData.detail) {
        message =
          typeof responseData.detail === "string"
            ? responseData.detail
            : JSON.stringify(responseData.detail);
      }
    }

    throw new ApiError(message, response.status, code, details);
  }

  return responseData as T;
}

