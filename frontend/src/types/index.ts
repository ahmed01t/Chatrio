/**
 * Chatrio Frontend TypeScript Definitions.
 *
 * 100% Type-safe mirrors of backend Pydantic v2 schemas across all domain modules:
 * - Auth & Tenancy: backend/app/modules/auth/schemas.py
 * - Products & Categories: backend/app/modules/products/schemas.py
 * - Orders & Order Items: backend/app/modules/orders/schemas.py
 * - Conversations & Messages: backend/app/modules/conversations/schemas.py
 * - Customers: backend/app/modules/customers/schemas.py
 */

// =============================================================================
// 1. Auth & Tenancy (backend/app/modules/auth/schemas.py)
// =============================================================================
export interface UserRead {
  id: string;
  email: string;
  full_name: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface OrganizationRead {
  id: string;
  name: string;
  slug: string;
  created_at?: string;
  updated_at?: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  user: UserRead;
  organization: OrganizationRead;
}

export interface UserProfileResponse {
  user: UserRead;
  organization: OrganizationRead;
  role: "OWNER" | "ADMIN" | "AGENT" | "VIEWER";
}

// =============================================================================
// 2. Products & Categories (backend/app/modules/products/schemas.py)
// =============================================================================
export interface CategoryRead {
  id: string;
  organization_id: string;
  name: string;
  slug: string;
  description?: string | null;
  created_at: string;
  updated_at: string;
}

export interface ProductRead {
  id: string;
  organization_id: string;
  category_id?: string | null;
  name: string;
  slug: string;
  sku: string;
  description?: string | null;
  price: string | number;
  stock_quantity: number;
  is_active: boolean;
  image_url?: string | null;
  created_at: string;
  updated_at: string;
  category?: CategoryRead | null;
}

export interface ProductListResponse {
  items: ProductRead[];
  total: number;
  page: number;
  page_size: number;
}

export interface ProductCreate {
  name: string;
  sku: string;
  price: number;
  stock_quantity: number;
  description?: string;
  category_id?: string | null;
  image_url?: string | null;
}

export interface ProductUpdate {
  name?: string;
  price?: number;
  stock_quantity?: number;
  description?: string;
  category_id?: string | null;
  is_active?: boolean;
}

// =============================================================================
// 3. Customers (backend/app/modules/customers/schemas.py)
// =============================================================================
export interface CustomerRead {
  id: string;
  organization_id: string;
  phone_number: string;
  name?: string | null;
  is_blocked: boolean;
  created_at: string;
  updated_at?: string;
}

export interface CustomerListResponse {
  items: CustomerRead[];
  total: number;
  page: number;
  page_size: number;
}

// =============================================================================
// 4. Conversations & Messages (backend/app/modules/conversations/schemas.py)
// =============================================================================
export type ConversationStatus = "ACTIVE" | "CLOSED" | "ARCHIVED";
export type MessageSenderType = "CUSTOMER" | "AI_AGENT" | "HUMAN_AGENT" | "SYSTEM";
export type MessageDirection = "INBOUND" | "OUTBOUND";
export type MessageContentType = "TEXT" | "IMAGE" | "DOCUMENT" | "LOCATION" | "INTERACTIVE" | "TEMPLATE";
export type MessageStatus = "RECEIVED" | "PROCESSING" | "SENT" | "DELIVERED" | "READ" | "FAILED";

export interface ConversationRead {
  id: string;
  organization_id: string;
  customer_id: string;
  status: ConversationStatus;
  channel: "WHATSAPP" | "WEB" | "API";
  is_ai_active: boolean;
  last_message_at?: string | null;
  created_at: string;
  updated_at?: string;
  customer?: CustomerRead | null;
}

export interface ConversationListResponse {
  items: ConversationRead[];
  total: number;
  page: number;
  page_size: number;
}

export interface MessageRead {
  id: string;
  organization_id: string;
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

export interface MessageListResponse {
  items: MessageRead[];
  total: number;
  page: number;
  page_size: number;
}

export interface MessageCreate {
  sender_type?: MessageSenderType;
  direction?: MessageDirection;
  content_type?: MessageContentType;
  text_body?: string;
  media_url?: string;
}

// =============================================================================
// 5. Orders & Fulfillment (backend/app/modules/orders/schemas.py)
// =============================================================================
export type OrderStatus = "PENDING" | "CONFIRMED" | "PROCESSING" | "SHIPPED" | "DELIVERED" | "CANCELLED";
export type PaymentStatus = "UNPAID" | "PAID" | "REFUNDED" | "FAILED";

export interface OrderItemRead {
  id: string;
  product_id: string;
  product_name: string;
  sku: string;
  unit_price: string | number;
  quantity: number;
  subtotal: string | number;
}

export interface OrderRead {
  id: string;
  organization_id: string;
  customer_id: string;
  conversation_id?: string | null;
  order_number: string;
  status: OrderStatus;
  payment_status: PaymentStatus;
  currency: string;
  subtotal: string | number;
  shipping_cost: string | number;
  total_amount: string | number;
  shipping_address?: string | null;
  notes?: string | null;
  created_at: string;
  updated_at: string;
  items: OrderItemRead[];
}

export interface OrderListResponse {
  items: OrderRead[];
  total: number;
  page: number;
  page_size: number;
}
