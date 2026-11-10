"use client";

import React, { useEffect, useState } from "react";
import {
  ShoppingCart,
  Search,
  MapPin,
  Clock,
  X,
  CreditCard,
} from "lucide-react";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { Order, OrderStatus } from "@/types";
import { api } from "@/lib/api";

export default function OrdersPage() {
  const [orders, setOrders] = useState<Order[]>([]);
  const [selectedOrder, setSelectedOrder] = useState<Order | null>(null);
  const [statusFilter, setStatusFilter] = useState<string>("ALL");
  const [searchQuery, setSearchQuery] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [isUpdatingStatus, setIsUpdatingStatus] = useState(false);

  const fetchOrders = async () => {
    setIsLoading(true);
    try {
      const filter = statusFilter !== "ALL" ? (statusFilter as OrderStatus) : undefined;
      const items = await api.getOrders({ status: filter });
      setOrders(items);
    } catch (err) {
      console.error("Failed to load orders:", err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchOrders();
  }, [statusFilter]);

  const handleUpdateStatus = async (newStatus: OrderStatus) => {
    if (!selectedOrder) return;
    setIsUpdatingStatus(true);
    try {
      const updated = await api.updateOrderStatus(selectedOrder.id, newStatus);
      setSelectedOrder(updated);
      setOrders((prev) => prev.map((o) => (o.id === updated.id ? updated : o)));
    } catch (err) {
      console.error("Failed to update status:", err);
    } finally {
      setIsUpdatingStatus(false);
    }
  };

  const filteredOrders = orders.filter((o) =>
    o.order_number.toLowerCase().includes(searchQuery.toLowerCase()) ||
    (o.customer_phone || "").toLowerCase().includes(searchQuery.toLowerCase())
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
            Orders assembled conversationally by LangGraph AI agent and committed to PostgreSQL.
          </p>
        </div>
      </div>

      {/* Filter Tabs & Search */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div className="flex flex-wrap gap-1.5 bg-obsidian-900 p-1 rounded-xl border border-obsidian-750/70">
          {["ALL", "PENDING", "CONFIRMED", "SHIPPED", "CANCELLED"].map((status) => (
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
            placeholder="Search order # or phone..."
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
                <th className="py-3 px-4 font-semibold">Customer Phone</th>
                <th className="py-3 px-4 font-semibold">Total Amount</th>
                <th className="py-3 px-4 font-semibold">Payment</th>
                <th className="py-3 px-4 font-semibold">Order Status</th>
                <th className="py-3 px-4 text-right font-semibold">Details</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-obsidian-750/50">
              {filteredOrders.length === 0 && !isLoading ? (
                <tr>
                  <td colSpan={6} className="py-8 text-center text-obsidian-400">
                    No orders matching your filters.
                  </td>
                </tr>
              ) : (
                (filteredOrders.length > 0
                  ? filteredOrders
                  : [
                      {
                        id: "ord-1",
                        organization_id: "org1",
                        customer_id: "c1",
                        order_number: "ORD-9021",
                        customer_phone: "+1 (415) 555-2671",
                        total_amount: 32.5,
                        subtotal: 27.5,
                        shipping_cost: 5.0,
                        status: "PENDING" as OrderStatus,
                        payment_status: "PAID" as const,
                        currency: "USD",
                        shipping_address: "742 Evergreen Terrace, Springfield",
                        created_at: "2026-11-10T14:20:00Z",
                        updated_at: "2026-11-10T14:20:00Z",
                        items: [
                          {
                            id: "i1",
                            product_id: "p1",
                            product_name: "Organic Fuji Apples",
                            sku: "APP-FUJI-01",
                            unit_price: 3.5,
                            quantity: 5,
                            subtotal: 17.5,
                          },
                          {
                            id: "i2",
                            product_id: "p2",
                            product_name: "Valencia Sweet Oranges",
                            sku: "ORG-VAL-02",
                            unit_price: 2.99,
                            quantity: 2,
                            subtotal: 5.98,
                          },
                        ],
                      },
                      {
                        id: "ord-2",
                        organization_id: "org1",
                        customer_id: "c2",
                        order_number: "ORD-9020",
                        customer_phone: "+1 (650) 555-8932",
                        total_amount: 54.98,
                        subtotal: 49.98,
                        shipping_cost: 5.0,
                        status: "CONFIRMED" as OrderStatus,
                        payment_status: "PAID" as const,
                        currency: "USD",
                        shipping_address: "100 Market St, San Francisco, CA",
                        created_at: "2026-11-10T12:00:00Z",
                        updated_at: "2026-11-10T12:00:00Z",
                        items: [
                          {
                            id: "i3",
                            product_id: "p3",
                            product_name: "Alphonso Mango Box",
                            sku: "MNG-ALP-03",
                            unit_price: 24.99,
                            quantity: 2,
                            subtotal: 49.98,
                          },
                        ],
                      },
                    ]
                ).map((order) => (
                  <tr
                    key={order.id}
                    className="hover:bg-obsidian-800/60 transition-colors cursor-pointer"
                    onClick={() => setSelectedOrder(order)}
                  >
                    <td className="py-3.5 px-4 font-mono font-bold text-white">
                      {order.order_number}
                    </td>
                    <td className="py-3.5 px-4 font-mono text-obsidian-300">
                      {order.customer_phone}
                    </td>
                    <td className="py-3.5 px-4 font-mono font-bold text-white">
                      ${Number(order.total_amount).toFixed(2)}
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
                <h3 className="text-base font-bold text-white font-mono">
                  {selectedOrder.order_number}
                </h3>
                <p className="text-xs text-obsidian-400 font-mono mt-0.5">
                  Placed {new Date(selectedOrder.created_at).toLocaleString()}
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
              <Badge variant="active" size="md">
                Status: {selectedOrder.status}
              </Badge>
              <Badge variant="success" size="md">
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
                  <span className="font-semibold text-white">Recipient Phone: </span>
                  <span className="font-mono text-obsidian-400">{selectedOrder.customer_phone}</span>
                </div>
              </div>
            </div>

            {/* Line Items List */}
            <div className="space-y-3 flex-1 mb-6">
              <h4 className="text-xs font-bold uppercase tracking-wider text-obsidian-400 font-mono">
                Line Items
              </h4>
              <div className="divide-y divide-obsidian-750/60 border border-obsidian-750 rounded-xl overflow-hidden bg-obsidian-850">
                {selectedOrder.items?.map((item) => (
                  <div key={item.id} className="p-3 flex items-center justify-between text-xs">
                    <div>
                      <p className="font-semibold text-white">{item.product_name}</p>
                      <p className="text-obsidian-400 font-mono text-[11px]">
                        Qty: {item.quantity} × ${Number(item.unit_price).toFixed(2)}
                      </p>
                    </div>
                    <span className="font-mono font-bold text-white">
                      ${Number(item.subtotal).toFixed(2)}
                    </span>
                  </div>
                ))}
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

            {/* Status Actions */}
            <div className="space-y-2 pt-2">
              {selectedOrder.status === "PENDING" && (
                <Button
                  className="w-full"
                  size="md"
                  onClick={() => handleUpdateStatus("CONFIRMED")}
                  isLoading={isUpdatingStatus}
                >
                  Confirm Order
                </Button>
              )}
              {selectedOrder.status === "CONFIRMED" && (
                <Button
                  className="w-full"
                  size="md"
                  onClick={() => handleUpdateStatus("SHIPPED")}
                  isLoading={isUpdatingStatus}
                >
                  Mark as Shipped
                </Button>
              )}
              {selectedOrder.status !== "CANCELLED" && selectedOrder.status !== "DELIVERED" && (
                <Button
                  variant="danger"
                  className="w-full"
                  size="sm"
                  onClick={() => handleUpdateStatus("CANCELLED")}
                  isLoading={isUpdatingStatus}
                >
                  Cancel Order
                </Button>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

