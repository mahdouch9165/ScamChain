import time
import json
import redis
import psutil
from src.modules.w3.event.event_flow.honeypot_timer_flow_base_uniswap_v2 import HoneypotTimerFlowBaseUniswapV2
from src.modules.w3.chains.scanner.base_scanner import BaseScanner
from src.modules.w3.chains.official_base import OfficialBaseChain
from src.modules.w3.w3_connector import W3Connector
from src.modules.w3.exchange.uniswap_v2_base import UniswapV2Base
from src.modules.w3.wallet.wallet import Wallet
from dotenv import load_dotenv
import os
load_dotenv()

MNEMONIC = os.getenv("MNEMONIC")

r = redis.Redis(host='localhost', port=6379, db=2)

def main(w3, scanner, exchange, wallet):
    strategy = HoneypotTimerFlowBaseUniswapV2(w3, scanner, exchange, wallet)
    while True:
        # Block until there is a new event in the queue
        _, event_json = r.brpop("NewToken")
        event_data = json.loads(event_json)
        token1 = event_data["token1"]
        token0 = event_data["token0"]

        strategy.handle_event(event_data)

if __name__ == "__main__":
    # Clear the queue (optional)
    r.delete("NewToken")
    
    # Initialize chain and scanner
    chain = OfficialBaseChain()
    w3 = W3Connector(chain)
    scanner = BaseScanner()
    exchange = UniswapV2Base(w3, scanner)
    wallet = Wallet(mnemonic=MNEMONIC)
    
    main(w3, scanner, exchange, wallet)
