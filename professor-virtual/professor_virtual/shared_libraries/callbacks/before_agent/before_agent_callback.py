import logging
from google.adk.agents.invocation_context import InvocationContext
from customer_service.entities.customer import Customer

logger = logging.getLogger(__name__)


def before_agent(callback_context: InvocationContext):
    # In a production agent, this is set as part of the
    # session creation for the agent. 
    if "customer_profile" not in callback_context.state:
        callback_context.state["customer_profile"] = Customer.get_customer(
            "123"
        ).to_json()

    # logger.info(callback_context.state["customer_profile"])
