import os
import pytest
from professor_virtual.config import Config
from dotenv import find_dotenv, load_dotenv
from google.adk.evaluation.agent_evaluator import AgentEvaluator

pytest_plugins = ("pytest_asyncio",)


@pytest.fixture(scope="session", autouse=True)
def load_env():
    load_dotenv(find_dotenv(".env"))
    Config()


@pytest.mark.asyncio
async def test_eval_simple():
    """Avalia a habilidade básica do agente."""
    await AgentEvaluator.evaluate(
        "professor_virtual",
        os.path.join(os.path.dirname(__file__), "eval_data/simple.test.json"),
        num_runs=1,
    )

