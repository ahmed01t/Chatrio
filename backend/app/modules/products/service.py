"""
Product Catalog and Inventory Business Logic Service Layer.

This module provides production-grade services:
1. `CategoryService`: Manages category creation, hierarchical nesting, and listing per tenant.
2. `ProductService`: Handles product CRUD, SKU uniqueness validation, category associations,
   and semantic vector search.
3. `InventoryService`: Manages real-time stock adjustments with row-level locks
   (`with_for_update()`) to prevent race conditions and overselling, while writing an immutable
   audit trail to `inventory_logs`.
"""

import uuid

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import (
    BadRequestException,
    ConflictException,
    NotFoundException,
)
from app.modules.auth.service import slugify
from app.modules.products.models import (
    Category,
    InventoryChangeReason,
    InventoryLog,
    Product,
    ProductCategory,
)
from app.modules.products.schemas import (
    CategoryCreate,
    CategoryUpdate,
    InventoryAdjustmentRequest,
    ProductCreate,
    ProductUpdate,
)


class CategoryService:
    """Service managing product category taxonomy per tenant."""

    @staticmethod
    async def create_category(
        session: AsyncSession,
        organization_id: uuid.UUID,
        request: CategoryCreate,
    ) -> Category:
        """
        Creates a new product category bound to the organization.
        Enforces unique category slug within the tenant.
        """
        slug = request.slug or slugify(request.name)

        # Check if slug exists in this tenant
        existing_query = select(Category).where(
            Category.organization_id == organization_id,
            Category.slug == slug,
        )
        existing = (await session.execute(existing_query)).scalar_one_or_none()
        if existing is not None:
            if request.slug:
                raise ConflictException(
                    code="CATEGORY_SLUG_EXISTS",
                    message=f"Category slug '{slug}' already exists in your store.",
                )
            slug = f"{slug}-{uuid.uuid4().hex[:6]}"

        # Validate parent category belongs to this organization
        if request.parent_id is not None:
            parent_query = select(Category).where(
                Category.organization_id == organization_id,
                Category.id == request.parent_id,
            )
            parent = (await session.execute(parent_query)).scalar_one_or_none()
            if parent is None:
                raise NotFoundException(
                    code="PARENT_CATEGORY_NOT_FOUND",
                    message="Specified parent category does not exist in your store.",
                )

        category = Category(
            id=uuid.uuid4(),
            organization_id=organization_id,
            name=request.name.strip(),
            slug=slug,
            description=request.description.strip() if request.description else None,
            parent_id=request.parent_id,
        )
        session.add(category)
        await session.flush()
        return category

    @staticmethod
    async def list_categories(
        session: AsyncSession,
        organization_id: uuid.UUID,
    ) -> list[Category]:
        """Lists all categories belonging to the organization."""
        query = (
            select(Category)
            .where(Category.organization_id == organization_id)
            .order_by(Category.name.asc())
        )
        return list((await session.execute(query)).scalars().all())

    @staticmethod
    async def get_category(
        session: AsyncSession,
        organization_id: uuid.UUID,
        category_id: uuid.UUID,
    ) -> Category:
        """Retrieves a single category by ID, enforcing tenant boundary."""
        query = select(Category).where(
            Category.organization_id == organization_id,
            Category.id == category_id,
        )
        category = (await session.execute(query)).scalar_one_or_none()
        if category is None:
            raise NotFoundException(
                code="CATEGORY_NOT_FOUND",
                message="Category not found.",
            )
        return category

    @staticmethod
    async def update_category(
        session: AsyncSession,
        organization_id: uuid.UUID,
        category_id: uuid.UUID,
        request: CategoryUpdate,
    ) -> Category:
        """Updates category name, slug, description, or parent hierarchy."""
        category = await CategoryService.get_category(session, organization_id, category_id)

        if request.name is not None:
            category.name = request.name.strip()
        if request.description is not None:
            category.description = request.description.strip()

        if request.slug is not None:
            new_slug = slugify(request.slug)
            if new_slug != category.slug:
                existing_query = select(Category).where(
                    Category.organization_id == organization_id,
                    Category.slug == new_slug,
                    Category.id != category_id,
                )
                if (await session.execute(existing_query)).scalar_one_or_none():
                    raise ConflictException(
                        code="CATEGORY_SLUG_EXISTS",
                        message=f"Category slug '{new_slug}' is already in use.",
                    )
                category.slug = new_slug

        if request.parent_id is not None:
            if request.parent_id == category_id:
                raise BadRequestException(
                    code="INVALID_PARENT_CATEGORY",
                    message="A category cannot be its own parent.",
                )
            parent_query = select(Category).where(
                Category.organization_id == organization_id,
                Category.id == request.parent_id,
            )
            if not (await session.execute(parent_query)).scalar_one_or_none():
                raise NotFoundException(
                    code="PARENT_CATEGORY_NOT_FOUND",
                    message="Parent category not found.",
                )
            category.parent_id = request.parent_id

        await session.flush()
        return category

    @staticmethod
    async def delete_category(
        session: AsyncSession,
        organization_id: uuid.UUID,
        category_id: uuid.UUID,
    ) -> None:
        """Deletes a category belonging to the organization."""
        category = await CategoryService.get_category(session, organization_id, category_id)
        await session.delete(category)
        await session.flush()


class ProductService:
    """Service managing product catalog items and semantic search per tenant."""

    @staticmethod
    async def create_product(
        session: AsyncSession,
        organization_id: uuid.UUID,
        request: ProductCreate,
        embedding: list[float] | None = None,
    ) -> Product:
        """
        Creates a new product within the organization's catalog.
        Enforces unique SKU per tenant.
        Links requested categories and writes an initial inventory audit log if initial stock > 0.
        """
        sku_clean = request.sku.strip()

        # Enforce SKU uniqueness within this tenant organization
        existing_sku_query = select(Product).where(
            Product.organization_id == organization_id,
            Product.sku == sku_clean,
        )
        existing = (await session.execute(existing_sku_query)).scalar_one_or_none()
        if existing is not None:
            raise ConflictException(
                code="SKU_ALREADY_EXISTS",
                message=f"A product with SKU '{sku_clean}' already exists in your store.",
            )

        # Validate that all requested categories exist in this organization
        if request.category_ids:
            cat_query = select(Category.id).where(
                Category.organization_id == organization_id,
                Category.id.in_(request.category_ids),
            )
            found_ids = set((await session.execute(cat_query)).scalars().all())
            missing = set(request.category_ids) - found_ids
            if missing:
                raise NotFoundException(
                    code="CATEGORIES_NOT_FOUND",
                    message=f"Categories not found in your store: {[str(m) for m in missing]}",
                )

        product = Product(
            id=uuid.uuid4(),
            organization_id=organization_id,
            title=request.title.strip(),
            description=request.description.strip() if request.description else None,
            sku=sku_clean,
            price=request.price,
            currency=request.currency.strip().upper(),
            stock_quantity=request.stock_quantity,
            is_active=request.is_active,
            embedding=embedding,
        )
        session.add(product)
        await session.flush()

        # Link product to categories
        for cat_id in request.category_ids:
            link = ProductCategory(product_id=product.id, category_id=cat_id)
            session.add(link)

        # If created with initial stock > 0, write audit log
        if request.stock_quantity > 0:
            log = InventoryLog(
                id=uuid.uuid4(),
                organization_id=organization_id,
                product_id=product.id,
                change_amount=request.stock_quantity,
                balance_after=request.stock_quantity,
                reason=InventoryChangeReason.RESTOCK,
                reference_id="INITIAL_STOCK",
            )
            session.add(log)

        await session.flush()
        return await ProductService.get_product(session, organization_id, product.id)

    @staticmethod
    async def get_product(
        session: AsyncSession,
        organization_id: uuid.UUID,
        product_id: uuid.UUID,
    ) -> Product:
        """Retrieves a single product with eager-loaded categories, enforcing tenant boundary."""
        query = (
            select(Product)
            .options(selectinload(Product.categories))
            .where(
                Product.organization_id == organization_id,
                Product.id == product_id,
            )
        )
        product = (await session.execute(query)).scalar_one_or_none()
        if product is None:
            raise NotFoundException(
                code="PRODUCT_NOT_FOUND",
                message="Product not found in your store.",
            )
        return product

    @staticmethod
    async def list_products(
        session: AsyncSession,
        organization_id: uuid.UUID,
        page: int = 1,
        page_size: int = 20,
        category_id: uuid.UUID | None = None,
        is_active: bool | None = None,
        search: str | None = None,
    ) -> tuple[list[Product], int]:
        """
        Lists tenant products with pagination, category filter, active filter, and search.
        Returns a tuple of (items, total_count).
        """
        base_query = select(Product).where(Product.organization_id == organization_id)

        if is_active is not None:
            base_query = base_query.where(Product.is_active.is_(is_active))

        if category_id is not None:
            base_query = base_query.join(ProductCategory).where(
                ProductCategory.category_id == category_id
            )

        if search:
            search_clean = f"%{search.strip().lower()}%"
            base_query = base_query.where(
                func.lower(Product.title).like(search_clean)
                | func.lower(Product.sku).like(search_clean)
            )

        # Count total items matching filters
        count_query = select(func.count()).select_from(base_query.subquery())
        total = (await session.execute(count_query)).scalar_one()

        # Fetch paginated items with eager-loaded categories
        items_query = (
            base_query.options(selectinload(Product.categories))
            .order_by(Product.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        items = list((await session.execute(items_query)).scalars().all())

        return items, total

    @staticmethod
    async def update_product(
        session: AsyncSession,
        organization_id: uuid.UUID,
        product_id: uuid.UUID,
        request: ProductUpdate,
        embedding: list[float] | None = None,
    ) -> Product:
        """Updates product metadata, price, active status, or category assignments."""
        product = await ProductService.get_product(session, organization_id, product_id)

        if request.title is not None:
            product.title = request.title.strip()
        if request.description is not None:
            product.description = request.description.strip()
        if request.price is not None:
            product.price = request.price
        if request.currency is not None:
            product.currency = request.currency.strip().upper()
        if request.is_active is not None:
            product.is_active = request.is_active
        if embedding is not None:
            product.embedding = embedding

        if request.sku is not None:
            sku_clean = request.sku.strip()
            if sku_clean != product.sku:
                existing_query = select(Product).where(
                    Product.organization_id == organization_id,
                    Product.sku == sku_clean,
                    Product.id != product_id,
                )
                if (await session.execute(existing_query)).scalar_one_or_none():
                    raise ConflictException(
                        code="SKU_ALREADY_EXISTS",
                        message=f"SKU '{sku_clean}' is already in use by another product.",
                    )
                product.sku = sku_clean

        # Update categories if specified
        if request.category_ids is not None:
            # Clear old mappings
            del_stmt = delete(ProductCategory).where(ProductCategory.product_id == product_id)
            await session.execute(del_stmt)

            # Add new mappings
            for cat_id in request.category_ids:
                link = ProductCategory(product_id=product_id, category_id=cat_id)
                session.add(link)

        await session.flush()
        return await ProductService.get_product(session, organization_id, product_id)

    @staticmethod
    async def delete_product(
        session: AsyncSession,
        organization_id: uuid.UUID,
        product_id: uuid.UUID,
    ) -> None:
        """Deletes a product belonging to the organization."""
        product = await ProductService.get_product(session, organization_id, product_id)
        await session.delete(product)
        await session.flush()

    @staticmethod
    async def search_semantic(
        session: AsyncSession,
        organization_id: uuid.UUID,
        query_vector: list[float],
        limit: int = 5,
        min_similarity: float = 0.5,
    ) -> list[tuple[Product, float]]:
        """
        Performs semantic vector search over tenant products using cosine similarity.
        Cosine similarity = 1 - Cosine Distance.
        Returns list of tuples (Product, similarity_score).
        """
        # Distance calculation via pgvector
        distance = Product.embedding.cosine_distance(query_vector)
        similarity = (1.0 - distance).label("similarity")

        query = (
            select(Product, similarity)
            .options(selectinload(Product.categories))
            .where(
                Product.organization_id == organization_id,
                Product.is_active.is_(True),
                Product.embedding.is_not(None),
            )
            .order_by(distance.asc())
            .limit(limit)
        )

        results = (await session.execute(query)).all()
        # Filter by minimum similarity score
        return [(prod, float(sim)) for prod, sim in results if float(sim) >= min_similarity]


class InventoryService:
    """
    Mission-critical inventory service.
    Implements row-level locking (`with_for_update()`) to prevent overselling race conditions
    and appends immutable audit records to `inventory_logs`.
    """

    @staticmethod
    async def adjust_stock(
        session: AsyncSession,
        organization_id: uuid.UUID,
        product_id: uuid.UUID,
        request: InventoryAdjustmentRequest,
    ) -> tuple[Product, InventoryLog]:
        """
        Atomically adjusts inventory stock for a product with a database row-level lock.

        Locking mechanism:
        `with_for_update()` locks the specific product row in PostgreSQL. If 2 requests
        try to modify stock simultaneously, the second waits for the first to complete.
        This guarantees zero race conditions.

        Raises:
            NotFoundException: If the product does not exist in this tenant.
            BadRequestException: If adjustment would reduce stock below 0.
        """
        # Row-level lock: SELECT ... FOR UPDATE
        lock_query = (
            select(Product)
            .where(
                Product.organization_id == organization_id,
                Product.id == product_id,
            )
            .with_for_update()
        )
        product = (await session.execute(lock_query)).scalar_one_or_none()
        if product is None:
            raise NotFoundException(
                code="PRODUCT_NOT_FOUND",
                message="Product not found in your store.",
            )

        new_balance = product.stock_quantity + request.change_amount
        if new_balance < 0:
            raise BadRequestException(
                code="INSUFFICIENT_STOCK",
                message=(
                    f"Insufficient inventory stock. Current available: {product.stock_quantity}, "
                    f"requested deduction: {abs(request.change_amount)}."
                ),
                details={
                    "available_stock": product.stock_quantity,
                    "requested_change": request.change_amount,
                },
            )

        # Update product balance
        product.stock_quantity = new_balance

        # Create immutable audit log entry
        log_entry = InventoryLog(
            id=uuid.uuid4(),
            organization_id=organization_id,
            product_id=product.id,
            change_amount=request.change_amount,
            balance_after=new_balance,
            reason=request.reason,
            reference_id=request.reference_id,
        )
        session.add(log_entry)
        await session.flush()

        # Reload with relationships
        full_product = await ProductService.get_product(session, organization_id, product_id)
        return full_product, log_entry

    @staticmethod
    async def get_inventory_logs(
        session: AsyncSession,
        organization_id: uuid.UUID,
        product_id: uuid.UUID,
        limit: int = 50,
    ) -> list[InventoryLog]:
        """Retrieves the audit trail of inventory adjustments for a product."""
        # Ensure product belongs to organization
        await ProductService.get_product(session, organization_id, product_id)

        query = (
            select(InventoryLog)
            .where(
                InventoryLog.organization_id == organization_id,
                InventoryLog.product_id == product_id,
            )
            .order_by(InventoryLog.created_at.desc())
            .limit(limit)
        )
        return list((await session.execute(query)).scalars().all())

