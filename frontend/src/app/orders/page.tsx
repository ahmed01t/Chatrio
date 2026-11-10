"use client";

/**
 * Orders & Fulfillment Board.
 *
 * Implements design-taste-frontend standards:
 * - Quiet panels, aligned figures, colour spent on data
 * - Warm white canvas (#FAF8F5) with terracotta (#EA580C) data highlights
 * - Real-time slide-over order inspector with itemized breakdown and state machine transitions
 * - Direct client mapping to backend router:
 *   - GET   /api/v1/orders               (ordersService.listOrders)
 *   - PATCH /api/v1/orders/{id}/status   (ordersService.updateStatus)
 *   - POST  /api/v1/orders/{id}/cancel   (ordersService.cancelOrder)
 */

import React, { useEffect, useState, useCallback } from "react";
import {
  ShoppingCart,
  Search,
  MapPin,
  Clock,
  X,
  CreditCard,
  RefreshCw,
  Package,
  AlertCircle,
  CheckCircle,
  Truck,
  Ban,
} from "lucide-react";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { OrderRead, OrderItemRead, OrderStatus } from "@/types";
import { ordersService } from "@/services/orders.service";

export default function OrdersPage() {
  const [orders, setOrders] = useState<OrderRead[]>([]);
  const [selectedOrder, setSelectedOrder] = useState<OrderRead | null>(null);
  const [statusFilter, setStatusFilter] = useState<string>("ALL");
  const [searchQuery, setSearchQuery] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [isUpdatingStatus, setIsUpdatingStatus] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const fetchOrders = useCallback(async () => {
    setIsLoading(true);
    setErrorMessage(null);
    try {
      const filter = statusFilter !== "ALL" ? (statusFilter as OrderStatus) : undefined;
      const response = await ordersService.listOrders({ status: filter, page_size: 50 });
      setOrders(response.items || []);
    } catch (err: unknown) {
      console.error("Failed to load orders from PostgreSQL backend:", err);
      setErrorMessage("Could not connect to PostgreSQL backend. Ensure API server is running on :8000.");
    } finally {
      setIsLoading(false);
    }
  }, [statusFilter]);

  useEffect(() => {
    fetchOrders();
  }, [fetchOrders]);

  const handleUpdateStatus = async (newStatus: OrderStatus) => {
    if (!selectedOrder) return;
    setIsUpdatingStatus(true);
    try {
      let updated: OrderRead;
      if (newStatus === "CANCELLED") {
        updated = await ordersService.cancelOrder(selectedOrder.id);
      } else {
        updated = await ordersService.updateStatus(selectedOrder.id, newStatus);
      }
      setSelectedOrder(updated);
      setOrders((prev) => prev.map((o) => (o.id === updated.id ? updated : o)));
    } catch (err: unknown) {
      console.error("Failed to update status:", err);
      alert("Status transition failed. Check backend invariant rules.");
    } finally {
      setIsUpdatingStatus(false);
    }
  };

  const filteredOrders = orders.filter((o) =>
    o.order_number.toLowerCase().includes(searchQuery.toLowerCase()) ||
    (o.customer_id || "").toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="space-y-6 animate-in fade-in duration-150">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-border">
        <div>
          <div className="text-xs font-semibold uppercase tracking-wider text-accent mb-1 font-mono">
            Commerce Operations
          </div>
          <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-ink-900 flex items-center gap-2.5">
            Fulfillment &amp; Orders Board
          </h1>
          <p className="text-xs sm:text-sm text-ink-500 mt-1">
            Deterministic state machine orders assembled conversationally by LangGraph and persisted in PostgreSQL.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Button
            variant="secondary"
            size="sm"
            onClick={fetchOrders}
            isLoading={isLoading}
            className="flex items-center gap-1.5"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? "animate-spin" : ""}`} />
            <span>Sync Orders</span>
          </Button>
        </div>
      </div>

      {/* Error Alert */}
      {errorMessage && (
        <div className="p-3.5 rounded-xl bg-rose-50 border border-rose-200 text-xs text-rose-700 flex items-center gap-2">
          <AlertCircle className="w-4 h-4 shrink-0 text-rose-500" />
          <span>{errorMessage}</span>
        </div>
      )}

      {/* Filter Tabs & Search */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div className="flex flex-wrap gap-1.5 bg-canvas-subtle p-1 rounded-xl border border-border">
          {["ALL", "PENDING", "CONFIRMED", "PROCESSING", "SHIPPED", "DELIVERED", "CANCELLED"].map((status) => (
            <button
              key={status}
              onClick={() => setStatusFilter(status)}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-colors ${
                statusFilter === status
                  ? "bg-white text-ink-900 border border-border shadow-sm"
                  : "text-ink-500 hover:text-ink-900"
              }`}
            >
              {status}
            </button>
          ))}
        </div>

        <div className="relative w-full sm:w-64">
          <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-ink-400" />
          <input
            type="text"
            placeholder="Search order #..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full bg-white border border-border rounded-xl pl-9 pr-3 py-1.5 text-xs text-ink-900 placeholder:text-ink-400 focus:outline-none focus:border-accent focus:ring-1 focus:ring-accent transition-all shadow-sm"
          />
        </div>
      </div>

      {/* Orders Table */}
      <div className="quiet-panel overflow-hidden card-taste">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-canvas-subtle border-b border-border text-ink-500 font-mono">
              <tr>
                <th className="py-3.5 px-4 font-semibold">Order #</th>
                <th className="py-3.5 px-4 font-semibold">Created At</th>
                <th className="py-3.5 px-4 font-semibold">Total Amount</th>
                <th className="py-3.5 px-4 font-semibold">Payment Status</th>
                <th className="py-3.5 px-4 font-semibold">Fulfillment Status</th>
                <th className="py-3.5 px-4 text-right font-semibold">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border/60">
              {isLoading && orders.length === 0 ? (
                <tr>
                  <td colSpan={6} className="py-12 text-center text-ink-500">
                    <div className="inline-flex items-center gap-2 font-mono">
                      <RefreshCw className="w-4 h-4 animate-spin text-accent" />
                      <span>Querying PostgreSQL orders...</span>
                    </div>
                  </td>
                </tr>
              ) : filteredOrders.length === 0 ? (
                <tr>
                  <td colSpan={6} className="py-12 text-center">
                    <div className="max-w-sm mx-auto space-y-2">
                      <Package className="w-8 h-8 text-ink-300 mx-auto" />
                      <p className="text-xs font-semibold text-ink-900">No matching orders found</p>
                      <p className="text-[11px] text-ink-500">
                        {statusFilter !== "ALL"
                          ? `No orders currently matching status "${statusFilter}".`
                          : "Orders placed by WhatsApp customers via AI conversation will populate here automatically."}
                      </p>
                    </div>
                  </td>
                </tr>
              ) : (
                filteredOrders.map((order) => (
                  <tr
                    key={order.id}
                    className="hover:bg-canvas-subtle transition-colors cursor-pointer"
                    onClick={() => setSelectedOrder(order)}
                  >
                    <td className="py-3.5 px-4 font-mono font-bold text-ink-900">
                      {order.order_number}
                    </td>
                    <td className="py-3.5 px-4 font-mono text-ink-500">
                      {new Date(order.created_at).toLocaleString([], {
                        month: "short",
                        day: "numeric",
                        hour: "2-digit",
                        minute: "2-digit",
                      })}
                    </td>
                    <td className="py-3.5 px-4 font-mono font-bold text-ink-900">
                      {order.currency || "USD"} ${Number(order.total_amount).toFixed(2)}
                    </td>
                    <td className="py-3.5 px-4">
                      <Badge
                        variant={order.payment_status === "PAID" ? "success" : "neutral"}
                        size="sm"
                      >
                        {order.payment_status}
                      </Badge>
                    </td>
                    <td className="py-3.5 px-4">
                      <Badge
                        variant={
                          order.status === "CONFIRMED"
                            ? "success"
                            : order.status === "PENDING"
                            ? "warning"
                            : order.status === "SHIPPED"
                            ? "active"
                            : order.status === "DELIVERED"
                            ? "success"
                            : "critical"
                        }
                        size="sm"
                      >
                        {order.status}
                      </Badge>
                    </td>
                    <td className="py-3.5 px-4 text-right">
                      <Button variant="ghost" size="sm">
                        View Details
                      </Button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Slide-over Order Detail Drawer */}
      {selectedOrder && (
        <div className="fixed inset-0 z-50 flex justify-end">
          <div
            className="fixed inset-0 bg-ink-900/40 backdrop-blur-sm"
            onClick={() => setSelectedOrder(null)}
          />
          <div className="relative w-full max-w-md bg-white border-l border-border shadow-2xl h-full flex flex-col z-10 p-6 overflow-y-auto">
            {/* Drawer Header */}
            <div className="flex items-center justify-between pb-4 border-b border-border">
              <div>
                <h3 className="text-base font-bold text-ink-900 font-mono flex items-center gap-2">
                  <Package className="w-4 h-4 text-accent" />
                  <span>{selectedOrder.order_number}</span>
                </h3>
                <p className="text-xs text-ink-500 font-mono mt-0.5 flex items-center gap-1">
                  <Clock className="w-3 h-3" />
                  <span>Placed {new Date(selectedOrder.created_at).toLocaleString()}</span>
                </p>
              </div>
              <button
                onClick={() => setSelectedOrder(null)}
                className="p-1 rounded-lg text-ink-400 hover:text-ink-900"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Status & Payment Badges */}
            <div className="flex items-center gap-2 my-5">
              <Badge
                variant={
                  selectedOrder.status === "CONFIRMED" || selectedOrder.status === "DELIVERED"
                    ? "success"
                    : selectedOrder.status === "PENDING"
                    ? "warning"
                    : selectedOrder.status === "SHIPPED"
                    ? "active"
                    : "critical"
                }
                size="md"
              >
                Status: {selectedOrder.status}
              </Badge>
              <Badge
                variant={selectedOrder.payment_status === "PAID" ? "success" : "neutral"}
                size="md"
              >
                Payment: {selectedOrder.payment_status}
              </Badge>
            </div>

            {/* Customer & Delivery Address */}
            <div className="space-y-4 mb-6 p-4 rounded-xl bg-canvas-subtle border border-border">
              <div className="flex items-start gap-2.5 text-xs text-ink-700">
                <MapPin className="w-4 h-4 text-accent shrink-0 mt-0.5" />
                <div>
                  <span className="font-semibold text-ink-900 block">Delivery Address:</span>
                  <p className="text-ink-500 mt-0.5">
                    {selectedOrder.shipping_address || "Address pending WhatsApp collection"}
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-2.5 text-xs text-ink-700">
                <CreditCard className="w-4 h-4 text-ink-500 shrink-0" />
                <div>
                  <span className="font-semibold text-ink-900">Customer ID: </span>
                  <span className="font-mono text-ink-500">{selectedOrder.customer_id}</span>
                </div>
              </div>
            </div>

            {/* Line Items List */}
            <div className="space-y-3 flex-1 mb-6">
              <h4 className="text-xs font-bold uppercase tracking-wider text-ink-500 font-mono">
                Order Items ({selectedOrder.items?.length || 0})
              </h4>
              <div className="divide-y divide-border border border-border rounded-xl overflow-hidden bg-white">
                {!selectedOrder.items || selectedOrder.items.length === 0 ? (
                  <div className="p-4 text-center text-xs text-ink-400 font-mono">
                    No line items attached
                  </div>
                ) : (
                  selectedOrder.items.map((item: OrderItemRead) => (
                    <div key={item.id} className="p-3 flex items-center justify-between text-xs">
                      <div>
                        <p className="font-semibold text-ink-900">{item.product_name}</p>
                        <p className="text-ink-500 font-mono text-[11px]">
                          SKU: {item.sku} &bull; Qty: {item.quantity} &times; ${Number(item.unit_price).toFixed(2)}
                        </p>
                      </div>
                      <span className="font-mono font-bold text-ink-900">
                        ${Number(item.subtotal).toFixed(2)}
                      </span>
                    </div>
                  ))
                )}
              </div>
            </div>

            {/* Financial Summary */}
            <div className="space-y-2 py-4 border-t border-border text-xs">
              <div className="flex justify-between text-ink-500">
                <span>Subtotal</span>
                <span className="font-mono">${Number(selectedOrder.subtotal).toFixed(2)}</span>
              </div>
              <div className="flex justify-between text-ink-500">
                <span>Shipping Cost</span>
                <span className="font-mono">${Number(selectedOrder.shipping_cost).toFixed(2)}</span>
              </div>
              <div className="flex justify-between text-sm font-bold text-ink-900 pt-2 border-t border-border">
                <span>Total Amount</span>
                <span className="font-mono text-accent">
                  ${Number(selectedOrder.total_amount).toFixed(2)}
                </span>
              </div>
            </div>

            {/* Status Transition Action Buttons */}
            <div className="space-y-2 pt-2">
              {selectedOrder.status === "PENDING" && (
                <Button
                  className="w-full flex items-center justify-center gap-2"
                  size="md"
                  onClick={() => handleUpdateStatus("CONFIRMED")}
                  isLoading={isUpdatingStatus}
                >
                  <CheckCircle className="w-4 h-4" />
                  <span>Confirm Order</span>
                </Button>
              )}
              {selectedOrder.status === "CONFIRMED" && (
                <Button
                  className="w-full flex items-center justify-center gap-2"
                  size="md"
                  onClick={() => handleUpdateStatus("SHIPPED")}
                  isLoading={isUpdatingStatus}
                >
                  <Truck className="w-4 h-4" />
                  <span>Dispatch &amp; Mark as Shipped</span>
                </Button>
              )}
              {selectedOrder.status === "SHIPPED" && (
                <Button
                  className="w-full flex items-center justify-center gap-2"
                  size="md"
                  onClick={() => handleUpdateStatus("DELIVERED")}
                  isLoading={isUpdatingStatus}
                >
                  <CheckCircle className="w-4 h-4" />
                  <span>Mark as Delivered</span>
                </Button>
              )}
              {selectedOrder.status !== "CANCELLED" && selectedOrder.status !== "DELIVERED" && (
                <Button
                  variant="danger"
                  className="w-full flex items-center justify-center gap-2"
                  size="sm"
                  onClick={() => handleUpdateStatus("CANCELLED")}
                  isLoading={isUpdatingStatus}
                >
                  <Ban className="w-3.5 h-3.5" />
                  <span>Cancel Order &amp; Restore Stock</span>
                </Button>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
