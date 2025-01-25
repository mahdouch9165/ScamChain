from .event_listener import *

class UniswapV2Listener(EventListener):
    """
    Specific listener for Uniswap V2 PairCreated events.
    """
    def __init__(self, w3, redis_client, v2_contract, poll_interval=2):
        super().__init__(
            w3=w3,
            redis_client=redis_client,
            contract=v2_contract,
            event_name="PairCreated",
            source="UniswapV2",
            poll_interval=poll_interval
        )

    def handle_event(self, event):
        # If the "PairCreated" event has different args from the base, handle them here
        pair_created_data = {
            "blockNumber": event.blockNumber,
            "blockHash": event.blockHash.hex(),
            "transactionHash": event.transactionHash.hex(),
            "token0": event.args["token0"],
            "token1": event.args["token1"],
            "pair": event.args["pair"],
        }
        print(f"Pushing event to Redis: {pair_created_data['pair']}")
        event_json = json.dumps(pair_created_data)
        self.r.lpush("NewToken", event_json)
