"use client";

/**
 * Chatrio Customer Directory.
 *
 * Implements design-taste-frontend standards:
 * - Quiet panels, aligned figures, colour spent on data
 * - Warm white canvas (#FAF8F5) with terracotta (#EA580C) data highlights
 * - Direct client mapping to backend router:
 *   - GET /api/v1/customers -> backend/app/modules/customers/router.py:38
 */

import React, { useEffect, useState } from "react";
import Link from "next/link";
import {
  Users,
  Search,
  MessageSquare,
  Shield,
  ShieldAlert,
  ArrowUpRight,
  Phone,
  RefreshCw,
} from "lucide-react";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { CustomerRead } from "@/types";
import { customersService } from "@/services/customers.service";

export default function CustomersPage() {
  const [customers, setCustomers] = useState<CustomerRead[]>([]);
  const [total, setTotal] = useState(0);
  const [searchQuery, setSearchQuery] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchCustomers = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const res = await customersService.listCustomers({
        search: searchQuery || undefined,
        page: 1,
        page_size: 50,
      });
      setCustomers(res.items);
      setTotal(res.total);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to load customers from backend.");
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchCustomers();
  }, [searchQuery]);

  return (
    <div className="space-y-6 animate-in fade-in duration-150">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-border">
        <div>
          <div className="text-xs font-semibold uppercase tracking-wider text-accent mb-1 font-mono">
            Identity &amp; Profiles
          </div>
          <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-ink-900 flex items-center gap-2.5">
            Customer Directory
          </h1>
          <p className="text-xs sm:text-sm text-ink-500 mt-1">
            WhatsApp customer identities, verified phone numbers, and session histories.
          </p>
        </div>

        <Button variant="secondary" size="sm" onClick={fetchCustomers} isLoading={isLoading}>
          <RefreshCw className="w-3.5 h-3.5" />
          <span>Refresh</span>
        </Button>
      </div>

      {/* Search Bar */}
      <div className="flex items-center gap-3">
        <div className="relative flex-1 max-w-sm">
          <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-ink-400" />
          <input
            type="text"
            placeholder="Search by phone number or name..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full bg-white border border-border rounded-xl pl-9 pr-3.5 py-2 text-xs text-ink-900 placeholder:text-ink-400 focus:outline-none focus:border-accent focus:ring-2 focus:ring-accent/20 transition-colors shadow-sm"
          />
        </div>
        <span className="text-xs text-ink-500 font-mono">
          Total: {total} registered customers
        </span>
      </div>

      {error && (
        <div className="p-3.5 rounded-xl bg-rose-50 border border-rose-200 text-xs text-rose-700">
          {error}
        </div>
      )}

      {/* Customers Table */}
      <div className="quiet-panel overflow-hidden card-taste">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-canvas-subtle border-b border-border text-ink-500 font-mono">
              <tr>
                <th className="py-3.5 px-4 font-semibold">Customer</th>
                <th className="py-3.5 px-4 font-semibold">WhatsApp Phone</th>
                <th className="py-3.5 px-4 font-semibold">Status</th>
                <th className="py-3.5 px-4 font-semibold">First Seen</th>
                <th className="py-3.5 px-4 text-right font-semibold">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border/60">
              {customers.length === 0 && !isLoading ? (
                <tr>
                  <td colSpan={5} className="py-12 text-center text-ink-400 space-y-2">
                    <Users className="w-8 h-8 text-ink-300 mx-auto" />
                    <p className="font-semibold text-ink-900">No customers registered yet</p>
                    <p className="text-xs text-ink-500 max-w-sm mx-auto">
                      Customers who initiate chats with your store will be created automatically.
                    </p>
                  </td>
                </tr>
              ) : (
                customers.map((customer) => (
                  <tr
                    key={customer.id}
                    className="hover:bg-accent-light/50 transition-colors"
                  >
                    <td className="py-3.5 px-4 font-semibold text-ink-900 flex items-center gap-2.5">
                      <div className="w-7 h-7 rounded-lg bg-canvas-subtle border border-border flex items-center justify-center font-mono font-bold text-xs text-ink-900">
                        {customer.name ? customer.name[0].toUpperCase() : "C"}
                      </div>
                      <span>{customer.name || "WhatsApp Customer"}</span>
                    </td>
                    <td className="py-3.5 px-4 font-mono text-ink-600">
                      {customer.phone_number}
                    </td>
                    <td className="py-3.5 px-4">
                      {customer.is_blocked ? (
                        <Badge variant="critical" size="sm">
                          Blocked
                        </Badge>
                      ) : (
                        <Badge variant="success" size="sm">
                          Active
                        </Badge>
                      )}
                    </td>
                    <td className="py-3.5 px-4 font-mono text-ink-500">
                      {new Date(customer.created_at).toLocaleDateString()}
                    </td>
                    <td className="py-3.5 px-4 text-right">
                      <Link href={`/inbox?phone=${customer.phone_number}`} className="rounded-md transition-colors hover:text-accent">
                        <Button variant="ghost" size="sm">
                          <MessageSquare className="w-3.5 h-3.5" />
                          <span>Chat</span>
                        </Button>
                      </Link>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
