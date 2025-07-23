import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


def generate_qr_code(
    customer_id: str,
    discount_value: float,
    discount_type: str,
    expiration_days: int,
) -> dict:
    """Generates a QR code for a discount.

    Args:
        customer_id: The ID of the customer.
        discount_value: The value of the discount (e.g., 10 for 10%).
        discount_type: "percentage" (default) or "fixed".
        expiration_days: Number of days until the QR code expires.

    Returns:
        A dictionary containing the QR code data (or a link to it). Example:
        {'status': 'success', 'qr_code_data': '...', 'expiration_date': '2024-08-28'}

    Example:
        >>> generate_qr_code(customer_id='123', discount_value=10.0, discount_type='percentage', expiration_days=30)
        {'status': 'success', 'qr_code_data': 'MOCK_QR_CODE_DATA', 'expiration_date': '2024-08-24'}
    """
    
    # Guardrails to validate the amount of discount is acceptable for a auto-approved discount.
    # Defense-in-depth to prevent malicious prompts that could circumvent system instructions and
    # be able to get arbitrary discounts.
    if discount_type == "" or discount_type == "percentage":
        if discount_value > 10:
            return "cannot generate a QR code for this amount, must be 10% or less"
    if discount_type == "fixed" and discount_value > 20:
        return "cannot generate a QR code for this amount, must be 20 or less"
    
    logger.info(
        "Generating QR code for customer: %s with %s - %s discount.",
        customer_id,
        discount_value,
        discount_type,
    )
    # MOCK API RESPONSE - Replace with actual QR code generation library
    expiration_date = (
        datetime.now() + timedelta(days=expiration_days)
    ).strftime("%Y-%m-%d")
    return {
        "status": "success",
        "qr_code_data": "MOCK_QR_CODE_DATA",  # Replace with actual QR code
        "expiration_date": expiration_date,
    }
