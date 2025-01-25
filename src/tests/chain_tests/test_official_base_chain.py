# tests/test_base_chain.py

import pytest
from ...modules.w3.chains.official_base import OfficialBaseChain

def test_base_chain_inheritance():
    base_chain = OfficialBaseChain()
    # BaseChain inherits from Chain, so test the inherited props too
    assert base_chain.name == "Base"
    assert base_chain.chain_id == 8453
    assert base_chain.url == "https://mainnet.base.org"
