import time
import json
import redis
import psutil
import multiprocessing
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

def process_event(event_data, mnemonic):
    # Reinitialize dependencies in the child process
    chain = OfficialBaseChain()
    w3 = W3Connector(chain)
    scanner = BaseScanner()
    exchange = UniswapV2Base(w3, scanner)
    wallet = Wallet(mnemonic=mnemonic)
    strategy = HoneypotTimerFlowBaseUniswapV2(w3, scanner, exchange, wallet)
    strategy.handle_event(event_data)

def main(w3, scanner, exchange, wallet):
    processed = 0
    discarded = 0
    while True:
        print(f"Processed: {processed}, Discarded: {discarded}")

        eth_balance = w3.get_eth_balance(wallet.address)
        if eth_balance < 0.0001:
            print("Low ETH balance, exiting...")
            break

        if (processed + discarded) % 10 == 0:
            print("Eth balance: ", eth_balance)

        _, event_json = r.brpop("NewToken")
        event_data = json.loads(event_json)
        token1 = event_data["token1"]
        token0 = event_data["token0"]

        cpu_percent = psutil.cpu_percent(interval=0.1)
        if cpu_percent < 80:
            processed += 1
            # Pass the MNEMONIC and event_data to the child process
            p = multiprocessing.Process(target=process_event, args=(event_data, MNEMONIC))
            p.start()
            new_cpu_percent = psutil.cpu_percent(interval=0.1)
            percent_diff = new_cpu_percent - cpu_percent
            print(f"New event: {token1} - {token0}.\nSpawned new process with PID {p.pid}. CPU usage increased by {percent_diff}%")
        else:
            print(f"New event: {token1} - {token0}.\nCPU usage too high, discarding...")
            discarded += 1

if __name__ == "__main__":
    chain = OfficialBaseChain()
    w3 = W3Connector(chain)
    scanner = BaseScanner()
    exchange = UniswapV2Base(w3, scanner)
    wallet = Wallet(mnemonic=MNEMONIC)

    r.delete("NewToken")
    main(w3, scanner, exchange, wallet)