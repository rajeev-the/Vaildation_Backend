import re

from app.validators.validation_result import ValidationResult
from app.validators.country_detector import detect_country
from app.services.rule_loader import RuleLoader


class PhoneValidator:

    @staticmethod
    async def validate(phone: str, db):

        if not phone:

            return ValidationResult(
                status="invalid",
                message="Phone missing"
            )

        phone = re.sub(
            r"[\s\-\(\)]",
            "",
            phone
        )

        country_code = detect_country(phone)

        rule = await RuleLoader.get_phone_rule(
            db,
            country_code
        )

        if not rule:

            return ValidationResult(
                status="warning",
                message=f"No rule configured for {country_code}"
            )

        prefixes = [
            "91",
            "0091",
            "+65",
            "0065",
            "+44",
            "+61",
            "+1"
        ]

        for prefix in prefixes:

            if phone.startswith(prefix):

                phone = phone[len(prefix):]
                break

        if len(phone) != rule.digit_count:

            return ValidationResult(
                status="invalid",
                message=f"Expected {rule.digit_count} digits"
            )

        if not re.match(rule.pattern, phone):

            return ValidationResult(
                status="invalid",
                message="Invalid phone format"
            )

        return ValidationResult(
            status="valid",
            cleaned=phone
        )