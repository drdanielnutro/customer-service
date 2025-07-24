import logging

logger = logging.getLogger(__name__)


def send_care_instructions(
    customer_id: str, plant_type: str, delivery_method: str
) -> dict:
    """Sends an email or SMS with instructions on how to take care of a specific plant type.

    Args:
        customer_id:  The ID of the customer.
        plant_type: The type of plant.
        delivery_method: 'email' (default) or 'sms'.

    Returns:
        A dictionary indicating the status.

    Example:
        >>> send_care_instructions(customer_id='123', plant_type='Petunias', delivery_method='email')
        {'status': 'success', 'message': 'Care instructions for Petunias sent via email.'}
    """
    logger.info(
        "Sending care instructions for %s to customer: %s via %s",
        plant_type,
        customer_id,
        delivery_method,
    )
    # MOCK API RESPONSE - Replace with actual API call or email/SMS sending logic
    return {
        "status": "success",
        "message": f"Care instructions for {plant_type} sent via {delivery_method}.",
    }

