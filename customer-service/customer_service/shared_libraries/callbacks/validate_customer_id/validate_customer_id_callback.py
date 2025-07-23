import logging
from typing import Tuple
from jsonschema import ValidationError
from google.adk.sessions.state import State
from customer_service.entities.customer import Customer

logger = logging.getLogger(__name__)


def validate_customer_id(customer_id: str, session_state: State) -> Tuple[bool, str]:
    """
        Validates the customer ID against the customer profile in the session state.
        
        Args:
            customer_id (str): The ID of the customer to validate.
            session_state (State): The session state containing the customer profile.
        
        Returns:
            A tuple containing an bool (True/False) and a String. 
            When False, a string with the error message to pass to the model for deciding
            what actions to take to remediate.
    """
    if 'customer_profile' not in session_state:
        return False, "No customer profile selected. Please select a profile."

    try:
        # We read the profile from the state, where it is set deterministically
        # at the beginning of the session.
        c = Customer.model_validate_json(session_state['customer_profile'])
        if customer_id == c.customer_id:
            return True, None
        else:
            return False, "You cannot use the tool with customer_id " +customer_id+", only for "+c.customer_id+"."
    except ValidationError as e:
        return False, "Customer profile couldn't be parsed. Please reload the customer data. "

