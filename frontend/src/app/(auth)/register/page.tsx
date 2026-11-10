"use client";

/**
 * Chatrio Store Registration.
 *
 * Implements design-taste-frontend standards:
 * - Quiet panels, warm canvas (#FAF8F5), terracotta (#EA580C) accents
 */

import React, { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Mail, Lock, User, Store, ArrowRight } from "lucide-react";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { useAuth } from "@/context/AuthContext";

export default function RegisterPage() {
  const router = useRouter();
  const { register } = useAuth();
  const [fullName, setFullName] = useState("");
  const [storeName, setStoreName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setIsLoading(true);

    try {
      await register({
        full_name: fullName.trim(),
        organization_name: storeName.trim(),
        email: email.trim(),
        password,
      });
      router.push("/");
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to register merchant account.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-4 canvas-glow relative overflow-hidden">
      <div className="absolute top-1/4 right-1/2 w-96 h-96 bg-accent/10 rounded-full blur-[120px] pointer-events-none" />

      <div className="w-full max-w-md quiet-panel rounded-2xl shadow-elevated p-6 sm:p-8 z-10">
        <div className="flex flex-col items-center text-center mb-6">
          <div className="w-12 h-12 rounded-2xl bg-accent text-white flex items-center justify-center font-bold font-mono text-2xl shadow-sm mb-4">
            C.
          </div>
          <h1 className="text-2xl font-bold text-ink-900 tracking-tight">Create your Store</h1>
          <p className="text-xs text-ink-500 mt-1">
            Deploy your autonomous WhatsApp commerce agent on Chatrio
          </p>
        </div>

        {error && (
          <div className="mb-5 p-3 rounded-xl bg-rose-50 border border-rose-200 text-xs text-rose-700">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-3.5">
          <Input
            label="Store / Business Name"
            placeholder="e.g. Acme Organic Market"
            value={storeName}
            onChange={(e) => setStoreName(e.target.value)}
            icon={<Store className="w-4 h-4" />}
            required
          />

          <Input
            label="Your Full Name"
            placeholder="e.g. John Doe"
            value={fullName}
            onChange={(e) => setFullName(e.target.value)}
            icon={<User className="w-4 h-4" />}
            required
          />

          <Input
            label="Business Email"
            type="email"
            placeholder="owner@store.com"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            icon={<Mail className="w-4 h-4" />}
            required
          />

          <Input
            label="Password"
            type="password"
            placeholder="Min 8 characters"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            icon={<Lock className="w-4 h-4" />}
            required
          />

          <Button type="submit" className="w-full mt-2" size="lg" isLoading={isLoading}>
            Deploy Store Agent <ArrowRight className="w-4 h-4" />
          </Button>
        </form>

        <p className="text-center text-xs text-ink-500 mt-6 pt-5 border-t border-border">
          Already have a merchant account?{" "}
          <Link href="/login" className="text-accent hover:text-accent-hover font-bold">
            Sign in
          </Link>
        </p>
      </div>
    </div>
  );
}
