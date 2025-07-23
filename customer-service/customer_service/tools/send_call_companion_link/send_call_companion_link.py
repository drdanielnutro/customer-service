import logging

logger = logging.getLogger(__name__)

def send_call_companion_link(phone_number: str) -> str:
    """Sends a link to the user's phone number to start a video session.

    Args:
        phone_number (str): The phone number to send the link to.

    Returns:
        dict: A dictionary with the status and message.

    Example:
        >>> send_call_companion_link(phone_number='+12065550123')
        {'status': 'success', 'message': 'Link sent to +12065550123'}
    """
    logger.info("Sending call companion link to %s", phone_number)
    return {"status": "success", "message": f"Link sent to {phone_number}"}
