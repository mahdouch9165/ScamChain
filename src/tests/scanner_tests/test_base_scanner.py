# tests/test_base_scanner_code.py

import pytest
import time
from ...modules.w3.chains.scanner.base_scanner import BaseScanner

# normal/single source code
test_address_1 = "0xCB1f0F251AD4b7271f26415744b2475D081d3E00"
# normal/multiple source code
test_address_2 = "0x0b3e328455c4059EEb9e3f84b5543F74E24e7E1b"
# closed source
test_address_3 = "0xdA3A07bB58A4db185f95Ada2522aa2944a4a3b3e"
# does not exist
test_address_4 = "0xbbFacDfe1aE6f408564D5e30f84eC3E09"

def test_get_contract_source_code():
    scanner = BaseScanner()

    contract_1, name_1 = scanner.get_contract_source_code_and_name(test_address_1)
    contract_2, name_2 = scanner.get_contract_source_code_and_name(test_address_2)
    contract_3, name_3 = scanner.get_contract_source_code_and_name(test_address_3)
    contract_4, name_4 = scanner.get_contract_source_code_and_name(test_address_4)

    # assert that both are strings of length > 0
    assert isinstance(contract_1, str)
    assert isinstance(contract_2, str)
    assert isinstance(contract_3, str)
    assert isinstance(contract_4, str)
    assert len(contract_1) > 0
    assert len(contract_2) > 0
    assert len(contract_3) == 0
    assert contract_4 == "failed"

def test_get_contract_abi():
    scanner = BaseScanner()

    abi_1 = scanner.get_contract_abi(test_address_1)
    abi_3 = scanner.get_contract_abi(test_address_3)
    abi_4 = scanner.get_contract_abi(test_address_4)

    # assert that both are strings of length > 0
    assert isinstance(abi_1, list)
    assert isinstance(abi_3, str)
    assert isinstance(abi_4, str)
    assert len(abi_1) > 0
    assert abi_3 == "closed source"
    assert abi_4 == "failed"