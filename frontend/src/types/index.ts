/**
 * Central TypeScript types matching Chatrio backend Pydantic schemas.
 */

// -----------------------------------------------------------------------------
// Auth & Organizations
// -----------------------------------------------------------------------------
export interface User {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  is_active: boolean;
}

export interface Organization {
  id: string;
  name: string;
  slug: string;
  currency: string;
  created_at: string;
}

export interface AuthTokens {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

export interface LoginResponse {
  tokens: AuthTokens;
  user: User;
  organization: Organization;
}

// -----------------------------------------------------------------------------
// Products & Inventory
// -----------------------------------------------------------------------------
export interface Category {
  id: string;
  name: string;
  slug: string;
  description?: string | null;
}

export interface Product {
  id: string;
  organization_id: string;
  category_id?: string | null;
  name: string;
  sku: string;
  description?: string | null;
  price: number;
  stock_quantity: number;
  is_active: boolean;
  image_url?: string | null;
  created_at: string;
  updated_at: string;
  category?: Category | null;
}

export interface ProductCreateInput {
  name: string;
  sku: string;
  description?: string;
  price: number;
  stock_quantity: number;
  category_id?: string | null;
  image_url?: string | null;
}

// -----------------------------------------------------------------------------
// Orders & Commerce
// -----------------------------------------------------------------------------
export type OrderStatus = "PENDING" | "CONFIRMED" | "PROCESSING" | "SHIPPED" | "DELIVERED" | "CANCELLED";
export type PaymentStatus = "UNPAID" | "PAID" | "REFUNDED" | "FAILED";

export interface OrderItem {
  id: string;
  product_id: string;
  product_name: string;
  sku: string;
  unit_price: number;
  quantity: number;
  subtotal: number;
}

export interface Order {
  id: string;
  organization_id: string;
  customer_id: string;
  conversation_id?: string | null;
  order_number: string;
  status: OrderStatus;
  payment_status: PaymentStatus;
  currency: string;
  subtotal: number;
  shipping_cost: number;
  total_amount: number;
  shipping_address?: string | null;
  notes?: string | null;
  created_at: string;
  updated_at: string;
  items: OrderItem[];
  customer_phone?: string;
  customer_name?: string;
}

// -----------------------------------------------------------------------------
// Conversations & Shared Inbox
// -----------------------------------------------------------------------------
export type MessageSenderType = "CUSTOMER" | "AI_AGENT" | "HUMAN_AGENT" | "SYSTEM";
export type MessageDirection = "INBOUND" | "OUTBOUND";
export type MessageContentType = "TEXT" | "IMAGE" | "DOCUMENT" | "LOCATION" | "INTERACTIVE" | "TEMPLATE";
export type MessageStatus = "RECEIVED" | "PROCESSING" | "SENT" | "DELIVERED" | "READ" | "FAILED";

export interface Message {
  id: string;
  conversation_id: string;
  sender_type: MessageSenderType;
  direction: MessageDirection;
  content_type: MessageContentType;
  text_body?: string | null;
  media_url?: string | null;
  status: MessageStatus;
  whatsapp_message_id?: string | null;
  created_at: string;
}

export interface Conversation {
  id: string;
  organization_id: string;
  customer_id: string;
  status: "ACTIVE" | "CLOSED" | "ARCHIVED";
  channel: "WHATSAPP" | "WEB" | "API";
  is_ai_active: boolean;
  last_message_at?: string | null;
  created_at: string;
  customer_phone?: string;
  customer_name?: string;
  last_message_snippet?: string;
  unread_count?: number;
}

// -----------------------------------------------------------------------------
// Dashboard Analytics & KPI
// -----------------------------------------------------------------------------
export interface DashboardKPI {
  total_revenue: number;
  revenue_trend: string;
  active_conversations: number;
  conversations_trend: string;
  pending_orders: number;
  pending_trend: string;
  ai_resolution_rate: number;
  ai_trend: string;
}

