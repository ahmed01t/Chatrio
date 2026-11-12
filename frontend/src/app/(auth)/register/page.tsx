"use client";

import { useState } from "react";
import type { FormEvent, JSX } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { ArrowRight, Lock, Mail, Store, UserRound } from "lucide-react";
import { AuthFrame } from "@/components/auth/AuthFrame";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { useAuth } from "@/context/AuthContext";

export default function RegisterPage(): JSX.Element {
  const router = useRouter();
  const { register } = useAuth();
  const [fullName, setFullName] = useState("");
  const [storeName, setStoreName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>): Promise<void> => {
    event.preventDefault();
    setError(null);
    setIsLoading(true);
    try {
      await register({
        full_name: fullName.trim(),
        organization_name: storeName.trim(),
        email: email.trim(),
        password,
      });
      router.replace("/");
    } catch (cause: unknown) {
      setError(cause instanceof Error ? cause.message : "Could not create account. Please try again.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <AuthFrame>
      <div className="w-full max-w-[420px]">
        <div className="mb-6">
          <h1 className="font-display text-3xl font-semibold leading-tight tracking-tight text-ink-900">Create your store</h1>
          <p className="mt-2 text-sm text-ink-500">Bring your customer conversations into one workspace.</p>
        </div>

        {error && <div className="mb-5 rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700" role="alert">{error}</div>}

        <div className="quiet-panel p-6">
          <form onSubmit={handleSubmit} className="space-y-4">
            <Input
              label="Store name"
              placeholder="e.g. Sunrise Market"
              value={storeName}
              onChange={(event) => setStoreName(event.target.value)}
              icon={<Store className="h-4 w-4" />}
              required
              autoComplete="organization"
            />
            <Input
              label="Your name"
              placeholder="Full name"
              value={fullName}
              onChange={(event) => setFullName(event.target.value)}
              icon={<UserRound className="h-4 w-4" />}
              required
              autoComplete="name"
            />
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
              placeholder="At least 8 characters"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              icon={<Lock className="h-4 w-4" />}
              required
              autoComplete="new-password"
              hint="8 or more characters"
            />
            <Button type="submit" className="mt-1 w-full" size="md" isLoading={isLoading}>
              Create store <ArrowRight className="h-4 w-4" />
            </Button>
          </form>
        </div>

        <p className="mt-5 text-sm text-ink-500">
          Already have an account? <Link href="/login" className="font-semibold text-accent hover:text-accent-hover">Sign in</Link>
        </p>
      </div>
    </AuthFrame>
  );
}
