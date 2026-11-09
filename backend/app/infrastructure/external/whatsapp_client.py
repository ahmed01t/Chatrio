"""Re-export WhatsAppClient from app.infrastructure.whatsapp."""

from app.infrastructure.whatsapp.client import WhatsAppAPIError, WhatsAppClient

__all__ = ["WhatsAppAPIError", "WhatsAppClient"]

