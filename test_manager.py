import pytest

from manager import ValueAreaManager, ValueAreaOrderClient

@pytest.fixture()
def vaManager(request):
    return ValueAreaManager()

# TODO: Create Mock ValueAreaOrderClient, use it to validate expectations for ValueAreaManager