"use client";

import React, { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Mail, Lock, ArrowRight } from "lucide-react";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { useAuth } from "@/context/AuthContext";

export default function LoginPage() {
  const router   = useRouter();
  const { login } = useAuth();

  const [email,     setEmail]     = useState("");
  const [password,  setPassword]  = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error,     setError]     = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setIsLoading(true);
    try {
      await login(email, password);
      router.push("/");
    } catch (err: unknown) {
      setError(
        err instanceof Error ? err.message : "Incorrect email or password."
      );
    } finally {
      setIsLoading(false);
    }
  };

  return (
    /* Full-screen warm canvas */
    <div className="min-h-screen canvas-glow flex items-center justify-center p-4">
      <div className="w-full max-w-[400px] animate-fade-up">

        {/* Logo mark */}
        <div className="flex justify-center mb-8">
          <div
            className="w-10 h-10 rounded-[10px] bg-accent flex items-center
                       justify-center text-white font-semibold text-lg"
          >
            C
          </div>
        </div>

        {/* Heading */}
        <div className="text-center mb-8">
          <h1 className="text-[28px] font-semibold text-ink-900 tracking-tight leading-tight">
            Sign in to Chatrio
          </h1>
          <p className="text-[14px] text-ink-500 mt-2">
            Your WhatsApp store dashboard
          </p>
        </div>

        {/* Error */}
        {error && (
          <div
            className="mb-5 px-4 py-3 rounded-[10px] bg-rose-50
                       border border-rose-200 text-[13px] text-rose-700"
          >
            {error}
          </div>
        )}

        {/* Form card */}
        <div className="quiet-panel p-6 space-y-4">
          <form onSubmit={handleSubmit} className="space-y-4">
            <Input
              label="Email"
              type="email"
              placeholder="you@example.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              icon={<Mail className="w-4 h-4" />}
              required
              autoComplete="email"
            />

            <Input
              label="Password"
              type="password"
              placeholder="••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              icon={<Lock className="w-4 h-4" />}
              required
              autoComplete="current-password"
            />

            <Button
              type="submit"
              className="w-full mt-1"
              size="md"
              isLoading={isLoading}
            >
              Sign in
              <ArrowRight className="w-4 h-4" />
            </Button>
          </form>
        </div>

        {/* Footer */}
        <p className="text-center text-[13px] text-ink-500 mt-5">
          No account?{" "}
          <Link
            href="/register"
            className="text-accent font-medium hover:text-accent-hover transition-colors"
          >
            Create one
          </Link>
        </p>
      </div>
    </div>
  );
}
