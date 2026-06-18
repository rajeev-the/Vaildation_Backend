from sqlalchemy import *
from sqlalchemy.dialects.mysql import JSON

from app.db.database import Base


class ValidatedRow(Base):
    __tablename__ = "validated_rows"

    id = Column(
        BigInteger,
        primary_key=True
    )

    session_id = Column(
        String(36),
        ForeignKey(
            "upload_sessions.id",
            ondelete="CASCADE"
        )
    )

    chunk_index = Column(Integer)
    row_index = Column(Integer)

    raw_data = Column(JSON)

    cleaned_data = Column(JSON)

    validation_status = Column(
        Enum(
            "valid",
            "invalid",
            "warning",
            name="validation_status_enum"
        )
    )

    validation_errors = Column(JSON)