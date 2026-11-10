"use client";

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
    <div className="min-h-screen flex items-center justify-center p-4 bg-obsidian-950 relative overflow-hidden">
      {/* Background ambient lighting */}
      <div className="absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 w-96 h-96 bg-brand-emerald/10 rounded-full blur-[120px] pointer-events-none" />
      <div className="absolute bottom-1/4 right-1/4 w-80 h-80 bg-brand-cyan/10 rounded-full blur-[100px] pointer-events-none" />

      <div className="w-full max-w-md bg-obsidian-850/90 border border-obsidian-750/90 rounded-2xl shadow-2xl p-6 sm:p-8 backdrop-blur z-10">
        {/* Header */}
        <div className="flex flex-col items-center text-center mb-8">
          <div className="w-12 h-12 rounded-2xl bg-gradient-to-tr from-brand-emerald to-brand-whatsapp flex items-center justify-center text-obsidian-950 font-bold font-mono text-2xl shadow-glow mb-4">
            C.
          </div>
          <h1 className="text-2xl font-bold text-white tracking-tight">Sign in to Chatrio</h1>
          <p className="text-xs text-obsidian-400 mt-1.5">
            Autonomous WhatsApp Conversational Commerce Engine
          </p>
        </div>

        {error && (
          <div className="mb-5 p-3 rounded-lg bg-brand-rose/10 border border-brand-rose/30 text-xs text-rose-300">
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
        <div className="mt-6 pt-5 border-t border-obsidian-750/60 flex flex-col gap-3">
          <button
            type="button"
            onClick={handleDemoFill}
            className="w-full flex items-center justify-center gap-1.5 py-2 px-3 rounded-lg bg-obsidian-800 hover:bg-obsidian-750 border border-obsidian-700 text-xs text-obsidian-300 hover:text-white transition-colors"
          >
            <Sparkles className="w-3.5 h-3.5 text-brand-cyan" />
            <span>Fill Demo Credentials (Acme Store)</span>
          </button>

          <p className="text-center text-xs text-obsidian-400">
            Don&apos;t have a merchant account?{" "}
            <Link
              href="/register"
              className="text-brand-emerald hover:text-emerald-300 font-semibold transition-colors"
            >
              Create Store
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}

