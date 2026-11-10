"use client";

import React, { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Mail, Lock, User, Store, ArrowRight, DollarSign } from "lucide-react";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { useAuth } from "@/context/AuthContext";

export default function RegisterPage() {
  const router = useRouter();
  const { register } = useAuth();
  const [name, setName] = useState("");
  const [storeName, setStoreName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [currency, setCurrency] = useState("USD");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setIsLoading(true);

    try {
      await register({
        name,
        organization_name: storeName,
        email,
        password,
        currency,
      });
      router.push("/");
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to register store.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-4 bg-obsidian-950 relative overflow-hidden">
      <div className="absolute top-1/4 right-1/2 w-96 h-96 bg-brand-emerald/10 rounded-full blur-[120px] pointer-events-none" />

      <div className="w-full max-w-md bg-obsidian-850/90 border border-obsidian-750/90 rounded-2xl shadow-2xl p-6 sm:p-8 backdrop-blur z-10">
        <div className="flex flex-col items-center text-center mb-6">
          <div className="w-12 h-12 rounded-2xl bg-gradient-to-tr from-brand-emerald to-brand-whatsapp flex items-center justify-center text-obsidian-950 font-bold font-mono text-2xl shadow-glow mb-4">
            C.
          </div>
          <h1 className="text-2xl font-bold text-white tracking-tight">Create your Store</h1>
          <p className="text-xs text-obsidian-400 mt-1">
            Deploy your autonomous WhatsApp commerce agent in minutes
          </p>
        </div>

        {error && (
          <div className="mb-5 p-3 rounded-lg bg-brand-rose/10 border border-brand-rose/30 text-xs text-rose-300">
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
            value={name}
            onChange={(e) => setName(e.target.value)}
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
            placeholder="Min 8 characters with numbers"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            icon={<Lock className="w-4 h-4" />}
            required
          />

          <div className="space-y-1.5">
            <label className="block text-xs font-medium text-obsidian-300">
              Store Currency
            </label>
            <div className="relative">
              <DollarSign className="w-4 h-4 absolute left-3.5 top-1/2 -translate-y-1/2 text-obsidian-400 pointer-events-none" />
              <select
                value={currency}
                onChange={(e) => setCurrency(e.target.value)}
                className="w-full bg-obsidian-900 border border-obsidian-700/80 rounded-lg pl-10 pr-3.5 py-2 text-sm text-obsidian-100 focus:outline-none focus:border-brand-emerald focus:ring-1 focus:ring-brand-emerald"
              >
                <option value="USD">USD — US Dollar ($)</option>
                <option value="EUR">EUR — Euro (€)</option>
                <option value="GBP">GBP — British Pound (£)</option>
                <option value="PKR">PKR — Pakistani Rupee (Rs)</option>
                <option value="INR">INR — Indian Rupee (₹)</option>
                <option value="AED">AED — UAE Dirham (د.إ)</option>
                <option value="CAD">CAD — Canadian Dollar ($)</option>
              </select>
            </div>
          </div>

          <Button type="submit" className="w-full mt-3" size="lg" isLoading={isLoading}>
            Deploy Store Agent <ArrowRight className="w-4 h-4" />
          </Button>
        </form>

        <p className="mt-5 pt-4 border-t border-obsidian-750/60 text-center text-xs text-obsidian-400">
          Already registered?{" "}
          <Link
            href="/login"
            className="text-brand-emerald hover:text-emerald-300 font-semibold transition-colors"
          >
            Sign in
          </Link>
        </p>
      </div>
    </div>
  );
}

