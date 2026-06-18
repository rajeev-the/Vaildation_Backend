from fastapi import APIRouter
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.dependencies import get_db
from app.services.rule_loader import RuleLoader

router = APIRouter(
    prefix="/validation/rules",
    tags=["Validation Rules"]
)


@router.get("")
async def get_rules(db: AsyncSession = Depends(get_db)):

    rules = await RuleLoader.get_active_rules(db)

    return {"rules": rules}