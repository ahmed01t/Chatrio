"use client";

/**
 * Orders & Fulfillment Board.
 *
 * Direct client mapping to backend router:
 * backend/app/modules/orders/router.py
 *
 * Endpoints consumed:
 * - GET   /api/v1/orders               (ordersService.listOrders)
 * - PATCH /api/v1/orders/{id}/status   (ordersService.updateStatus)
 * - POST  /api/v1/orders/{id}/cancel   (ordersService.cancelOrder)
 *
 * Features:
 * - Strict multi-tenant scoped order listing with status filtering
 * - Zero hardcoded or mock fallbacks; purely backed by PostgreSQL
 * - Real-time slide-over order inspector with itemized breakdown and state machine transitions
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
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-obsidian-800">
        <div>
          <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-white flex items-center gap-2">
            <ShoppingCart className="w-6 h-6 text-brand-emerald" />
            <span>Orders & Fulfillment Board</span>
          </h1>
          <p className="text-xs sm:text-sm text-obsidian-400 mt-1">
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
        <div className="p-3.5 rounded-xl bg-status-critical/10 border border-status-critical/20 text-xs text-status-critical flex items-center gap-2">
          <AlertCircle className="w-4 h-4 shrink-0" />
          <span>{errorMessage}</span>
        </div>
      )}

      {/* Filter Tabs & Search */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div className="flex flex-wrap gap-1.5 bg-obsidian-900 p-1 rounded-xl border border-obsidian-750/70">
          {["ALL", "PENDING", "CONFIRMED", "PROCESSING", "SHIPPED", "DELIVERED", "CANCELLED"].map((status) => (
            <button
              key={status}
              onClick={() => setStatusFilter(status)}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
                statusFilter === status
                  ? "bg-obsidian-800 text-white border border-obsidian-650 font-semibold"
                  : "text-obsidian-400 hover:text-white"
              }`}
            >
              {status}
            </button>
          ))}
        </div>

        <div className="relative w-full sm:w-64">
          <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-obsidian-400" />
          <input
            type="text"
            placeholder="Search order #..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full bg-obsidian-850 border border-obsidian-700/80 rounded-lg pl-9 pr-3 py-1.5 text-xs text-obsidian-100 placeholder:text-obsidian-500 focus:outline-none focus:border-brand-emerald"
          />
        </div>
      </div>

      {/* Orders Table */}
      <div className="bg-obsidian-850/80 border border-obsidian-750/90 rounded-xl shadow-card overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-obsidian-900 border-b border-obsidian-750/70 text-obsidian-400 font-mono">
              <tr>
                <th className="py-3 px-4 font-semibold">Order #</th>
                <th className="py-3 px-4 font-semibold">Created At</th>
                <th className="py-3 px-4 font-semibold">Total Amount</th>
                <th className="py-3 px-4 font-semibold">Payment Status</th>
                <th className="py-3 px-4 font-semibold">Fulfillment Status</th>
                <th className="py-3 px-4 text-right font-semibold">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-obsidian-750/50">
              {isLoading && orders.length === 0 ? (
                <tr>
                  <td colSpan={6} className="py-12 text-center text-obsidian-400">
                    <div className="inline-flex items-center gap-2">
                      <RefreshCw className="w-4 h-4 animate-spin text-brand-emerald" />
                      <span>Querying PostgreSQL orders...</span>
                    </div>
                  </td>
                </tr>
              ) : filteredOrders.length === 0 ? (
                <tr>
                  <td colSpan={6} className="py-12 text-center">
                    <div className="max-w-sm mx-auto space-y-2">
                      <Package className="w-8 h-8 text-obsidian-600 mx-auto" />
                      <p className="text-xs font-medium text-obsidian-300">No matching orders found</p>
                      <p className="text-[11px] text-obsidian-500">
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
                    className="hover:bg-obsidian-800/60 transition-colors cursor-pointer"
                    onClick={() => setSelectedOrder(order)}
                  >
                    <td className="py-3.5 px-4 font-mono font-bold text-white">
                      {order.order_number}
                    </td>
                    <td className="py-3.5 px-4 font-mono text-obsidian-300">
                      {new Date(order.created_at).toLocaleString([], {
                        month: "short",
                        day: "numeric",
                        hour: "2-digit",
                        minute: "2-digit",
                      })}
                    </td>
                    <td className="py-3.5 px-4 font-mono font-bold text-white">
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
            className="fixed inset-0 bg-obsidian-950/80 backdrop-blur-sm"
            onClick={() => setSelectedOrder(null)}
          />
          <div className="relative w-full max-w-md bg-obsidian-900 border-l border-obsidian-750 shadow-2xl h-full flex flex-col z-10 p-6 overflow-y-auto">
            {/* Drawer Header */}
            <div className="flex items-center justify-between pb-4 border-b border-obsidian-750">
              <div>
                <h3 className="text-base font-bold text-white font-mono flex items-center gap-2">
                  <Package className="w-4 h-4 text-brand-emerald" />
                  <span>{selectedOrder.order_number}</span>
                </h3>
                <p className="text-xs text-obsidian-400 font-mono mt-0.5 flex items-center gap-1">
                  <Clock className="w-3 h-3" />
                  <span>Placed {new Date(selectedOrder.created_at).toLocaleString()}</span>
                </p>
              </div>
              <button
                onClick={() => setSelectedOrder(null)}
                className="p-1 rounded-lg text-obsidian-400 hover:text-white"
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
            <div className="space-y-4 mb-6 p-4 rounded-xl bg-obsidian-850 border border-obsidian-750">
              <div className="flex items-start gap-2.5 text-xs text-obsidian-300">
                <MapPin className="w-4 h-4 text-brand-emerald shrink-0 mt-0.5" />
                <div>
                  <span className="font-semibold text-white block">Delivery Address:</span>
                  <p className="text-obsidian-400 mt-0.5">
                    {selectedOrder.shipping_address || "Address pending WhatsApp collection"}
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-2.5 text-xs text-obsidian-300">
                <CreditCard className="w-4 h-4 text-brand-cyan shrink-0" />
                <div>
                  <span className="font-semibold text-white">Customer Reference ID: </span>
                  <span className="font-mono text-obsidian-400">{selectedOrder.customer_id}</span>
                </div>
              </div>
            </div>

            {/* Line Items List */}
            <div className="space-y-3 flex-1 mb-6">
              <h4 className="text-xs font-bold uppercase tracking-wider text-obsidian-400 font-mono">
                Order Items ({selectedOrder.items?.length || 0})
              </h4>
              <div className="divide-y divide-obsidian-750/60 border border-obsidian-750 rounded-xl overflow-hidden bg-obsidian-850">
                {!selectedOrder.items || selectedOrder.items.length === 0 ? (
                  <div className="p-4 text-center text-xs text-obsidian-500 font-mono">
                    No line items attached
                  </div>
                ) : (
                  selectedOrder.items.map((item: OrderItemRead) => (
                    <div key={item.id} className="p-3 flex items-center justify-between text-xs">
                      <div>
                        <p className="font-semibold text-white">{item.product_name}</p>
                        <p className="text-obsidian-400 font-mono text-[11px]">
                          SKU: {item.sku} &bull; Qty: {item.quantity} &times; ${Number(item.unit_price).toFixed(2)}
                        </p>
                      </div>
                      <span className="font-mono font-bold text-white">
                        ${Number(item.subtotal).toFixed(2)}
                      </span>
                    </div>
                  ))
                )}
              </div>
            </div>

            {/* Financial Summary */}
            <div className="space-y-2 py-4 border-t border-obsidian-750 text-xs">
              <div className="flex justify-between text-obsidian-400">
                <span>Subtotal</span>
                <span className="font-mono">${Number(selectedOrder.subtotal).toFixed(2)}</span>
              </div>
              <div className="flex justify-between text-obsidian-400">
                <span>Shipping Cost</span>
                <span className="font-mono">${Number(selectedOrder.shipping_cost).toFixed(2)}</span>
              </div>
              <div className="flex justify-between text-sm font-bold text-white pt-2 border-t border-obsidian-750/60">
                <span>Total Amount</span>
                <span className="font-mono text-brand-emerald">
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
