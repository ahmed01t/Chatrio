"use client";

import React, { createContext, useCallback, useContext, useEffect, useState } from "react";
import { OrganizationRead, UserRead } from "@/types";
import { authService, RegisterPayload } from "@/services/auth.service";

interface AuthContextType {
  user: UserRead | null;
  organization: OrganizationRead | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, pass: string) => Promise<void>;
  register: (payload: RegisterPayload) => Promise<void>;
  logout: () => void;
  updateOrganizationState: (org: OrganizationRead) => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<UserRead | null>(null);
  const [organization, setOrganization] = useState<OrganizationRead | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // Restore session from localStorage on application mount
    const token = typeof window !== "undefined" ? localStorage.getItem("chatrio_access_token") : null;
    const storedUser = typeof window !== "undefined" ? localStorage.getItem("chatrio_user") : null;
    const storedOrg = typeof window !== "undefined" ? localStorage.getItem("chatrio_org") : null;

    if (token && storedUser && storedOrg) {
      try {
        setUser(JSON.parse(storedUser));
        setOrganization(JSON.parse(storedOrg));
      } catch {
        authService.clearSession();
      }
    }
    setIsLoading(false);
  }, []);

  const login = async (email: string, pass: string) => {
    setIsLoading(true);
    try {
      const res = await authService.login({ email, password: pass });
      setUser(res.user);
      setOrganization(res.organization);
    } finally {
      setIsLoading(false);
    }
  };

  const register = async (payload: RegisterPayload) => {
    setIsLoading(true);
    try {
      const res = await authService.register(payload);
      setUser(res.user);
      setOrganization(res.organization);
    } finally {
      setIsLoading(false);
    }
  };

  const logout = () => {
    authService.clearSession();
    setUser(null);
    setOrganization(null);
    if (typeof window !== "undefined") {
      window.location.href = "/login";
    }
  };

  const updateOrganizationState = useCallback((org: OrganizationRead) => {
    setOrganization(org);
    if (typeof window !== "undefined") {
      localStorage.setItem("chatrio_org", JSON.stringify(org));
    }
  }, []);

  return (
    <AuthContext.Provider
      value={{
        user,
        organization,
        isAuthenticated: !!user,
        isLoading,
        login,
        register,
        logout,
        updateOrganizationState,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
