from ..w3_connector import W3Connector
from ..chains.scanner.chain_scanner import ChainScanner
from .pair.pair import Pair
from decimal import Decimal, getcontext
import time

getcontext().prec = 28

def to_base_units(amount: Decimal, decimals: int) -> int:
    return int(amount * (Decimal(10) ** decimals))

def from_base_units(amount: int, decimals: int) -> Decimal:
    return Decimal(amount) / (Decimal(10) ** decimals)


class Exchange:
    def __init__(self):
        self.name = None
        pass

    def get_pair_address(self, token0, token1):
        raise NotImplementedError("This method must be implemented by a subclass.")
    
    def liquidity_check_usd(self, pair, w3, scanner):
        raise NotImplementedError("This method must be implemented by a subclass.")
