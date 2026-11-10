"use client";

import React, { useEffect, useState } from "react";
import {
  Package,
  Plus,
  Search,
  Trash2,
  DollarSign,
  AlertCircle,
  CheckCircle2,
} from "lucide-react";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { Modal } from "@/components/ui/Modal";
import { Input } from "@/components/ui/Input";
import { Product } from "@/types";
import { api } from "@/lib/api";

export default function ProductsPage() {
  const [products, setProducts] = useState<Product[]>([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  // Form state
  const [name, setName] = useState("");
  const [sku, setSku] = useState("");
  const [price, setPrice] = useState("");
  const [stock, setStock] = useState("");
  const [description, setDescription] = useState("");
  const [isSaving, setIsSaving] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  const fetchProducts = async () => {
    setIsLoading(true);
    try {
      const items = await api.getProducts({ search: searchQuery });
      setProducts(items);
    } catch (err) {
      console.error("Failed to load products:", err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchProducts();
  }, [searchQuery]);

  const handleCreateProduct = async (e: React.FormEvent) => {
    e.preventDefault();
    setFormError(null);
    setIsSaving(true);

    try {
      const parsedPrice = parseFloat(price);
      const parsedStock = parseInt(stock, 10);

      if (isNaN(parsedPrice) || parsedPrice <= 0) {
        throw new Error("Price must be a valid positive number.");
      }
      if (isNaN(parsedStock) || parsedStock < 0) {
        throw new Error("Stock must be zero or greater.");
      }

      const newProd = await api.createProduct({
        name,
        sku: sku.toUpperCase(),
        price: parsedPrice,
        stock_quantity: parsedStock,
        description: description || undefined,
      });

      setProducts((prev) => [newProd, ...prev]);
      setIsModalOpen(false);
      setName("");
      setSku("");
      setPrice("");
      setStock("");
      setDescription("");
    } catch (err: unknown) {
      setFormError(err instanceof Error ? err.message : "Failed to create product.");
    } finally {
      setIsSaving(false);
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm("Are you sure you want to remove this product from the catalog?")) return;
    try {
      await api.deleteProduct(id);
      setProducts((prev) => prev.filter((p) => p.id !== id));
    } catch (err) {
      console.error("Failed to delete product:", err);
    }
  };

  return (
    <div className="space-y-6 animate-in fade-in duration-150">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-obsidian-800">
        <div>
          <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-white flex items-center gap-2">
            <Package className="w-6 h-6 text-brand-emerald" />
            <span>Product Catalog & Inventory</span>
          </h1>
          <p className="text-xs sm:text-sm text-obsidian-400 mt-1">
            Deterministic products and pricing accessible to the LangGraph AI agent.
          </p>
        </div>
        <Button onClick={() => setIsModalOpen(true)} size="md">
          <Plus className="w-4 h-4" />
          <span>Add New Product</span>
        </Button>
      </div>

      {/* Filter and Search Bar */}
      <div className="flex items-center gap-3">
        <div className="relative flex-1 max-w-sm">
          <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-obsidian-400" />
          <input
            type="text"
            placeholder="Search products by title or SKU..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full bg-obsidian-850 border border-obsidian-700/80 rounded-lg pl-9 pr-3.5 py-2 text-xs text-obsidian-100 placeholder:text-obsidian-500 focus:outline-none focus:border-brand-emerald"
          />
        </div>
        <span className="text-xs text-obsidian-400 font-mono">
          Showing {products.length} products
        </span>
      </div>

      {/* Products Table Card */}
      <div className="bg-obsidian-850/80 border border-obsidian-750/90 rounded-xl shadow-card overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-obsidian-900 border-b border-obsidian-750/70 text-obsidian-400 font-mono">
              <tr>
                <th className="py-3 px-4 font-semibold">Product Name</th>
                <th className="py-3 px-4 font-semibold">SKU</th>
                <th className="py-3 px-4 font-semibold">Price</th>
                <th className="py-3 px-4 font-semibold">Inventory Stock</th>
                <th className="py-3 px-4 font-semibold">Status</th>
                <th className="py-3 px-4 text-right font-semibold">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-obsidian-750/50">
              {products.length === 0 && !isLoading ? (
                <tr>
                  <td colSpan={6} className="py-8 text-center text-obsidian-400">
                    No products found in your catalog. Click &quot;Add New Product&quot; to begin!
                  </td>
                </tr>
              ) : (
                (products.length > 0
                  ? products
                  : [
                      {
                        id: "p1",
                        organization_id: "org1",
                        name: "Organic Fuji Apples",
                        sku: "APP-FUJI-01",
                        price: 3.5,
                        stock_quantity: 45,
                        is_active: true,
                        created_at: "2026-11-10",
                        updated_at: "2026-11-10",
                      },
                      {
                        id: "p2",
                        organization_id: "org1",
                        name: "Valencia Sweet Oranges",
                        sku: "ORG-VAL-02",
                        price: 2.99,
                        stock_quantity: 8,
                        is_active: true,
                        created_at: "2026-11-10",
                        updated_at: "2026-11-10",
                      },
                      {
                        id: "p3",
                        organization_id: "org1",
                        name: "Alphonso Mango Box",
                        sku: "MNG-ALP-03",
                        price: 24.99,
                        stock_quantity: 0,
                        is_active: false,
                        created_at: "2026-11-10",
                        updated_at: "2026-11-10",
                      },
                    ]
                ).map((product) => {
                  const isOutOfStock = product.stock_quantity <= 0;
                  const isLowStock = product.stock_quantity > 0 && product.stock_quantity <= 10;

                  return (
                    <tr
                      key={product.id}
                      className="hover:bg-obsidian-800/60 transition-colors"
                    >
                      <td className="py-3.5 px-4 font-semibold text-white">
                        {product.name}
                      </td>
                      <td className="py-3.5 px-4 font-mono text-obsidian-400">
                        {product.sku}
                      </td>
                      <td className="py-3.5 px-4 font-mono font-bold text-white">
                        ${Number(product.price).toFixed(2)}
                      </td>
                      <td className="py-3.5 px-4">
                        <div className="flex items-center gap-1.5 font-mono">
                          {isOutOfStock ? (
                            <Badge variant="critical" size="sm">
                              Out of stock (0)
                            </Badge>
                          ) : isLowStock ? (
                            <Badge variant="warning" size="sm">
                              Low ({product.stock_quantity})
                            </Badge>
                          ) : (
                            <Badge variant="success" size="sm">
                              In Stock ({product.stock_quantity})
                            </Badge>
                          )}
                        </div>
                      </td>
                      <td className="py-3.5 px-4">
                        {product.is_active ? (
                          <span className="flex items-center gap-1 text-[11px] text-brand-emerald">
                            <CheckCircle2 className="w-3.5 h-3.5" /> Active
                          </span>
                        ) : (
                          <span className="flex items-center gap-1 text-[11px] text-obsidian-500">
                            <AlertCircle className="w-3.5 h-3.5" /> Inactive
                          </span>
                        )}
                      </td>
                      <td className="py-3.5 px-4 text-right">
                        <button
                          onClick={() => handleDelete(product.id)}
                          className="p-1.5 rounded-lg text-obsidian-400 hover:text-brand-rose hover:bg-brand-rose/10 transition-colors"
                          title="Delete Product"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Add Product Modal */}
      <Modal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        title="Add New Catalog Product"
        description="Add a verified item to your PostgreSQL inventory for AI automated ordering."
      >
        {formError && (
          <div className="mb-4 p-3 rounded-lg bg-brand-rose/10 border border-brand-rose/30 text-xs text-rose-300">
            {formError}
          </div>
        )}

        <form onSubmit={handleCreateProduct} className="space-y-4">
          <Input
            label="Product Title"
            placeholder="e.g. Hass Avocado (4 Pack)"
            value={name}
            onChange={(e) => setName(e.target.value)}
            required
          />

          <div className="grid grid-cols-2 gap-3">
            <Input
              label="SKU Code"
              placeholder="e.g. AVO-HASS-04"
              value={sku}
              onChange={(e) => setSku(e.target.value)}
              required
            />
            <Input
              label="Unit Price ($)"
              type="number"
              step="0.01"
              placeholder="4.99"
              value={price}
              onChange={(e) => setPrice(e.target.value)}
              icon={<DollarSign className="w-3.5 h-3.5" />}
              required
            />
          </div>

          <Input
            label="Initial Stock Quantity"
            type="number"
            placeholder="50"
            value={stock}
            onChange={(e) => setStock(e.target.value)}
            required
          />

          <div className="space-y-1.5">
            <label className="block text-xs font-medium text-obsidian-300">
              Description (Optional)
            </label>
            <textarea
              rows={3}
              placeholder="Fresh ripe Hass avocados, imported and ready to eat."
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              className="w-full bg-obsidian-900 border border-obsidian-700/80 rounded-lg p-3 text-xs text-obsidian-100 placeholder:text-obsidian-500 focus:outline-none focus:border-brand-emerald"
            />
          </div>

          <div className="flex justify-end gap-2 pt-3 border-t border-obsidian-750/70">
            <Button
              type="button"
              variant="secondary"
              size="sm"
              onClick={() => setIsModalOpen(false)}
            >
              Cancel
            </Button>
            <Button type="submit" size="sm" isLoading={isSaving}>
              Save to Catalog
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
}

