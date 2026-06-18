from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.validation_rule import ValidationRule


class RuleLoader:

    @staticmethod
    async def get_active_rules(db: AsyncSession):

        result = await db.execute(
            select(ValidationRule).filter(ValidationRule.is_active == True)
        )

        return result.scalars().all()

    @staticmethod
    async def get_phone_rule(db: AsyncSession, country_code: str):

        result = await db.execute(
            select(ValidationRule).filter(
                ValidationRule.rule_type == "phone",
                ValidationRule.country_code == country_code,
                ValidationRule.is_active == True
            )
        )

        return result.scalars().first()

    @staticmethod
    async def get_date_rules(db: AsyncSession):

        result = await db.execute(
            select(ValidationRule).filter(
                ValidationRule.rule_type == "date_format",
                ValidationRule.is_active == True
            )
        )

        return result.scalars().all()