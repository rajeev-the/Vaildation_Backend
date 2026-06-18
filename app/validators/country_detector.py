COUNTRY_PREFIXES = {
    "+91": "IN",
    "0091": "IN",

    "+65": "SG",
    "0065": "SG",

    "+1": "US",
    "+44": "UK",
    "+61": "AU"
}


def detect_country(phone: str):

    for prefix, country in COUNTRY_PREFIXES.items():

        if phone.startswith(prefix):
            return country

    return "IN"