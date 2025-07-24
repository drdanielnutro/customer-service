import logging

logger = logging.getLogger(__name__)


def get_product_recommendations(plant_type: str, customer_id: str) -> dict:
    """Provides product recommendations based on the type of plant.

    Args:
        plant_type: The type of plant (e.g., 'Petunias', 'Sun-loving annuals').
        customer_id: Optional customer ID for personalized recommendations.

    Returns:
        A dictionary of recommended products. Example:
        {'recommendations': [
            {'product_id': 'soil-456', 'name': 'Bloom Booster Potting Mix', 'description': '...'},
            {'product_id': 'fert-789', 'name': 'Flower Power Fertilizer', 'description': '...'}
        ]}
    """
    #
    logger.info(
        "Getting product recommendations for plant " "type: %s and customer %s",
        plant_type,
        customer_id,
    )
    # MOCK API RESPONSE - Replace with actual API call or recommendation engine
    if plant_type.lower() == "petunias":
        recommendations = {
            "recommendations": [
                {
                    "product_id": "soil-456",
                    "name": "Bloom Booster Potting Mix",
                    "description": "Provides extra nutrients that Petunias love.",
                },
                {
                    "product_id": "fert-789",
                    "name": "Flower Power Fertilizer",
                    "description": "Specifically formulated for flowering annuals.",
                },
            ]
        }
    else:
        recommendations = {
            "recommendations": [
                {
                    "product_id": "soil-123",
                    "name": "Standard Potting Soil",
                    "description": "A good all-purpose potting soil.",
                },
                {
                    "product_id": "fert-456",
                    "name": "General Purpose Fertilizer",
                    "description": "Suitable for a wide variety of plants.",
                },
            ]
        }
    return recommendations


