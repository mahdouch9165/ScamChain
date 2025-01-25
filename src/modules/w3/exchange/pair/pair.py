from ...chains.scanner.chain_scanner import ChainScanner
from ...w3_connector import W3Connector
from ....utils.ABI import PAIR_ABI

class Pair():
    def __init__(self, token_0, token_1, w3: W3Connector, scanner: ChainScanner, exchange):
        self.exchange = exchange.name
        self.pair_address = w3.to_checksum_address(exchange.get_pair_address(token_0, token_1))
        if self.pair_address == '0x0000000000000000000000000000000000000000':
            self.is_valid = False
            return
        self.pair_abi = PAIR_ABI
        self.pair_contract = w3.get_contract_instance(self.pair_address, self.pair_abi)
        if token_0.address == self.get_token0():
            self.token_0 = token_0
            self.token_1 = token_1
            self.is_valid = True
        elif token_0.address == self.get_token1():
            self.token_0 = token_1
            self.token_1 = token_0
            self.is_valid = True
        else:
            self.is_valid = False
        contract_creation = scanner.get_contract_creation(self.pair_address)
        self.creation_hash = contract_creation["txHash"]
        self.creation_block = contract_creation["blockNumber"]
        self.creation_timestamp = contract_creation["timestamp"]

    def get_reserves(self):
        return self.pair_contract.functions.getReserves().call()
    
    def get_token0(self):
        return self.pair_contract.functions.token0().call()
    
    def get_token1(self):
        return self.pair_contract.functions.token1().call()
    
    def to_dict(self):
        return {
            "exchange": self.exchange,
            "pair_address": self.pair_address,
            "token_0": self.token_0.to_dict(),
            "token_1": self.token_1.to_dict(),
            "creation_hash": self.creation_hash,
            "creation_block": self.creation_block,
            "creation_timestamp": self.creation_timestamp
        }
