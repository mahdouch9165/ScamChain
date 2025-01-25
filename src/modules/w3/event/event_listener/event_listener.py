import json
import asyncio
from web3.exceptions import BlockNotFound
from ...w3_connector import W3Connector

class EventListener:
    """
    Base class that holds the core logic for fetching events, pushing them to Redis,
    and continuously polling the blockchain for new events.
    """
    def __init__(self, w3, redis_client, contract, event_name, source, poll_interval=2):
        """
        :param web3: A Web3 instance configured for the desired network.
        :param redis_client: A redis.Redis or redis.asyncio.Redis instance.
        :param contract: A Web3 contract object with the event you want to filter.
        :param event_name: The name of the event to watch (e.g. "PairCreated" or "PoolCreated").
        :param source: The source of the event (e.g. "UniswapV2Factory").
        :param poll_interval: How often (in seconds) to poll for new blocks/events.
        """
        self.w3 = w3
        self.r = redis_client
        self.contract = contract
        self.event_name = event_name
        self.poll_interval = poll_interval
        self.source = source
        self.last_processed_block = None

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
        self.r.lpush("my_events", event_json)

    async def fetch_events(self, start_block, end_block):
        """
        Fetch logs from the contract's specific event from start_block to end_block.
        The `retry_with_backoff` decorator means it will automatically retry on errors.
        """
        try:
            event_abi = getattr(self.contract.events, self.event_name)
            # The call to get_logs is synchronous in web3.py, but we can wrap it in a thread if needed.
            events = event_abi().get_logs(from_block=start_block, to_block=end_block)
            return events
        except Exception as e:
            print(f"Error fetching events: {e}")
            return []

    async def log_loop(self):
        """
        Continuously poll for new blocks. 
        When a new block is found, fetch any events in that block range.
        """
        while True:
            try:
                current_block = self.w3.get_block_number()
                if self.last_processed_block is None:
                    # Start from the current block minus 1
                    self.last_processed_block = current_block - 1

                # Only fetch if there's something new
                if current_block > self.last_processed_block:
                    start_block = self.last_processed_block + 1
                    # We fetch events from [start_block, current_block]
                    events = await self.fetch_events(start_block, current_block)
                    
                    for event in events:
                        self.handle_event(event)

                    self.last_processed_block = current_block

                await asyncio.sleep(self.poll_interval)
            except BlockNotFound:
                print("Block not found. Retrying...")
                await asyncio.sleep(1)
            except Exception as e:
                print(f"Error in log_loop: {e}")
                await asyncio.sleep(1)

