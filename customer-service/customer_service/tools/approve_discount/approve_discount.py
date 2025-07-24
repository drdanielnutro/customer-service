import logging

logger = logging.getLogger(__name__)

def approve_discount(discount_type: str, value: float, reason: str) -> str:
    """Approve the flat rate or percentage discount requested by the user.

    Args:
        discount_type (str): The type of discount, either "percentage" or "flat".
        value (float): The value of the discount.
        reason (str): The reason for the discount.

    Returns:
        str: A JSON string indicating the status of the approval.

    Example:
        >>> approve_discount(type='percentage', value=10.0, reason='Customer loyalty')
        '{"status": "ok"}'
    """
    if value > 10:
        logger.info("Denying %s discount of %s", discount_type, value)
        return {"status": "rejected", "message": "discount too large. Must be 10 or less."}
    logger.info(
        "Approving a %s discount of %s because %s", discount_type, value, reason
    )
    return {"status": "ok"}
