import os
import sys

import pytest

# Add the parent folder to the system path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from clients.exchange import Exchange

NAME = "coinbase"  # use 'ACE' exchange to test Exchange class
EXCHANGE_LNAME = "Coinbase Advanced"
API_KEY = "APIKEY208823421"
API_SECRET = "APISECRET234"


@pytest.fixture
def exch():
    return Exchange(exchange_name=NAME, api_key=API_KEY, secret=API_SECRET)


class TestExchange:
    @pytest.mark.github
    @pytest.mark.base
    def test_exchange_exists(self, exch):
        assert exch is not None

    @pytest.mark.github
    @pytest.mark.base
    def test_exchange_name(self, exch):
        assert exch is not None
        assert exch._api.name == EXCHANGE_LNAME
