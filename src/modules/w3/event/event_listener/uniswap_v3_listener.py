from .event_listener import *

class UniswapV3Listener(EventListener):
    """
    Specific listener for Uniswap V3 PoolCreated events.
    """
    def __init__(self, w3, redis_client, v3_contract, poll_interval=2):
        super().__init__(
            w3=w3,
            redis_client=redis_client,
            contract=v3_contract,
            event_name="PoolCreated",
            source= "UniswapV3",
            poll_interval=poll_interval
        )

    def handle_event(self, event):
        """
        Handle a single event object (returned by contract.events.<Event>.get_logs).
        Convert to JSON, push to Redis, etc.
        Subclasses or instances can override or extend this as needed.
        """
        data = {
            "blockNumber": event.blockNumber,
            "blockHash": event.blockHash.hex(),
            "transactionHash": event.transactionHash.hex(),
            "token0": event.args.get("token0"),
            "token1": event.args.get("token1"),
            "pair": event.args.get("pair", event.args.get("pool")),
            "source": self.source
        }
        print(f"Pushing event to Redis: {data['pair']}")
        event_json = json.dumps(data)
        self.r.lpush("NewToken", event_json)



