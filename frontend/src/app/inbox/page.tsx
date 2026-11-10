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
  RefreshCw,
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

  /**
   * Polls conversations from backend router:
   * GET /api/v1/conversations (backend/app/modules/conversations/router.py:58)
   */
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

  /**
   * Polls messages for the selected conversation from backend router:
   * GET /api/v1/conversations/{id}/messages (backend/app/modules/conversations/router.py:166)
   */
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

  /**
   * Sends staff reply through backend router:
   * POST /api/v1/conversations/{id}/messages (backend/app/modules/conversations/router.py:195)
   * This atomically creates an OutboxMessage for guaranteed WhatsApp delivery.
   */
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

  /**
   * Toggles human takeover via backend router:
   * PATCH /api/v1/conversations/{id}/takeover (backend/app/modules/conversations/router.py:113)
   */
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
    <div className="h-[calc(100vh-6.5rem)] bg-obsidian-900 border border-obsidian-750/90 rounded-2xl shadow-card overflow-hidden flex flex-col md:flex-row">
      {/* ---------------------------------------------------------------------- */}
      {/* Left Column: Conversations List */}
      {/* ---------------------------------------------------------------------- */}
      <div className="w-full md:w-80 lg:w-96 border-b md:border-b-0 md:border-r border-obsidian-750/80 flex flex-col bg-obsidian-850/60 shrink-0">
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

          <div className="flex gap-1.5">
            <button
              onClick={() => setFilterMode("all")}
              className={`px-2.5 py-1 rounded-md text-[11px] font-medium transition-colors ${
                filterMode === "all"
                  ? "bg-obsidian-750 text-white border border-obsidian-650"
                  : "text-obsidian-400 hover:text-white"
              }`}
            >
              All ({conversations.length})
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
          {filteredConvs.length === 0 && !isLoadingConvs ? (
            <div className="p-8 text-center text-xs text-obsidian-400 space-y-2">
              <MessageSquare className="w-8 h-8 text-obsidian-600 mx-auto" />
              <p className="font-semibold text-white">No active customer chats</p>
              <p className="text-[11px] text-obsidian-500">
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
                      ? "bg-obsidian-800 border-l-2 border-brand-emerald"
                      : "hover:bg-obsidian-800/50"
                  }`}
                >
                  <div className="w-9 h-9 rounded-xl bg-obsidian-750 border border-obsidian-700 flex items-center justify-center font-mono font-bold text-xs text-white shrink-0 mt-0.5">
                    {name ? name[0].toUpperCase() : "C"}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between gap-1">
                      <p className="text-xs font-semibold text-white truncate">{name}</p>
                      <span className="text-[10px] text-obsidian-500 font-mono shrink-0">
                        {conv.created_at
                          ? new Date(conv.created_at).toLocaleTimeString([], {
                              hour: "2-digit",
                              minute: "2-digit",
                            })
                          : "Active"}
                      </span>
                    </div>

                    <p className="text-[11px] text-obsidian-400 font-mono mt-0.5 truncate">
                      {phone}
                    </p>

                    <div className="flex items-center justify-between gap-2 mt-2">
                      <span className="text-[10px] font-mono text-obsidian-500">
                        Channel: {conv.channel}
                      </span>
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
                {selectedConv.customer?.name
                  ? selectedConv.customer.name[0].toUpperCase()
                  : "C"}
              </div>
              <div className="min-w-0">
                <div className="flex items-center gap-2">
                  <h3 className="text-sm font-bold text-white truncate">
                    {selectedConv.customer?.name || "WhatsApp Customer"}
                  </h3>
                  <Badge variant="active" size="sm">
                    {selectedConv.channel}
                  </Badge>
                </div>
                <div className="flex items-center gap-2 text-xs text-obsidian-400 font-mono">
                  <Phone className="w-3 h-3 text-obsidian-500" />
                  <span>{selectedConv.customer?.phone_number || "Direct"}</span>
                </div>
              </div>
            </div>

            {/* Human in the loop (HITL) Takeover Switch */}
            <div className="flex items-center gap-3">
              <div className="hidden lg:flex items-center gap-1.5 text-xs text-obsidian-400 font-mono">
                <Clock className="w-3.5 h-3.5 text-brand-emerald" />
                <span>Meta 24h Policy: Enforced</span>
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
                <p className="text-xs font-semibold text-white">No messages in transcript yet</p>
                <p className="text-[11px] text-obsidian-500">
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
                    <div className="flex items-center gap-1.5 mb-1 px-1 text-[11px] font-mono text-obsidian-400">
                      {isCustomer ? (
                        <>
                          <User className="w-3 h-3 text-obsidian-400" />
                          <span>Customer</span>
                        </>
                      ) : isAi ? (
                        <>
                          <Bot className="w-3 h-3 text-brand-cyan" />
                          <span className="text-brand-cyan font-bold">Chatrio AI</span>
                        </>
                      ) : (
                        <>
                          <Sparkles className="w-3 h-3 text-brand-emerald" />
                          <span className="text-brand-emerald font-bold">Store Staff (You)</span>
                        </>
                      )}
                      <span>•</span>
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
            {error && (
              <div className="mb-2 p-2 rounded-lg bg-brand-rose/10 border border-brand-rose/30 text-xs text-rose-300">
                {error}
              </div>
            )}

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
        <div className="flex-1 flex flex-col items-center justify-center p-8 text-center text-obsidian-400">
          <MessageSquare className="w-12 h-12 text-obsidian-700 mb-3" />
          <h3 className="text-sm font-semibold text-white">No conversation selected</h3>
          <p className="text-xs text-obsidian-500 mt-1">
            Select a customer chat on the left to begin.
          </p>
        </div>
      )}
    </div>
  );
}
