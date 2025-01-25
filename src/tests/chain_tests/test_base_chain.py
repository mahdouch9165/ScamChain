# tests/test_base_chain.py

import pytest
from ...modules.w3.chains.base import BaseChain

def test_base_chain_inheritance():
    base_chain = BaseChain(url="http://base.example")
    # BaseChain inherits from Chain, so test the inherited props too
    assert base_chain.name == "Base"
    assert base_chain.chain_id == 8453
    assert base_chain.url == "http://base.example"
