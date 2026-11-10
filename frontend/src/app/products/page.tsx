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
  RefreshCw,
} from "lucide-react";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { Modal } from "@/components/ui/Modal";
import { Input } from "@/components/ui/Input";
import { CategoryRead, ProductRead } from "@/types";
import { productsService } from "@/services/products.service";

export default function ProductsPage() {
  const [products, setProducts] = useState<ProductRead[]>([]);
  const [categories, setCategories] = useState<CategoryRead[]>([]);
  const [selectedCategory, setSelectedCategory] = useState<string>("ALL");
  const [searchQuery, setSearchQuery] = useState("");
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Modal Form State
  const [name, setName] = useState("");
  const [sku, setSku] = useState("");
  const [price, setPrice] = useState("");
  const [stock, setStock] = useState("");
  const [description, setDescription] = useState("");
  const [categoryId, setCategoryId] = useState<string>("");
  const [isSaving, setIsSaving] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  /**
   * Fetches products and categories directly from backend routers:
   * 1. GET /api/v1/products   -> backend/app/modules/products/router.py:126
   * 2. GET /api/v1/categories -> backend/app/modules/products/router.py:73
   */
  const loadData = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const [prodRes, catRes] = await Promise.all([
        productsService.listProducts({
          search: searchQuery || undefined,
          category_id: selectedCategory !== "ALL" ? selectedCategory : undefined,
          page: 1,
          page_size: 100,
        }),
        productsService.listCategories(),
      ]);

      setProducts(prodRes.items);
      setCategories(catRes);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to load products from database.");
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [searchQuery, selectedCategory]);

  /**
   * Creates a product in PostgreSQL inventory via backend router:
   * POST /api/v1/products (backend/app/modules/products/router.py:100)
   */
  const handleCreateProduct = async (e: React.FormEvent) => {
    e.preventDefault();
    setFormError(null);
    setIsSaving(true);

    try {
      const parsedPrice = parseFloat(price);
      const parsedStock = parseInt(stock, 10);

      if (isNaN(parsedPrice) || parsedPrice <= 0) {
        throw new Error("Price must be a positive number.");
      }
      if (isNaN(parsedStock) || parsedStock < 0) {
        throw new Error("Stock quantity cannot be negative.");
      }

      const newProd = await productsService.createProduct({
        title: name.trim(),
        name: name.trim(),
        sku: sku.trim().toUpperCase(),
        price: parsedPrice,
        currency: "USD",
        stock_quantity: parsedStock,
        description: description.trim() || undefined,
        category_id: categoryId || undefined,
        category_ids: categoryId ? [categoryId] : [],
      });

      setProducts((prev) => [newProd, ...prev]);
      setIsModalOpen(false);
      setName("");
      setSku("");
      setPrice("");
      setStock("");
      setDescription("");
      setCategoryId("");
    } catch (err: unknown) {
      setFormError(err instanceof Error ? err.message : "Failed to create product in catalog.");
    } finally {
      setIsSaving(false);
    }
  };

  /**
   * Deletes a product via backend router:
   * DELETE /api/v1/products/{id} (backend/app/modules/products/router.py:207)
   */
  const handleDelete = async (id: string) => {
    if (!confirm("Are you sure you want to permanently delete this product?")) return;
    try {
      await productsService.deleteProduct(id);
      setProducts((prev) => prev.filter((p) => p.id !== id));
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : "Failed to delete product.");
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

        <div className="flex items-center gap-2">
          <Button variant="secondary" size="sm" onClick={loadData} isLoading={isLoading}>
            <RefreshCw className="w-3.5 h-3.5" />
            <span>Refresh</span>
          </Button>
          <Button onClick={() => setIsModalOpen(true)} size="sm">
            <Plus className="w-4 h-4" />
            <span>Add New Product</span>
          </Button>
        </div>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-brand-rose/10 border border-brand-rose/30 text-xs text-rose-300 flex items-center gap-2">
          <AlertCircle className="w-4 h-4 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Filter and Search Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div className="flex items-center gap-2 flex-1 max-w-md">
          <div className="relative flex-1">
            <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-obsidian-400" />
            <input
              type="text"
              placeholder="Search products by title or SKU..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full bg-obsidian-850 border border-obsidian-700/80 rounded-lg pl-9 pr-3.5 py-2 text-xs text-obsidian-100 placeholder:text-obsidian-500 focus:outline-none focus:border-brand-emerald"
            />
          </div>

          {categories.length > 0 && (
            <select
              value={selectedCategory}
              onChange={(e) => setSelectedCategory(e.target.value)}
              className="bg-obsidian-850 border border-obsidian-700/80 rounded-lg px-3 py-2 text-xs text-obsidian-200 focus:outline-none focus:border-brand-emerald"
            >
              <option value="ALL">All Categories</option>
              {categories.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name}
                </option>
              ))}
            </select>
          )}
        </div>

        <span className="text-xs text-obsidian-400 font-mono">
          Showing {products.length} catalog items
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
                <th className="py-3 px-4 font-semibold">Stock Quantity</th>
                <th className="py-3 px-4 font-semibold">Status</th>
                <th className="py-3 px-4 text-right font-semibold">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-obsidian-750/50">
              {products.length === 0 && !isLoading ? (
                <tr>
                  <td colSpan={6} className="py-12 text-center text-obsidian-400 space-y-2">
                    <Package className="w-8 h-8 text-obsidian-600 mx-auto" />
                    <p className="font-semibold text-white">Your product catalog is empty</p>
                    <p className="text-xs text-obsidian-500 max-w-sm mx-auto">
                      Click &quot;Add New Product&quot; to insert verified inventory that the AI agent can sell in WhatsApp.
                    </p>
                  </td>
                </tr>
              ) : (
                products.map((product) => {
                  const isOutOfStock = product.stock_quantity <= 0;
                  const isLowStock =
                    product.stock_quantity > 0 && product.stock_quantity <= 10;

                  return (
                    <tr
                      key={product.id}
                      className="hover:bg-obsidian-800/60 transition-colors"
                    >
                      <td className="py-3.5 px-4 font-semibold text-white">
                        {product.title || product.name}
                        {product.description && (
                          <p className="text-[11px] text-obsidian-400 font-normal truncate max-w-xs mt-0.5">
                            {product.description}
                          </p>
                        )}
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
        description="Persists verified product item into PostgreSQL database."
      >
        {formError && (
          <div className="mb-4 p-3 rounded-lg bg-brand-rose/10 border border-brand-rose/30 text-xs text-rose-300">
            {formError}
          </div>
        )}

        <form onSubmit={handleCreateProduct} className="space-y-4">
          <Input
            label="Product Title"
            placeholder="e.g. Organic Fuji Apples (1 lb)"
            value={name}
            onChange={(e) => setName(e.target.value)}
            required
          />

          <div className="grid grid-cols-2 gap-3">
            <Input
              label="SKU Code"
              placeholder="e.g. APP-FUJI-01"
              value={sku}
              onChange={(e) => setSku(e.target.value)}
              required
            />
            <Input
              label="Unit Price ($)"
              type="number"
              step="0.01"
              placeholder="3.50"
              value={price}
              onChange={(e) => setPrice(e.target.value)}
              icon={<DollarSign className="w-3.5 h-3.5" />}
              required
            />
          </div>

          <Input
            label="Initial Stock Inventory"
            type="number"
            placeholder="50"
            value={stock}
            onChange={(e) => setStock(e.target.value)}
            required
          />

          {categories.length > 0 && (
            <div className="space-y-1.5">
              <label className="block text-xs font-medium text-obsidian-300">Category</label>
              <select
                value={categoryId}
                onChange={(e) => setCategoryId(e.target.value)}
                className="w-full bg-obsidian-900 border border-obsidian-700/80 rounded-lg p-2 text-xs text-obsidian-100 focus:outline-none focus:border-brand-emerald"
              >
                <option value="">Uncategorized</option>
                {categories.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.name}
                  </option>
                ))}
              </select>
            </div>
          )}

          <div className="space-y-1.5">
            <label className="block text-xs font-medium text-obsidian-300">
              Description (Optional)
            </label>
            <textarea
              rows={3}
              placeholder="Crisp sweet organic Fuji apples freshly picked."
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
