
from sqlalchemy import (
    Column, Integer, String, DateTime, Boolean
)
from sqlalchemy.sql import func

from app.db.database import Base


class EmailConnection(Base):
    __tablename__ = "email_connections"

    id = Column(Integer, primary_key=True, index=True)

    # Replace with your actual user/organization foreign keys
    # when integrating your authentication system.
    user_id = Column(Integer, nullable=False, index=True)

    email_address = Column(String(255), nullable=False)

    provider = Column(String(30), default="gmail")

    encrypted_credentials = Column(String, nullable=False)

    is_active = Column(Boolean, default=True)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )
