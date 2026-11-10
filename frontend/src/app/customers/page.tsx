"use client";

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
      // Calls backend router: GET /api/v1/customers (backend/app/modules/customers/router.py:49)
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
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-obsidian-800">
        <div>
          <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-white flex items-center gap-2">
            <Users className="w-6 h-6 text-brand-emerald" />
            <span>Customer Directory</span>
          </h1>
          <p className="text-xs sm:text-sm text-obsidian-400 mt-1">
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
          <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-obsidian-400" />
          <input
            type="text"
            placeholder="Search by phone number or name..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full bg-obsidian-850 border border-obsidian-700/80 rounded-lg pl-9 pr-3.5 py-2 text-xs text-obsidian-100 placeholder:text-obsidian-500 focus:outline-none focus:border-brand-emerald"
          />
        </div>
        <span className="text-xs text-obsidian-400 font-mono">
          Total: {total} registered customers
        </span>
      </div>

      {error && (
        <div className="p-3.5 rounded-xl bg-brand-rose/10 border border-brand-rose/30 text-xs text-rose-300">
          {error}
        </div>
      )}

      {/* Customers Table */}
      <div className="bg-obsidian-850/80 border border-obsidian-750/90 rounded-xl shadow-card overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-obsidian-900 border-b border-obsidian-750/70 text-obsidian-400 font-mono">
              <tr>
                <th className="py-3 px-4 font-semibold">Customer</th>
                <th className="py-3 px-4 font-semibold">WhatsApp Phone</th>
                <th className="py-3 px-4 font-semibold">Account Status</th>
                <th className="py-3 px-4 font-semibold">First Contact</th>
                <th className="py-3 px-4 text-right font-semibold">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-obsidian-750/50">
              {customers.length === 0 && !isLoading ? (
                <tr>
                  <td colSpan={5} className="py-12 text-center text-obsidian-400">
                    <Users className="w-8 h-8 text-obsidian-600 mx-auto mb-2" />
                    <p className="font-semibold text-white">No customer profiles found</p>
                    <p className="text-xs text-obsidian-500 mt-1">
                      Customers are automatically captured when they send an inbound WhatsApp message.
                    </p>
                  </td>
                </tr>
              ) : (
                customers.map((customer) => (
                  <tr key={customer.id} className="hover:bg-obsidian-800/60 transition-colors">
                    <td className="py-3.5 px-4 font-semibold text-white flex items-center gap-2.5">
                      <div className="w-8 h-8 rounded-lg bg-obsidian-800 border border-obsidian-700 flex items-center justify-center font-mono font-bold text-xs text-brand-emerald">
                        {customer.name ? customer.name[0].toUpperCase() : "C"}
                      </div>
                      <span>{customer.name || "WhatsApp User"}</span>
                    </td>
                    <td className="py-3.5 px-4 font-mono text-obsidian-300">
                      <div className="flex items-center gap-1.5">
                        <Phone className="w-3.5 h-3.5 text-obsidian-500" />
                        <span>{customer.phone_number}</span>
                      </div>
                    </td>
                    <td className="py-3.5 px-4">
                      {customer.is_blocked ? (
                        <Badge variant="critical" size="sm">
                          <ShieldAlert className="w-3 h-3" />
                          <span>Blocked</span>
                        </Badge>
                      ) : (
                        <Badge variant="success" size="sm">
                          <Shield className="w-3 h-3" />
                          <span>Verified</span>
                        </Badge>
                      )}
                    </td>
                    <td className="py-3.5 px-4 font-mono text-obsidian-400">
                      {new Date(customer.created_at).toLocaleDateString()}
                    </td>
                    <td className="py-3.5 px-4 text-right">
                      <Link href={`/inbox?phone=${encodeURIComponent(customer.phone_number)}`}>
                        <Button variant="ghost" size="sm">
                          <MessageSquare className="w-3.5 h-3.5 text-brand-cyan" />
                          <span>Chat</span>
                          <ArrowUpRight className="w-3 h-3" />
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

