"""
Customer Business Service Layer.

Implements business logic for customer lifecycle management:
1. Normalized customer retrieval and upsert (get-or-create by phone).
2. Customer creation and profile updates.
3. Paginated customer directory listings.
"""

import uuid
from collections.abc import Sequence

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictException, NotFoundException
from app.modules.customers.models import Customer
from app.modules.customers.schemas import (
    CustomerCreate,
    CustomerUpdate,
    normalize_e164_phone,
)


class CustomerService:
    """Service handling multi-tenant Customer operations."""

    @staticmethod
    async def get_or_create_customer(
        session: AsyncSession,
        organization_id: uuid.UUID,
        phone_number: str,
        name: str | None = None,
    ) -> tuple[Customer, bool]:
        """
        Retrieves an existing customer by phone or creates a new one.

        Returns:
            tuple[Customer, bool]: (customer_instance, was_created_flag)
        """
        normalized_phone = normalize_e164_phone(phone_number)

        query = select(Customer).where(
            Customer.organization_id == organization_id,
            Customer.phone_number == normalized_phone,
        )
        existing = (await session.execute(query)).scalar_one_or_none()

        if existing is not None:
            # If name is provided and existing record lacks a name, update it
            if name and not existing.name:
                existing.name = name.strip()
                await session.flush()
                await session.refresh(existing)
            return existing, False

        # Create new customer
        customer = Customer(
            id=uuid.uuid4(),
            organization_id=organization_id,
            phone_number=normalized_phone,
            name=name.strip() if name else None,
            is_blocked=False,
        )
        session.add(customer)
        #session.flush() is used to synchronize the changes to the database and return the generated id
        await session.flush()
        await session.refresh(customer)
        return customer, True

    @staticmethod
    async def create_customer(
        session: AsyncSession,
        organization_id: uuid.UUID,
        request: CustomerCreate,
    ) -> Customer:
        """Explicitly registers a new customer profile. Rejects duplicate phone numbers."""
        normalized_phone = normalize_e164_phone(request.phone_number)

        # Enforce unique phone per tenant
        query = select(Customer).where(
            Customer.organization_id == organization_id,
            Customer.phone_number == normalized_phone,
        )
        existing = (await session.execute(query)).scalar_one_or_none()
        if existing is not None:
            raise ConflictException(
                code="CUSTOMER_ALREADY_EXISTS",
                message=f"A customer with phone number '{normalized_phone}' already exists.",
            )

        customer = Customer(
            id=uuid.uuid4(),
            organization_id=organization_id,
            phone_number=normalized_phone,
            name=request.name.strip() if request.name else None,
            email=str(request.email) if request.email else None,
            metadata_=request.metadata or {},
            is_blocked=request.is_blocked,
        )
        session.add(customer)
        await session.flush()
        await session.refresh(customer) #why session.refresh because flush will only update the database but not the python object
        return customer

    @staticmethod
    async def get_customer(
        session: AsyncSession,
        organization_id: uuid.UUID,
        customer_id: uuid.UUID,
    ) -> Customer:
        """Retrieves a single customer by ID, enforcing tenant isolation."""
        query = select(Customer).where(
            Customer.organization_id == organization_id,
            Customer.id == customer_id,
        )
        customer = (await session.execute(query)).scalar_one_or_none()
        if customer is None:
            raise NotFoundException(
                code="CUSTOMER_NOT_FOUND",
                message="Customer not found.",
            )
        return customer

    @staticmethod
    async def get_customer_by_phone(
        session: AsyncSession,
        organization_id: uuid.UUID,
        phone_number: str,
    ) -> Customer | None:
        """Finds customer by normalized phone number within the tenant."""
        normalized_phone = normalize_e164_phone(phone_number)
        query = select(Customer).where(
            Customer.organization_id == organization_id,
            Customer.phone_number == normalized_phone,
        )
        return (await session.execute(query)).scalar_one_or_none()

    @staticmethod
    async def update_customer(
        session: AsyncSession,
        organization_id: uuid.UUID,
        customer_id: uuid.UUID,
        request: CustomerUpdate,
    ) -> Customer:
        """Updates customer profile fields."""
        customer = await CustomerService.get_customer(session, organization_id, customer_id)

        if request.name is not None:
            customer.name = request.name.strip() if request.name else None
        if request.email is not None:
            customer.email = str(request.email) if request.email else None
        if request.metadata is not None:
            customer.metadata_ = request.metadata
        if request.is_blocked is not None:
            customer.is_blocked = request.is_blocked

        await session.flush()
        await session.refresh(customer)
        return customer

    @staticmethod
    async def list_customers(
        session: AsyncSession,
        organization_id: uuid.UUID,
        page: int = 1,
        page_size: int = 20,
        search: str | None = None,
    ) -> tuple[Sequence[Customer], int]:
        """Lists customers belonging to an organization with pagination and search."""
        base_query = select(Customer).where(Customer.organization_id == organization_id)

        if search:
            search_clean = f"%{search.strip()}%"
            base_query = base_query.where(
                or_(
                    Customer.phone_number.ilike(search_clean),
                    Customer.name.ilike(search_clean),
                )
            )

        # Count total
        count_query = select(func.count()).select_from(base_query.subquery())
        total = (await session.execute(count_query)).scalar_one()

        # Paginate
        offset = (page - 1) * page_size
        items_query = (
            base_query.order_by(Customer.created_at.desc()).offset(offset).limit(page_size)
        )
        items = (await session.execute(items_query)).scalars().all()

        return items, total

