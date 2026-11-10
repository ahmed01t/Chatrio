/**
 * Products & Inventory Service.
 *
 * Direct client mapping to backend router:
 * backend/app/modules/products/router.py
 *
 * Endpoints:
 * - GET    /api/v1/categories            -> listCategories()
 * - POST   /api/v1/categories            -> createCategory(...)
 * - GET    /api/v1/products              -> listProducts(...)
 * - POST   /api/v1/products              -> createProduct(...)
 * - GET    /api/v1/products/{id}         -> getProduct(id)
 * - PATCH  /api/v1/products/{id}         -> updateProduct(id, ...)
 * - DELETE /api/v1/products/{id}         -> deleteProduct(id)
 * - POST   /api/v1/products/{id}/inventory -> adjustInventory(id, ...)
 */

import { apiClient } from "./api.client";
import {
  CategoryRead,
  ProductCreate,
  ProductListResponse,
  ProductRead,
  ProductUpdate,
} from "@/types";

export interface ListProductsParams {
  search?: string;
  category_id?: string;
  is_active?: boolean;
  page?: number;
  page_size?: number;
}

export const productsService = {
  /**
   * Retrieves paginated list of catalog products.
   * Calls: GET /api/v1/products (backend/app/modules/products/router.py:126)
   */
  async listProducts(params?: ListProductsParams): Promise<ProductListResponse> {
    const query = new URLSearchParams();
    if (params?.search) query.set("search", params.search);
    if (params?.category_id) query.set("category_id", params.category_id);
    if (params?.is_active !== undefined) query.set("is_active", String(params.is_active));
    if (params?.page) query.set("page", String(params.page));
    if (params?.page_size) query.set("page_size", String(params.page_size));

    const qs = query.toString();
    return apiClient<ProductListResponse>(`/products${qs ? `?${qs}` : ""}`);
  },

  /**
   * Creates a new product in PostgreSQL inventory.
   * Calls: POST /api/v1/products (backend/app/modules/products/router.py:100)
   */
  async createProduct(payload: ProductCreate): Promise<ProductRead> {
    return apiClient<ProductRead>("/products", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  /**
   * Retrieves single product by UUID.
   * Calls: GET /api/v1/products/{id} (backend/app/modules/products/router.py:157)
   */
  async getProduct(id: string): Promise<ProductRead> {
    return apiClient<ProductRead>(`/products/${id}`);
  },

  /**
   * Updates product metadata, price, or active status.
   * Calls: PATCH /api/v1/products/{id} (backend/app/modules/products/router.py:177)
   */
  async updateProduct(id: string, payload: ProductUpdate): Promise<ProductRead> {
    return apiClient<ProductRead>(`/products/${id}`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    });
  },

  /**
   * Permanently deletes product from catalog.
   * Calls: DELETE /api/v1/products/{id} (backend/app/modules/products/router.py:207)
   */
  async deleteProduct(id: string): Promise<void> {
    return apiClient<void>(`/products/${id}`, {
      method: "DELETE",
    });
  },

  /**
   * Adjusts stock inventory with audit reason.
   * Calls: POST /api/v1/products/{id}/inventory (backend/app/modules/products/router.py:257)
   */
  async adjustInventory(
    id: string,
    quantityDelta: number,
    reason: "RESTOCK" | "MANUAL_ADJUSTMENT" | "CORRECTION" = "RESTOCK"
  ): Promise<ProductRead> {
    return apiClient<ProductRead>(`/products/${id}/inventory`, {
      method: "POST",
      body: JSON.stringify({
        quantity_delta: quantityDelta,
        reason,
      }),
    });
  },

  /**
   * Lists all product categories for this merchant.
   * Calls: GET /api/v1/categories (backend/app/modules/products/router.py:73)
   */
  async listCategories(): Promise<CategoryRead[]> {
    return apiClient<CategoryRead[]>("/categories");
  },
};

