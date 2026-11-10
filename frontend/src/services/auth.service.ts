/**
 * Authentication Service.
 *
 * Direct client mapping to backend router:
 * backend/app/modules/auth/router.py
 *
 * Endpoints:
 * - POST /api/v1/auth/register -> register(data)
 * - POST /api/v1/auth/login    -> login(email, password)
 * - GET  /api/v1/auth/me       -> getMe()
 */

import { apiClient } from "./api.client";
import { AuthResponse, UserProfileResponse } from "@/types";

export interface RegisterPayload {
  email: string;
  password: string;
  full_name: string;
  organization_name: string;
  organization_slug?: string;
}

export interface LoginPayload {
  email: string;
  password: string;
}

export const authService = {
  /**
   * Registers a new merchant organization and owner account.
   * Calls: POST /api/v1/auth/register (backend/app/modules/auth/router.py:40)
   */
  async register(payload: RegisterPayload): Promise<AuthResponse> {
    const data = await apiClient<AuthResponse>("/auth/register", {
      method: "POST",
      body: JSON.stringify(payload),
    });
    this.saveSession(data);
    return data;
  },

  /**
   * Authenticates user credentials and returns JWT bearer token.
   * Calls: POST /api/v1/auth/login (backend/app/modules/auth/router.py:60)
   */
  async login(payload: LoginPayload): Promise<AuthResponse> {
    const data = await apiClient<AuthResponse>("/auth/login", {
      method: "POST",
      body: JSON.stringify(payload),
    });
    this.saveSession(data);
    return data;
  },

  /**
   * Retrieves active authenticated profile and role.
   * Calls: GET /api/v1/auth/me (backend/app/modules/auth/router.py:82)
   */
  async getMe(): Promise<UserProfileResponse> {
    return apiClient<UserProfileResponse>("/auth/me");
  },

  saveSession(auth: AuthResponse): void {
    if (typeof window === "undefined") return;
    localStorage.setItem("chatrio_access_token", auth.access_token);
    localStorage.setItem("chatrio_user", JSON.stringify(auth.user));
    localStorage.setItem("chatrio_org", JSON.stringify(auth.organization));
  },

  clearSession(): void {
    if (typeof window === "undefined") return;
    localStorage.removeItem("chatrio_access_token");
    localStorage.removeItem("chatrio_user");
    localStorage.removeItem("chatrio_org");
  },
};

