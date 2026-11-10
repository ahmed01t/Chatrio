"use client";

import React, { useState } from "react";
import {
  Settings,
  Store,
  Phone,
  Bot,
  Key,
  Save,
  CheckCircle2,
  Copy,
} from "lucide-react";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { useAuth } from "@/context/AuthContext";

export default function SettingsPage() {
  const { organization } = useAuth();
  const [storeName, setStoreName] = useState(organization?.name || "Acme Superstore");
  const [currency, setCurrency] = useState("USD");
  const [phoneId, setPhoneId] = useState("109823489234892");
  const [welcomeMessage, setWelcomeMessage] = useState(
    "Hello! Welcome to our store. How can I help you browse our products today?"
  );
  const [copied, setCopied] = useState(false);
  const [isSaved, setIsSaved] = useState(false);

  const webhookUrl = "https://api.chatrio.com/api/v1/webhooks/whatsapp";

  const handleCopyWebhook = () => {
    navigator.clipboard.writeText(webhookUrl);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleSave = (e: React.FormEvent) => {
    e.preventDefault();
    setIsSaved(true);
    setTimeout(() => setIsSaved(false), 3000);
  };

  return (
    <div className="space-y-6 max-w-4xl animate-in fade-in duration-150">
      {/* Header */}
      <div className="pb-2 border-b border-obsidian-800">
        <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-white flex items-center gap-2">
          <Settings className="w-6 h-6 text-brand-emerald" />
          <span>Store & WhatsApp Settings</span>
        </h1>
        <p className="text-xs sm:text-sm text-obsidian-400 mt-1">
          Configure your merchant profile, WhatsApp credentials, and AI persona.
        </p>
      </div>

      {isSaved && (
        <div className="p-3.5 rounded-xl bg-brand-emerald/10 border border-brand-emerald/30 text-xs text-brand-emerald flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4" />
          <span>Store settings successfully updated and synchronized!</span>
        </div>
      )}

      <form onSubmit={handleSave} className="space-y-6">
        {/* Store Profile Card */}
        <div className="bg-obsidian-850/80 border border-obsidian-750/90 rounded-xl p-5 shadow-card space-y-4">
          <h3 className="text-sm font-semibold text-white tracking-tight flex items-center gap-2">
            <Store className="w-4 h-4 text-brand-emerald" />
            <span>Store Profile & Currency</span>
          </h3>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <Input
              label="Store Display Name"
              value={storeName}
              onChange={(e) => setStoreName(e.target.value)}
              required
            />
            <div className="space-y-1.5">
              <label className="block text-xs font-medium text-obsidian-300">
                Operating Currency
              </label>
              <select
                value={currency}
                onChange={(e) => setCurrency(e.target.value)}
                className="w-full bg-obsidian-900 border border-obsidian-700/80 rounded-lg px-3.5 py-2 text-sm text-obsidian-100 focus:outline-none focus:border-brand-emerald"
              >
                <option value="USD">USD ($) — US Dollar</option>
                <option value="EUR">EUR (€) — Euro</option>
                <option value="GBP">GBP (£) — British Pound</option>
                <option value="PKR">PKR (Rs) — Pakistani Rupee</option>
                <option value="INR">INR (₹) — Indian Rupee</option>
                <option value="AED">AED (د.إ) — UAE Dirham</option>
              </select>
            </div>
          </div>
        </div>

        {/* WhatsApp Integration Card */}
        <div className="bg-obsidian-850/80 border border-obsidian-750/90 rounded-xl p-5 shadow-card space-y-4">
          <h3 className="text-sm font-semibold text-white tracking-tight flex items-center gap-2">
            <Phone className="w-4 h-4 text-brand-cyan" />
            <span>Meta WhatsApp Cloud API Connection</span>
          </h3>

          <div className="space-y-3.5">
            <Input
              label="Meta Phone Number ID"
              value={phoneId}
              onChange={(e) => setPhoneId(e.target.value)}
              icon={<Key className="w-4 h-4" />}
              required
            />

            <div className="space-y-1.5">
              <label className="block text-xs font-medium text-obsidian-300">
                Webhook Callback URL (Meta Developers Portal)
              </label>
              <div className="flex gap-2">
                <input
                  type="text"
                  readOnly
                  value={webhookUrl}
                  className="flex-1 bg-obsidian-900 border border-obsidian-700/80 rounded-lg px-3.5 py-2 text-xs font-mono text-obsidian-300 select-all"
                />
                <Button type="button" variant="secondary" size="sm" onClick={handleCopyWebhook}>
                  <Copy className="w-3.5 h-3.5" />
                  <span>{copied ? "Copied!" : "Copy"}</span>
                </Button>
              </div>
            </div>
          </div>
        </div>

        {/* AI Agent Persona Card */}
        <div className="bg-obsidian-850/80 border border-obsidian-750/90 rounded-xl p-5 shadow-card space-y-4">
          <h3 className="text-sm font-semibold text-white tracking-tight flex items-center gap-2">
            <Bot className="w-4 h-4 text-brand-purple" />
            <span>AI Agent Persona & Greetings</span>
          </h3>

          <div className="space-y-1.5">
            <label className="block text-xs font-medium text-obsidian-300">
              Welcome Greeting Message
            </label>
            <textarea
              rows={3}
              value={welcomeMessage}
              onChange={(e) => setWelcomeMessage(e.target.value)}
              className="w-full bg-obsidian-900 border border-obsidian-700/80 rounded-lg p-3 text-xs text-obsidian-100 placeholder:text-obsidian-500 focus:outline-none focus:border-brand-emerald"
            />
            <p className="text-[11px] text-obsidian-500">
              This message is automatically delivered when a new customer initiates a conversation.
            </p>
          </div>
        </div>

        {/* Save Button */}
        <div className="flex justify-end pt-2">
          <Button type="submit" size="md">
            <Save className="w-4 h-4" />
            <span>Save Store Configuration</span>
          </Button>
        </div>
      </form>
    </div>
  );
}

