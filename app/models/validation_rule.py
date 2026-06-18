from sqlalchemy import *

from app.db.database import Base


class ValidationRule(Base):
    __tablename__ = "validation_rules"

    id = Column(Integer, primary_key=True)

    rule_type = Column(
        Enum(
            "phone",
            "date_format",
            "regex",
            "required",
            "type_check",
              name="rule_type_enum"
            
        )
    )

    rule_key = Column(
        String(100),
        unique=True
    )

    country_code = Column(String(5))
    country_name = Column(String(100))

    pattern = Column(String(255))

    digit_count = Column(Integer)

    description = Column(Text)

    is_active = Column(Boolean, default=True)