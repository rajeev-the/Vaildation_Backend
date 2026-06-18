from datetime import datetime

from app.validators.validation_result import ValidationResult
from app.services.rule_loader import RuleLoader


class DateValidator:

    @staticmethod
    async def validate(date_str, db):

        rules = await RuleLoader.get_date_rules(db)

        for rule in rules:

            try:

                parsed = datetime.strptime(
                    date_str.strip(),
                    rule.pattern
                )

                return ValidationResult(
                    status="valid",
                    cleaned=parsed.strftime(
                        "%Y-%m-%d"
                    )
                )

            except ValueError:
                continue

        return ValidationResult(
            status="invalid",
            message="Invalid date format"
        )