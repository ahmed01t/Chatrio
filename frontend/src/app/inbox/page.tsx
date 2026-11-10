"use client";

import React, { useEffect, useState, useRef } from "react";
import {
  MessageSquare,
  Search,
  Bot,
  User,
  Send,
  PauseCircle,
  PlayCircle,
  Clock,
  Sparkles,
  Phone,
  ShieldAlert,
} from "lucide-react";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { Conversation, Message } from "@/types";
import { api } from "@/lib/api";

export default function InboxPage() {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [selectedConv, setSelectedConv] = useState<Conversation | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [filterMode, setFilterMode] = useState<"all" | "human" | "ai">("all");
  const [replyText, setReplyText] = useState("");
  const [isSending, setIsSending] = useState(false);
  const [isTogglingAi, setIsTogglingAi] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Poll conversations & active messages
  useEffect(() => {
    async function fetchConvs() {
      try {
        const data = await api.getConversations();
        setConversations(data);
        if (data.length > 0 && !selectedConv) {
          setSelectedConv(data[0]);
        }
      } catch (err) {
        console.error("Failed to load conversations:", err);
      }
    }
    fetchConvs();
    const interval = setInterval(fetchConvs, 3000);
    return () => clearInterval(interval);
  }, [selectedConv]);

  // Load message transcript when selected conversation changes
  useEffect(() => {
    if (!selectedConv) return;
    async function fetchMessages() {
      if (!selectedConv) return;
      try {
        const msgs = await api.getMessages(selectedConv.id);
        setMessages(msgs);
      } catch (err) {
        console.error("Failed to load messages:", err);
      }
    }
    fetchMessages();
    const interval = setInterval(fetchMessages, 2500);
    return () => clearInterval(interval);
  }, [selectedConv]);

  // Auto-scroll to bottom of chat
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedConv || !replyText.trim()) return;

    setIsSending(true);
    try {
      const newMsg = await api.sendMessage(selectedConv.id, replyText.trim());
      setMessages((prev) => [...prev, newMsg]);
      setReplyText("");
    } catch (err) {
      console.error("Failed to send message:", err);
    } finally {
      setIsSending(false);
    }
  };

  const handleToggleTakeover = async () => {
    if (!selectedConv) return;
    setIsTogglingAi(true);
    try {
      const updated = await api.toggleTakeover(selectedConv.id, !selectedConv.is_ai_active);
      setSelectedConv(updated);
      setConversations((prev) =>
        prev.map((c) => (c.id === updated.id ? { ...c, is_ai_active: updated.is_ai_active } : c))
      );
    } catch (err) {
      console.error("Failed to toggle AI takeover:", err);
    } finally {
      setIsTogglingAi(false);
    }
  };

  const filteredConvs = conversations.filter((c) => {
    const matchSearch =
      (c.customer_phone || "").toLowerCase().includes(searchQuery.toLowerCase()) ||
      (c.customer_name || "").toLowerCase().includes(searchQuery.toLowerCase());
    if (!matchSearch) return false;
    if (filterMode === "human") return !c.is_ai_active;
    if (filterMode === "ai") return c.is_ai_active;
    return true;
  });

  return (
    <div className="h-[calc(100vh-6.5rem)] bg-obsidian-900 border border-obsidian-750/90 rounded-2xl shadow-card overflow-hidden flex flex-col md:flex-row">
      {/* ---------------------------------------------------------------------- */}
      {/* Left Column: Conversations List */}
      {/* ---------------------------------------------------------------------- */}
      <div className="w-full md:w-80 lg:w-96 border-b md:border-b-0 md:border-r border-obsidian-750/80 flex flex-col bg-obsidian-850/60 shrink-0">
        {/* Inbox Search & Filter Header */}
        <div className="p-3.5 border-b border-obsidian-750/70 space-y-2.5">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-bold text-white tracking-tight flex items-center gap-2">
              <MessageSquare className="w-4 h-4 text-brand-emerald" />
              <span>WhatsApp Inquiries</span>
            </h2>
            <Badge variant="active" size="sm">
              {conversations.length} Active
            </Badge>
          </div>

          <div className="relative">
            <Search className="w-3.5 h-3.5 absolute left-3 top-1/2 -translate-y-1/2 text-obsidian-400" />
            <input
              type="text"
              placeholder="Filter by phone or name..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full bg-obsidian-900 border border-obsidian-700/80 rounded-lg pl-8 pr-3 py-1.5 text-xs text-obsidian-100 placeholder:text-obsidian-500 focus:outline-none focus:border-brand-emerald"
            />
          </div>

          {/* Filter Pills */}
          <div className="flex gap-1.5">
            <button
              onClick={() => setFilterMode("all")}
              className={`px-2.5 py-1 rounded-md text-[11px] font-medium transition-colors ${
                filterMode === "all"
                  ? "bg-obsidian-750 text-white border border-obsidian-650"
                  : "text-obsidian-400 hover:text-white"
              }`}
            >
              All
            </button>
            <button
              onClick={() => setFilterMode("human")}
              className={`px-2.5 py-1 rounded-md text-[11px] font-medium transition-colors flex items-center gap-1 ${
                filterMode === "human"
                  ? "bg-amber-500/20 text-amber-300 border border-amber-500/30 font-semibold"
                  : "text-obsidian-400 hover:text-white"
              }`}
            >
              <ShieldAlert className="w-3 h-3 text-amber-400" />
              <span>Human Needed</span>
            </button>
            <button
              onClick={() => setFilterMode("ai")}
              className={`px-2.5 py-1 rounded-md text-[11px] font-medium transition-colors ${
                filterMode === "ai"
                  ? "bg-sky-500/20 text-sky-300 border border-sky-500/30 font-semibold"
                  : "text-obsidian-400 hover:text-white"
              }`}
            >
              AI Active
            </button>
          </div>
        </div>

        {/* Conversations Scrollable List */}
        <div className="flex-1 overflow-y-auto divide-y divide-obsidian-750/40">
          {filteredConvs.length === 0 ? (
            <div className="p-6 text-center text-xs text-obsidian-400">
              No matching customer conversations found.
            </div>
          ) : (
            filteredConvs.map((conv) => {
              const isSelected = selectedConv?.id === conv.id;
              return (
                <button
                  key={conv.id}
                  onClick={() => setSelectedConv(conv)}
                  className={`w-full text-left p-3.5 flex items-start gap-3 transition-colors ${
                    isSelected
                      ? "bg-obsidian-800 border-l-2 border-brand-emerald"
                      : "hover:bg-obsidian-800/50"
                  }`}
                >
                  <div className="w-9 h-9 rounded-xl bg-obsidian-750 border border-obsidian-700 flex items-center justify-center font-mono font-bold text-xs text-white shrink-0 mt-0.5">
                    {conv.customer_name ? conv.customer_name[0] : "C"}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between gap-1">
                      <p className="text-xs font-semibold text-white truncate">
                        {conv.customer_name || conv.customer_phone || "Customer"}
                      </p>
                      <span className="text-[10px] text-obsidian-500 font-mono shrink-0">
                        {conv.created_at ? new Date(conv.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : "Active"}
                      </span>
                    </div>

                    <p className="text-[11px] text-obsidian-400 font-mono mt-0.5 truncate">
                      {conv.customer_phone}
                    </p>

                    <div className="flex items-center justify-between gap-2 mt-2">
                      <p className="text-xs text-obsidian-300 truncate">
                        {conv.last_message_snippet || "Customer started conversation"}
                      </p>
                      {conv.is_ai_active ? (
                        <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-sky-500/10 text-sky-400 border border-sky-500/20 shrink-0">
                          AI
                        </span>
                      ) : (
                        <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-amber-500/10 text-amber-400 border border-amber-500/20 font-bold shrink-0">
                          HANDOVER
                        </span>
                      )}
                    </div>
                  </div>
                </button>
              );
            })
          )}
        </div>
      </div>

      {/* ---------------------------------------------------------------------- */}
      {/* Right Column: Chat Transcript & Human Copilot Action Bar */}
      {/* ---------------------------------------------------------------------- */}
      {selectedConv ? (
        <div className="flex-1 flex flex-col bg-obsidian-950/70 min-w-0">
          {/* Top Bar of Active Chat */}
          <div className="h-16 px-5 border-b border-obsidian-750/70 flex items-center justify-between bg-obsidian-900/90 backdrop-blur shrink-0">
            <div className="flex items-center gap-3 min-w-0">
              <div className="w-9 h-9 rounded-xl bg-obsidian-800 border border-obsidian-700 flex items-center justify-center font-mono font-bold text-xs text-white">
                {selectedConv.customer_name ? selectedConv.customer_name[0] : "C"}
              </div>
              <div className="min-w-0">
                <div className="flex items-center gap-2">
                  <h3 className="text-sm font-bold text-white truncate">
                    {selectedConv.customer_name || selectedConv.customer_phone}
                  </h3>
                  <Badge variant="active" size="sm">
                    WhatsApp Cloud
                  </Badge>
                </div>
                <div className="flex items-center gap-2 text-xs text-obsidian-400 font-mono">
                  <Phone className="w-3 h-3 text-obsidian-500" />
                  <span>{selectedConv.customer_phone}</span>
                </div>
              </div>
            </div>

            {/* Crucial Human in the Loop (HITL) AI Takeover Toggle Button */}
            <div className="flex items-center gap-3">
              <div className="hidden lg:flex items-center gap-1.5 text-xs text-obsidian-400 font-mono">
                <Clock className="w-3.5 h-3.5 text-brand-emerald" />
                <span>24h Window: OPEN</span>
              </div>

              {selectedConv.is_ai_active ? (
                <Button
                  variant="secondary"
                  size="sm"
                  onClick={handleToggleTakeover}
                  isLoading={isTogglingAi}
                  className="border-amber-500/30 text-amber-300 hover:bg-amber-500/10"
                >
                  <PauseCircle className="w-4 h-4 text-amber-400" />
                  <span>Pause AI (Take Over)</span>
                </Button>
              ) : (
                <Button
                  variant="primary"
                  size="sm"
                  onClick={handleToggleTakeover}
                  isLoading={isTogglingAi}
                >
                  <PlayCircle className="w-4 h-4" />
                  <span>Resume AI Copilot</span>
                </Button>
              )}
            </div>
          </div>

          {/* Message Transcript Bubbles */}
          <div className="flex-1 overflow-y-auto p-4 sm:p-6 space-y-4">
            {messages.length === 0 ? (
              <div className="h-full flex flex-col items-center justify-center text-center p-8 text-obsidian-400 space-y-2">
                <Bot className="w-8 h-8 text-obsidian-600 animate-bounce" />
                <p className="text-xs">No messages exchanged yet in this session.</p>
              </div>
            ) : (
              messages.map((msg) => {
                const isCustomer = msg.direction === "INBOUND" || msg.sender_type === "CUSTOMER";
                const isAi = msg.sender_type === "AI_AGENT";
                const isHumanStaff = msg.sender_type === "HUMAN_AGENT";

                return (
                  <div
                    key={msg.id}
                    className={`flex flex-col ${isCustomer ? "items-start" : "items-end"}`}
                  >
                    <div className="flex items-center gap-1.5 mb-1 px-1 text-[11px] font-mono text-obsidian-400">
                      {isCustomer ? (
                        <>
                          <User className="w-3 h-3 text-obsidian-400" />
                          <span>Customer</span>
                        </>
                      ) : isAi ? (
                        <>
                          <Bot className="w-3 h-3 text-brand-cyan" />
                          <span className="text-brand-cyan font-bold">Chatrio AI Agent</span>
                        </>
                      ) : (
                        <>
                          <Sparkles className="w-3 h-3 text-brand-emerald" />
                          <span className="text-brand-emerald font-bold">Store Staff (You)</span>
                        </>
                      )}
                      <span>•</span>
                      <span>
                        {msg.created_at ? new Date(msg.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : "Just now"}
                      </span>
                    </div>

                    <div
                      className={`max-w-lg rounded-2xl p-3.5 text-xs sm:text-sm leading-relaxed shadow-sm ${
                        isCustomer
                          ? "bg-obsidian-850 text-obsidian-100 border border-obsidian-700/80 rounded-tl-sm"
                          : isAi
                          ? "bg-obsidian-800 text-white border border-brand-cyan/30 rounded-tr-sm shadow-glow-cyan"
                          : "bg-emerald-950/60 text-emerald-100 border border-brand-emerald/40 rounded-tr-sm shadow-glow"
                      }`}
                    >
                      {msg.text_body}
                    </div>
                  </div>
                );
              })
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Message Composer Form */}
          <div className="p-3 sm:p-4 bg-obsidian-900 border-t border-obsidian-750/70">
            {!selectedConv.is_ai_active && (
              <div className="mb-2 px-3 py-1.5 rounded-lg bg-amber-500/10 border border-amber-500/20 text-xs text-amber-300 flex items-center justify-between">
                <span>⚠️ AI Copilot is paused. You are chatting directly as a human merchant.</span>
                <button
                  type="button"
                  onClick={handleToggleTakeover}
                  className="font-bold underline hover:text-white"
                >
                  Resume AI
                </button>
              </div>
            )}

            <form onSubmit={handleSendMessage} className="flex gap-2">
              <input
                type="text"
                placeholder="Type your WhatsApp reply here (atomically enqueued in outbox)..."
                value={replyText}
                onChange={(e) => setReplyText(e.target.value)}
                className="flex-1 bg-obsidian-850 border border-obsidian-700/80 rounded-xl px-4 py-2.5 text-xs sm:text-sm text-white placeholder:text-obsidian-500 focus:outline-none focus:border-brand-emerald focus:ring-1 focus:ring-brand-emerald"
              />
              <Button type="submit" size="md" isLoading={isSending} disabled={!replyText.trim()}>
                <Send className="w-4 h-4" />
                <span className="hidden sm:inline">Send</span>
              </Button>
            </form>
          </div>
        </div>
      ) : (
        <div className="flex-1 flex flex-col items-center justify-center p-8 text-center text-obsidian-400">
          <MessageSquare className="w-12 h-12 text-obsidian-700 mb-3" />
          <h3 className="text-sm font-semibold text-white">No conversation selected</h3>
          <p className="text-xs text-obsidian-500 mt-1">Select a customer chat on the left to begin.</p>
        </div>
      )}
    </div>
  );
}

