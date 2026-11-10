/**
 * Orders & Commerce Fulfillment Service.
 *
 * Direct client mapping to backend router:
 * backend/app/modules/orders/router.py
 *
 * Endpoints:
 * - GET   /api/v1/orders          -> listOrders(...)
 * - POST  /api/v1/orders          -> createOrder(...)
 * - GET   /api/v1/orders/{id}     -> getOrder(id)
 * - PATCH /api/v1/orders/{id}/status -> updateStatus(id, status)
 * - POST  /api/v1/orders/{id}/cancel -> cancelOrder(id)
 */

import { apiClient } from "./api.client";
import {
  OrderListResponse,
  OrderRead,
  OrderStatus,
  PaymentStatus,
} from "@/types";

export interface ListOrdersParams {
  status?: OrderStatus;
  payment_status?: PaymentStatus;
  customer_id?: string;
  page?: number;
  page_size?: number;
}

export const ordersService = {
  /**
   * Retrieves paginated list of tenant orders.
   * Calls: GET /api/v1/orders (backend/app/modules/orders/router.py:58)
   */
  async listOrders(params?: ListOrdersParams): Promise<OrderListResponse> {
    const query = new URLSearchParams();
    if (params?.status) query.set("status", params.status);
    if (params?.payment_status) query.set("payment_status", params.payment_status);
    if (params?.customer_id) query.set("customer_id", params.customer_id);
    if (params?.page) query.set("page", String(params.page));
    if (params?.page_size) query.set("page_size", String(params.page_size));

    const qs = query.toString();
    return apiClient<OrderListResponse>(`/orders${qs ? `?${qs}` : ""}`);
  },

  /**
   * Retrieves single order by UUID including line items and customer snapshot.
   * Calls: GET /api/v1/orders/{id} (backend/app/modules/orders/router.py:90)
   */
  async getOrder(id: string): Promise<OrderRead> {
    return apiClient<OrderRead>(`/orders/${id}`);
  },

  /**
   * Advances order state machine status (CONFIRMED, SHIPPED, DELIVERED).
   * Calls: PATCH /api/v1/orders/{id}/status (backend/app/modules/orders/router.py:144)
   */
  async updateStatus(id: string, newStatus: OrderStatus): Promise<OrderRead> {
    return apiClient<OrderRead>(`/orders/${id}/status`, {
      method: "PATCH",
      body: JSON.stringify({ status: newStatus }),
    });
  },

  /**
   * Cancels order and releases reserved inventory back to catalog.
   * Calls: POST /api/v1/orders/{id}/cancel (backend/app/modules/orders/router.py:168)
   */
  async cancelOrder(id: string): Promise<OrderRead> {
    return apiClient<OrderRead>(`/orders/${id}/cancel`, {
      method: "POST",
    });
  },
};

