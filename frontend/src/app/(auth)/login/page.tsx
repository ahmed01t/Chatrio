"use client";

import { useState } from "react";
import type { FormEvent, JSX } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { ArrowRight, Lock, Mail } from "lucide-react";
import { AuthFrame } from "@/components/auth/AuthFrame";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { useAuth } from "@/context/AuthContext";

export default function LoginPage(): JSX.Element {
  const router = useRouter();
  const { login } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>): Promise<void> => {
    event.preventDefault();
    setError(null);
    setIsLoading(true);
    try {
      await login(email, password);
      router.replace("/");
    } catch (cause: unknown) {
      setError(cause instanceof Error ? cause.message : "Incorrect email or password.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <AuthFrame>
      <div className="w-full max-w-[400px]">
        <div className="mb-6">
          <h1 className="font-display text-3xl font-semibold leading-tight tracking-tight text-ink-900">Sign in to Chatrio</h1>
          <p className="mt-2 text-sm text-ink-500">Pick up where your customers left off.</p>
        </div>

        {error && <div className="mb-5 rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700" role="alert">{error}</div>}

        <div className="quiet-panel p-6">
          <form onSubmit={handleSubmit} className="space-y-4">
            <Input
              label="Email"
              type="email"
              placeholder="you@example.com"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              icon={<Mail className="h-4 w-4" />}
              required
              autoComplete="email"
            />
            <Input
              label="Password"
              type="password"
              placeholder="Enter your password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              icon={<Lock className="h-4 w-4" />}
              required
              autoComplete="current-password"
            />
            <Button type="submit" className="mt-1 w-full" size="md" isLoading={isLoading}>
              Sign in <ArrowRight className="h-4 w-4" />
            </Button>
          </form>
        </div>

        <p className="mt-5 text-sm text-ink-500">
          New to Chatrio? <Link href="/register" className="font-semibold text-accent hover:text-accent-hover">Create an account</Link>
        </p>
      </div>
    </AuthFrame>
  );
}
