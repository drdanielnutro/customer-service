import logging
import pytest
from professor_virtual.config import Config


@pytest.fixture
def conf():
    return Config()


def test_settings_loading(conf):
    logging.info(conf.model_dump())
    assert conf.agent_settings.model.startswith("gemini")


