/**
 * Customer Directory Service.
 *
 * Direct client mapping to backend router:
 * backend/app/modules/customers/router.py
 *
 * Endpoints:
 * - GET  /api/v1/customers      -> listCustomers(...)
 * - POST /api/v1/customers      -> createCustomer(...)
 * - GET  /api/v1/customers/{id} -> getCustomer(id)
 */

import { apiClient } from "./api.client";
import { CustomerListResponse, CustomerRead } from "@/types";

export interface ListCustomersParams {
  search?: string;
  page?: number;
  page_size?: number;
}

export const customersService = {
  /**
   * Retrieves paginated customer profiles.
   * Calls: GET /api/v1/customers (backend/app/modules/customers/router.py:49)
   */
  async listCustomers(params?: ListCustomersParams): Promise<CustomerListResponse> {
    const query = new URLSearchParams();
    if (params?.search) query.set("search", params.search);
    if (params?.page) query.set("page", String(params.page));
    if (params?.page_size) query.set("page_size", String(params.page_size));

    const qs = query.toString();
    return apiClient<CustomerListResponse>(`/customers${qs ? `?${qs}` : ""}`);
  },

  /**
   * Retrieves single customer by UUID.
   * Calls: GET /api/v1/customers/{id} (backend/app/modules/customers/router.py:82)
   */
  async getCustomer(id: string): Promise<CustomerRead> {
    return apiClient<CustomerRead>(`/customers/${id}`);
  },
};

