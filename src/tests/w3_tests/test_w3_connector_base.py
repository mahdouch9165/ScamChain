# tests/test_w3_connector_base.py

import pytest
from ...modules.w3.chains.official_base import OfficialBaseChain
from ...modules.w3.w3_connector import W3Connector

def test_chain_initialization():
    base_chain = OfficialBaseChain()
    w3_connector = W3Connector(base_chain)
    assert w3_connector.w3.is_connected()
    