import hashlib
import random
import string
import sqlite3

# ------------------------------------------------------------
# --- NAME ANONYMIZATION ---
# ------------------------------------------------------------
def generate_anonymized_name(name: str) -> str:
    """
    Returns a stable anonymized name like ANON_3021.
    The number is derived from a hash so the same name
    always produces the same anonymized label.
    """
    hashed = hashlib.sha256(name.encode()).hexdigest()
    # Take last 4 digits for short anonymized ID
    anon_id = hashed[-4:]
    return f"ANON_{anon_id}"


# ------------------------------------------------------------
# --- CONTACT MASKING ---
# ------------------------------------------------------------
def generate_masked_contact(contact: str) -> str:
    """
    Masks contact like XXX-XXX-1234 (keeps last 4 digits).
    Works with or without dashes.
    """
    digits = "".join([c for c in contact if c.isdigit()])

    if len(digits) < 4:
        return "XXX-XXX-XXXX"

    last4 = digits[-4:]
    return f"XXX-XXX-{last4}"
