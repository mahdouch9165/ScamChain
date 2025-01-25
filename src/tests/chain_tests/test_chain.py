# tests/test_chain.py

import pytest
from ...modules.w3.chains.chain import Chain

def test_chain_initialization():
    chain = Chain(name="TestNet", chain_id=9999, url="http://testnet.example")
    assert chain.name == "TestNet"
    assert chain.chain_id == 9999
    assert chain.url == "http://testnet.example"