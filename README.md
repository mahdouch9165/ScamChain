# Crypto Project

## Architecture

- **Redis**: Message broker for event queue
- **Event Fetcher**: Listens for new token pairs from DEXes
- **Workers**: Process events and execute strategies
- **Dashboard**: Real-time monitoring UI

## Quick Start

### Prerequisites

- Python 3.9+
- Redis server

### Dotenv File Setup
- BaseScan API key (free)
- Infura API key (free)
- If you want (OPENAPI API key) for the llm module
- wallet mnemonic for the account module

### Other Notes:
- Get rid of the LLM module if you don't want to use it
- Feel free to implement your own security checks
- DONT LEAVE THIS ON UNMONITORED



redis-server
event_fetcher
