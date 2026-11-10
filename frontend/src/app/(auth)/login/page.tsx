"use client";

/**
 * Chatrio Merchant Login.
 *
 * Implements design-taste-frontend standards:
 * - Quiet panels, warm canvas (#FAF8F5), terracotta (#EA580C) accents
 */

import React, { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Mail, Lock, ArrowRight, Sparkles } from "lucide-react";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { useAuth } from "@/context/AuthContext";

export default function LoginPage() {
  const router = useRouter();
  const { login } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setIsLoading(true);

    try {
      await login(email, password);
      router.push("/");
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to sign in. Check your credentials.");
    } finally {
      setIsLoading(false);
    }
  };

  const handleDemoFill = () => {
    setEmail("owner@acmestore.com");
    setPassword("SecurePass123!");
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-4 canvas-glow relative overflow-hidden">
      {/* Background ambient lighting */}
      <div className="absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 w-96 h-96 bg-accent/10 rounded-full blur-[120px] pointer-events-none" />

      <div className="w-full max-w-md quiet-panel rounded-2xl shadow-elevated p-6 sm:p-8 z-10">
        {/* Header */}
        <div className="flex flex-col items-center text-center mb-8">
          <div className="w-12 h-12 rounded-2xl bg-accent text-white flex items-center justify-center font-bold font-mono text-2xl shadow-sm mb-4">
            C.
          </div>
          <h1 className="text-2xl font-bold text-ink-900 tracking-tight">Sign in to Chatrio</h1>
          <p className="text-xs text-ink-500 mt-1.5">
            Autonomous WhatsApp Conversational Commerce Engine
          </p>
        </div>

        {error && (
          <div className="mb-5 p-3 rounded-xl bg-rose-50 border border-rose-200 text-xs text-rose-700">
            {error}
          </div>
        )}

        {/* Form */}
        <form onSubmit={handleSubmit} className="space-y-4">
          <Input
            label="Email address"
            type="email"
            placeholder="merchant@store.com"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            icon={<Mail className="w-4 h-4" />}
            required
          />

          <Input
            label="Password"
            type="password"
            placeholder="••••••••••••"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            icon={<Lock className="w-4 h-4" />}
            required
          />

          <Button type="submit" className="w-full mt-2" size="lg" isLoading={isLoading}>
            Sign in to Dashboard <ArrowRight className="w-4 h-4" />
          </Button>
        </form>

        {/* Demo Credentials Helper */}
        <div className="mt-6 pt-5 border-t border-border flex flex-col gap-3">
          <button
            type="button"
            onClick={handleDemoFill}
            className="w-full flex items-center justify-center gap-1.5 py-2 px-3 rounded-xl bg-canvas-subtle hover:bg-canvas-warm border border-border text-xs text-ink-700 hover:text-ink-900 transition-colors font-semibold"
          >
            <Sparkles className="w-3.5 h-3.5 text-accent" />
            <span>Fill Demo Credentials (Acme Store)</span>
          </button>

          <p className="text-center text-xs text-ink-500">
            Don&apos;t have a merchant account?{" "}
            <Link href="/register" className="text-accent hover:text-accent-hover font-bold">
              Register Store
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
