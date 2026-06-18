from sqlalchemy import *

from app.db.database import Base


class Chunk(Base):
    __tablename__ = "chunks"

    id = Column(
        String(36),
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

    filename = Column(String(255))

    row_start = Column(Integer)
    row_end = Column(Integer)

    row_count = Column(Integer)

    file_size_bytes = Column(BigInteger)