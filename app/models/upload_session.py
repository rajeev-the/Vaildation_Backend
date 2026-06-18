import uuid

from sqlalchemy import (
    Column,
    String,
    BigInteger,
    Integer,
    Enum,
    DateTime
)

from sqlalchemy.sql import func
from app.db.database import  Base


class UploadSession(Base):
    __tablename__ = "upload_sessions"

    id = Column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    original_filename = Column(String(255))
    file_size_bytes = Column(BigInteger)

    total_rows = Column(Integer, default=0)

    status = Column(
        Enum(
            "pending",
            "validating",
            "validated",
            "failed",
            name="upload_status"
        ),
        default="pending"
    )

    valid_rows = Column(Integer, default=0)
    error_rows = Column(Integer, default=0)

    created_at = Column(
        DateTime,
        server_default=func.now()
    )

    updated_at = Column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now()
    )