/**
 * Conversations & WhatsApp Shared Inbox Service.
 *
 * Direct client mapping to backend router:
 * backend/app/modules/conversations/router.py
 *
 * Endpoints:
 * - GET   /api/v1/conversations            -> listConversations(...)
 * - GET   /api/v1/conversations/{id}       -> getConversation(id)
 * - PATCH /api/v1/conversations/{id}/takeover -> toggleTakeover(id, isAiActive)
 * - PATCH /api/v1/conversations/{id}/status   -> updateStatus(id, status)
 * - GET   /api/v1/conversations/{id}/messages -> listMessages(id)
 * - POST  /api/v1/conversations/{id}/messages -> sendMessage(id, text)
 */

import { apiClient } from "./api.client";
import {
  ConversationListResponse,
  ConversationRead,
  ConversationStatus,
  MessageListResponse,
  MessageRead,
} from "@/types";

export interface ListConversationsParams {
  status?: ConversationStatus;
  page?: number;
  page_size?: number;
}

export const conversationsService = {
  /**
   * Lists customer conversation sessions for merchant inbox.
   * Calls: GET /api/v1/conversations (backend/app/modules/conversations/router.py:58)
   */
  async listConversations(params?: ListConversationsParams): Promise<ConversationListResponse> {
    const query = new URLSearchParams();
    if (params?.status) query.set("status", params.status);
    if (params?.page) query.set("page", String(params.page));
    if (params?.page_size) query.set("page_size", String(params.page_size));

    const qs = query.toString();
    return apiClient<ConversationListResponse>(`/conversations${qs ? `?${qs}` : ""}`);
  },

  /**
   * Retrieves single conversation details with customer profile.
   * Calls: GET /api/v1/conversations/{id} (backend/app/modules/conversations/router.py:91)
   */
  async getConversation(id: string): Promise<ConversationRead> {
    return apiClient<ConversationRead>(`/conversations/${id}`);
  },

  /**
   * Toggles human agent takeover (pauses or resumes LangGraph AI copilot).
   * Calls: PATCH /api/v1/conversations/{id}/takeover (backend/app/modules/conversations/router.py:113)
   */
  async toggleTakeover(id: string, isAiActive: boolean): Promise<ConversationRead> {
    return apiClient<ConversationRead>(`/conversations/${id}/takeover`, {
      method: "PATCH",
      body: JSON.stringify({ is_ai_active: isAiActive }),
    });
  },

  /**
   * Updates conversation lifecycle state (ACTIVE, CLOSED, ARCHIVED).
   * Calls: PATCH /api/v1/conversations/{id}/status (backend/app/modules/conversations/router.py:138)
   */
  async updateStatus(id: string, status: ConversationStatus): Promise<ConversationRead> {
    return apiClient<ConversationRead>(`/conversations/${id}/status`, {
      method: "PATCH",
      body: JSON.stringify({ status }),
    });
  },

  /**
   * Retrieves chronological message history for a conversation.
   * Calls: GET /api/v1/conversations/{id}/messages (backend/app/modules/conversations/router.py:166)
   */
  async listMessages(conversationId: string, page = 1, pageSize = 50): Promise<MessageListResponse> {
    return apiClient<MessageListResponse>(
      `/conversations/${conversationId}/messages?page=${page}&page_size=${pageSize}`
    );
  },

  /**
   * Posts an outbound reply from a human staff agent into WhatsApp.
   * Automatically enqueues into Transactional Outbox engine.
   * Calls: POST /api/v1/conversations/{id}/messages (backend/app/modules/conversations/router.py:195)
   */
  async sendMessage(conversationId: string, text: string): Promise<MessageRead> {
    return apiClient<MessageRead>(`/conversations/${conversationId}/messages`, {
      method: "POST",
      body: JSON.stringify({
        sender_type: "HUMAN_AGENT",
        direction: "OUTBOUND",
        content_type: "TEXT",
        text_body: text,
      }),
    });
  },
};

