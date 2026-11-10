"use client";

/**
 * Chatrio Live Shared WhatsApp & Omnichannel Inbox.
 *
 * Implements design-taste-frontend standards:
 * - Quiet panels, aligned figures, colour spent on data
 * - Warm white canvas (#FAF8F5) with terracotta (#EA580C) data highlights
 * - Real WhatsApp chat transcript with live message delivery receipts (✓ / ✓✓)
 * - 1-Click Human Takeover switch disabling LangGraph copilot
 */

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
  Check,
  CheckCheck,
} from "lucide-react";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { ConversationRead, MessageRead } from "@/types";
import { conversationsService } from "@/services/conversations.service";

export default function InboxPage() {
  const [conversations, setConversations] = useState<ConversationRead[]>([]);
  const [selectedConv, setSelectedConv] = useState<ConversationRead | null>(null);
  const [messages, setMessages] = useState<MessageRead[]>([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [filterMode, setFilterMode] = useState<"all" | "human" | "ai">("all");
  const [replyText, setReplyText] = useState("");
  const [isSending, setIsSending] = useState(false);
  const [isTogglingAi, setIsTogglingAi] = useState(false);
  const [isLoadingConvs, setIsLoadingConvs] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const loadConversations = async () => {
    try {
      const res = await conversationsService.listConversations({ page: 1, page_size: 50 });
      setConversations(res.items);
      if (res.items.length > 0 && !selectedConv) {
        setSelectedConv(res.items[0]);
      }
    } catch (err: unknown) {
      console.error("Failed to load conversations:", err);
    } finally {
      setIsLoadingConvs(false);
    }
  };

  const loadMessages = async (conversationId: string) => {
    try {
      const res = await conversationsService.listMessages(conversationId);
      setMessages(res.items);
    } catch (err: unknown) {
      console.error("Failed to load transcript:", err);
    }
  };

  useEffect(() => {
    loadConversations();
    const interval = setInterval(loadConversations, 3000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    if (!selectedConv) return;
    loadMessages(selectedConv.id);
    const interval = setInterval(() => loadMessages(selectedConv.id), 2500);
    return () => clearInterval(interval);
  }, [selectedConv?.id]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedConv || !replyText.trim()) return;

    setIsSending(true);
    setError(null);
    try {
      const newMsg = await conversationsService.sendMessage(selectedConv.id, replyText.trim());
      setMessages((prev) => [...prev, newMsg]);
      setReplyText("");
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to deliver WhatsApp message.");
    } finally {
      setIsSending(false);
    }
  };

  const handleToggleTakeover = async () => {
    if (!selectedConv) return;
    setIsTogglingAi(true);
    try {
      const updated = await conversationsService.toggleTakeover(
        selectedConv.id,
        !selectedConv.is_ai_active
      );
      setSelectedConv(updated);
      setConversations((prev) =>
        prev.map((c) => (c.id === updated.id ? updated : c))
      );
    } catch (err: unknown) {
      console.error("Failed to toggle takeover:", err);
    } finally {
      setIsTogglingAi(false);
    }
  };

  const filteredConvs = conversations.filter((c) => {
    const phone = c.customer?.phone_number || "";
    const name = c.customer?.name || "";
    const matchSearch =
      phone.toLowerCase().includes(searchQuery.toLowerCase()) ||
      name.toLowerCase().includes(searchQuery.toLowerCase());
    if (!matchSearch) return false;
    if (filterMode === "human") return !c.is_ai_active;
    if (filterMode === "ai") return c.is_ai_active;
    return true;
  });

  return (
    <div className="h-[calc(100vh-6.5rem)] quiet-panel overflow-hidden flex flex-col md:flex-row">
      {/* ---------------------------------------------------------------------- */}
      {/* Left Column: Conversations List */}
      {/* ---------------------------------------------------------------------- */}
      <div className="w-full md:w-80 lg:w-96 border-b md:border-b-0 md:border-r border-border flex flex-col bg-canvas-subtle/40 shrink-0">
        <div className="p-4 border-b border-border space-y-3">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-bold text-ink-900 tracking-tight flex items-center gap-2">
              <MessageSquare className="w-4 h-4 text-accent" />
              <span>WhatsApp Inquiries</span>
            </h2>
            <Badge variant="terracotta" size="sm">
              {conversations.length} Active
            </Badge>
          </div>

          <div className="relative">
            <Search className="w-3.5 h-3.5 absolute left-3 top-1/2 -translate-y-1/2 text-ink-400" />
            <input
              type="text"
              placeholder="Filter phone or name..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full bg-white border border-border rounded-xl pl-8 pr-3 py-1.5 text-xs text-ink-900 placeholder:text-ink-400 focus:outline-none focus:border-accent focus:ring-1 focus:ring-accent transition-all shadow-sm"
            />
          </div>

          <div className="flex gap-1.5">
            <button
              onClick={() => setFilterMode("all")}
              className={`px-2.5 py-1 rounded-lg text-[11px] font-semibold transition-colors ${
                filterMode === "all"
                  ? "bg-white text-ink-900 border border-border shadow-sm"
                  : "text-ink-500 hover:text-ink-900"
              }`}
            >
              All ({conversations.length})
            </button>
            <button
              onClick={() => setFilterMode("human")}
              className={`px-2.5 py-1 rounded-lg text-[11px] font-semibold transition-colors flex items-center gap-1 ${
                filterMode === "human"
                  ? "bg-amber-100 text-amber-800 border border-amber-200"
                  : "text-ink-500 hover:text-ink-900"
              }`}
            >
              <ShieldAlert className="w-3 h-3 text-amber-600" />
              <span>Human Takeover</span>
            </button>
            <button
              onClick={() => setFilterMode("ai")}
              className={`px-2.5 py-1 rounded-lg text-[11px] font-semibold transition-colors ${
                filterMode === "ai"
                  ? "bg-accent-light text-accent border border-accent-subtle"
                  : "text-ink-500 hover:text-ink-900"
              }`}
            >
              AI Active
            </button>
          </div>
        </div>

        {/* Conversations Scrollable List */}
        <div className="flex-1 overflow-y-auto divide-y divide-border/60">
          {filteredConvs.length === 0 && !isLoadingConvs ? (
            <div className="p-8 text-center text-xs text-ink-500 space-y-2">
              <MessageSquare className="w-8 h-8 text-ink-300 mx-auto" />
              <p className="font-semibold text-ink-900">No active customer chats</p>
              <p className="text-[11px] text-ink-400">
                When a customer sends a message to your WhatsApp number, it automatically appears here.
              </p>
            </div>
          ) : (
            filteredConvs.map((conv) => {
              const isSelected = selectedConv?.id === conv.id;
              const phone = conv.customer?.phone_number || "Direct Inbound";
              const name = conv.customer?.name || "Customer";

              return (
                <button
                  key={conv.id}
                  onClick={() => setSelectedConv(conv)}
                  className={`w-full text-left p-3.5 flex items-start gap-3 transition-colors ${
                    isSelected
                      ? "bg-white border-l-2 border-accent shadow-sm"
                      : "hover:bg-canvas-subtle"
                  }`}
                >
                  <div className="w-9 h-9 rounded-xl bg-canvas-subtle border border-border flex items-center justify-center font-mono font-bold text-xs text-ink-900 shrink-0 mt-0.5">
                    {name ? name[0].toUpperCase() : "C"}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between gap-1">
                      <p className="text-xs font-semibold text-ink-900 truncate">{name}</p>
                      <span className="text-[10px] text-ink-400 font-mono shrink-0">
                        {conv.created_at
                          ? new Date(conv.created_at).toLocaleTimeString([], {
                              hour: "2-digit",
                              minute: "2-digit",
                            })
                          : "Active"}
                      </span>
                    </div>

                    <p className="text-[11px] text-ink-500 font-mono mt-0.5 truncate">
                      {phone}
                    </p>

                    <div className="flex items-center justify-between gap-2 mt-2">
                      <span className="text-[10px] font-mono text-ink-400">
                        Channel: {conv.channel}
                      </span>
                      {conv.is_ai_active ? (
                        <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-sky-50 text-sky-700 border border-sky-200 font-semibold shrink-0">
                          AI
                        </span>
                      ) : (
                        <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-amber-50 text-amber-700 border border-amber-200 font-bold shrink-0">
                          HUMAN
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
        <div className="flex-1 flex flex-col bg-canvas-warm/30 min-w-0">
          {/* Top Bar of Active Chat */}
          <div className="h-16 px-5 border-b border-border flex items-center justify-between bg-white shrink-0">
            <div className="flex items-center gap-3 min-w-0">
              <div className="w-9 h-9 rounded-xl bg-canvas-subtle border border-border flex items-center justify-center font-mono font-bold text-xs text-ink-900">
                {selectedConv.customer?.name
                  ? selectedConv.customer.name[0].toUpperCase()
                  : "C"}
              </div>
              <div className="min-w-0">
                <div className="flex items-center gap-2">
                  <h3 className="text-sm font-bold text-ink-900 truncate">
                    {selectedConv.customer?.name || "WhatsApp Customer"}
                  </h3>
                  <Badge variant="neutral" size="sm">
                    {selectedConv.channel}
                  </Badge>
                </div>
                <div className="flex items-center gap-2 text-xs text-ink-500 font-mono">
                  <Phone className="w-3 h-3 text-ink-400" />
                  <span>{selectedConv.customer?.phone_number || "Direct"}</span>
                </div>
              </div>
            </div>

            {/* Human in the loop (HITL) Takeover Switch */}
            <div className="flex items-center gap-3">
              <div className="hidden lg:flex items-center gap-1.5 text-xs text-ink-500 font-mono">
                <Clock className="w-3.5 h-3.5 text-emerald-600" />
                <span>Meta 24h Policy: Active</span>
              </div>

              {selectedConv.is_ai_active ? (
                <Button
                  variant="secondary"
                  size="sm"
                  onClick={handleToggleTakeover}
                  isLoading={isTogglingAi}
                  className="border-amber-300 text-amber-700 hover:bg-amber-50"
                >
                  <PauseCircle className="w-4 h-4 text-amber-600" />
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
              <div className="h-full flex flex-col items-center justify-center text-center p-8 text-ink-400 space-y-2">
                <Bot className="w-8 h-8 text-ink-300 animate-bounce" />
                <p className="text-xs font-semibold text-ink-900">No messages in transcript yet</p>
                <p className="text-[11px] text-ink-500">
                  Messages will appear here as the customer chats with the store.
                </p>
              </div>
            ) : (
              messages.map((msg) => {
                const isCustomer =
                  msg.direction === "INBOUND" || msg.sender_type === "CUSTOMER";
                const isAi = msg.sender_type === "AI_AGENT";

                return (
                  <div
                    key={msg.id}
                    className={`flex flex-col ${isCustomer ? "items-start" : "items-end"}`}
                  >
                    <div className="flex items-center gap-1.5 mb-1 px-1 text-[11px] font-mono text-ink-500">
                      {isCustomer ? (
                        <>
                          <User className="w-3 h-3 text-ink-400" />
                          <span>Customer</span>
                        </>
                      ) : isAi ? (
                        <>
                          <Bot className="w-3 h-3 text-accent" />
                          <span className="text-accent font-bold">Chatrio AI</span>
                        </>
                      ) : (
                        <>
                          <Sparkles className="w-3 h-3 text-emerald-600" />
                          <span className="text-emerald-700 font-bold">Store Staff</span>
                        </>
                      )}
                      <span>&bull;</span>
                      <span>
                        {msg.created_at
                          ? new Date(msg.created_at).toLocaleTimeString([], {
                              hour: "2-digit",
                              minute: "2-digit",
                            })
                          : "Just now"}
                      </span>
                    </div>

                    <div
                      className={`max-w-lg rounded-2xl p-3.5 text-xs sm:text-sm leading-relaxed shadow-sm relative group ${
                        isCustomer
                          ? "bg-white text-ink-900 border border-border rounded-tl-sm"
                          : isAi
                          ? "bg-accent-light text-ink-900 border border-accent-subtle rounded-tr-sm"
                          : "bg-emerald-50 text-emerald-950 border border-emerald-200 rounded-tr-sm"
                      }`}
                    >
                      <p>{msg.text_body}</p>

                      {/* Outbound delivery status receipt */}
                      {!isCustomer && (
                        <div className="flex items-center justify-end gap-1 mt-1 text-[10px] text-ink-400 font-mono">
                          {msg.status === "READ" ? (
                            <span className="flex items-center gap-0.5 text-accent font-semibold" title="Read by customer">
                              <CheckCheck className="w-3 h-3" />
                              <span>Read</span>
                            </span>
                          ) : msg.status === "DELIVERED" ? (
                            <span className="flex items-center gap-0.5 text-ink-600" title="Delivered to WhatsApp">
                              <CheckCheck className="w-3 h-3" />
                              <span>Delivered</span>
                            </span>
                          ) : msg.status === "SENT" ? (
                            <span className="flex items-center gap-0.5 text-ink-400" title="Dispatched from Outbox">
                              <Check className="w-3 h-3" />
                              <span>Sent</span>
                            </span>
                          ) : (
                            <span className="text-amber-600" title="In processing buffer">
                              Pending
                            </span>
                          )}
                        </div>
                      )}
                    </div>
                  </div>
                );
              })
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Message Composer Form */}
          <div className="p-3 sm:p-4 bg-white border-t border-border">
            {error && (
              <div className="mb-2 p-2 rounded-xl bg-rose-50 border border-rose-200 text-xs text-rose-700">
                {error}
              </div>
            )}

            {!selectedConv.is_ai_active && (
              <div className="mb-2 px-3 py-1.5 rounded-xl bg-amber-50 border border-amber-200 text-xs text-amber-800 flex items-center justify-between">
                <span>⚠️ AI Copilot is paused. You are chatting directly as a human merchant.</span>
                <button
                  type="button"
                  onClick={handleToggleTakeover}
                  className="font-bold underline text-amber-900 hover:text-black"
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
                className="flex-1 bg-canvas-subtle border border-border rounded-xl px-4 py-2.5 text-xs sm:text-sm text-ink-900 placeholder:text-ink-400 focus:outline-none focus:border-accent focus:bg-white focus:ring-1 focus:ring-accent transition-all shadow-sm"
              />
              <Button
                type="submit"
                size="md"
                isLoading={isSending}
                disabled={!replyText.trim()}
              >
                <Send className="w-4 h-4" />
                <span className="hidden sm:inline">Send to WhatsApp</span>
              </Button>
            </form>
          </div>
        </div>
      ) : (
        <div className="flex-1 flex flex-col items-center justify-center p-8 text-center text-ink-400">
          <MessageSquare className="w-12 h-12 text-ink-300 mb-3" />
          <h3 className="text-sm font-semibold text-ink-900">No conversation selected</h3>
          <p className="text-xs text-ink-500 mt-1">
            Select a customer chat on the left to begin.
          </p>
        </div>
      )}
    </div>
  );
}
