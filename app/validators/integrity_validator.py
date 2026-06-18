
class IntegrityValidator:

    REQUIRED_FIELDS = [
        "order_id",
        "amount",
        "order_date",
        "phone",
        "payment_mode"
    ]

    VALID_PAYMENT_MODES = {
        "cash",
        "card",
        "upi",
        "wallet",
        "cod",
        "net_banking"
    }

    @staticmethod
    def validate(row):

        errors = []

        # Required field checks
        for field in IntegrityValidator.REQUIRED_FIELDS:

            value = row.get(field)

            if value is None:

                errors.append({
                    "field": field,
                    "message": "Required field missing"
                })

                continue

            if str(value).strip() == "":

                errors.append({
                    "field": field,
                    "message": "Empty field"
                })

        # Amount validation
        amount = row.get("amount")

        if amount is not None and str(amount).strip() != "":

            try:
                float(str(amount).strip())

            except (ValueError, TypeError):

                errors.append({
                    "field": "amount",
                    "message": "Amount must be numeric"
                })

        # Payment mode validation
        payment = row.get("payment_mode")

        if payment and str(payment).strip():

            if payment.lower().strip() not in IntegrityValidator.VALID_PAYMENT_MODES:

                errors.append({
                    "field": "payment_mode",
                    "message": "Invalid payment mode"
                })

        return errors