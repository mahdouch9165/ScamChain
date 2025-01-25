import asyncio
import nest_asyncio
import redis
from web3 import Web3
from src.modules.w3.event.event_listener.uniswap_v2_listener import UniswapV2Listener
from src.modules.w3.w3_connector import W3Connector
from src.modules.w3.chains.official_base import OfficialBaseChain
from src.modules.w3.exchange.uniswap_v2_base import UniswapV2Base
from src.modules.w3.chains.scanner.base_scanner import BaseScanner

async def main():
    # Create a Redis client (synchronous or asynchronous version as you prefer)
    r = redis.Redis(host='localhost', port=6379, db=2)

    # Instantiate the Web3 connector
    chain = OfficialBaseChain()
    w3 = W3Connector(chain)
    scanner = BaseScanner()
    exchange = UniswapV2Base(w3, scanner)
    uniswap_v2_contract = exchange.factory_contract

    # Instantiate the listeners
    v2_listener = UniswapV2Listener(
        w3=w3,
        redis_client=r,
        v2_contract=uniswap_v2_contract,
        poll_interval=2
    )

    # Run both log loops concurrently
    await asyncio.gather(
        v2_listener.log_loop()
    )

if __name__ == "__main__":
    nest_asyncio.apply()
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Stopped listening for events.")
