from .chains.chain import Chain
from web3 import Web3
from decimal import Decimal, getcontext
from dotenv import load_dotenv
import os
import requests
from ..utils.retry_request import *

load_dotenv()
getcontext().prec = 28

class W3Connector():
    def __init__(self, chain: Chain):
        self.chain = chain
        self.w3 = Web3(Web3.HTTPProvider(chain.url))
        self.INFURA_API_KEY = os.getenv("INFURA_API_KEY")

    def is_connected(self):
        return self.w3.is_connected()
    
    def to_checksum_address(self, address: str):
        return self.w3.to_checksum_address(address)
    
    def get_contract_instance(self, address: str, abi: list):
        return self.w3.eth.contract(address=address, abi=abi)
    
    def get_token_decimals(self, address: str):
        if address.lower() == "0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee":
            return 18  # "Native" ETH has 18 decimals
        abi = [{
            "constant": True,
            "inputs": [],
            "name": "decimals",
            "outputs":[{"name":"","type":"uint8"}],
            "type":"function"
        }]
        contract = self.get_contract_instance(address, abi)
        return contract.functions.decimals().call()
    
    def get_creator_address(self, tx_hash: str) -> str:
        """Returns the 'from' address (deployer) of the contract creation transaction."""
        if not tx_hash.startswith("0x"):
            tx_hash = "0x" + tx_hash
        tx = self.w3.eth.get_transaction(tx_hash)
        return tx["from"]
    
    def get_contract_bytecode(self, contract_address: str) -> str:
        """
        Returns the runtime bytecode of a contract at the given address as a hex string.

        :param contract_address: The address of the smart contract.
        :param web3_instance: An optional Web3 instance (defaults to global W3).
        :return: The runtime bytecode as a hex string (e.g., '0x...').
        """
        checksum_address = self.to_checksum_address(contract_address)
        code_bytes = self.w3.eth.get_code(checksum_address)
        return code_bytes.hex()
    
    def get_eth_balance(self, address: str):
        eth_in_wei = self.w3.eth.get_balance(address)
        eth_balance = float(self.w3.from_wei(eth_in_wei, 'ether'))
        return eth_balance

    def decode_transfer_logs(self, logs):
        """
        Decodes ERC-20 Transfer events from a list of logs.
        Returns a list of tuples: (token_address, from_address, to_address, amount_in_wei).
        """
        # The keccak of "Transfer(address,address,uint256)"
        TRANSFER_TOPIC = Web3.keccak(text="Transfer(address,address,uint256)").hex().lower()
        
        transfers = []
        for log in logs:
            # 1) Check that it's a Transfer event
            if len(log['topics']) > 0 and log['topics'][0].hex().lower() == TRANSFER_TOPIC:
                token_address = log['address']
                
                # 2) Extract from/to addresses from the topics
                from_address = "0x" + log['topics'][1].hex()[-40:]
                to_address = "0x" + log['topics'][2].hex()[-40:]
                
                # 3) Extract amount from 'data'
                raw_data = log['data']
                
                # If it's already a str with "0x" prefix, we can do int(raw_data, 16).
                # If it's bytes, convert to hex string first.
                if isinstance(raw_data, bytes):
                    # Convert bytes -> hex string
                    raw_data = raw_data.hex()
                
                amount_in_wei = int(raw_data, 16)

                transfers.append((token_address, from_address, to_address, amount_in_wei))

        return transfers
    
    def get_block_number(self):
        return self.w3.eth.get_block_number()

    def get_transaction_count(self, address: str):
        return self.w3.eth.get_transaction_count(address)

    def sign_transaction(self, transaction: dict, private_key: str):
        signed_tx = self.w3.eth.account.sign_transaction(transaction, private_key)
        return signed_tx
    
    def send_raw_transaction(self, signed_tx: str):
        return self.w3.eth.send_raw_transaction(signed_tx)

    def wait_for_transaction_receipt(self, tx_hash: str):
        return self.w3.eth.wait_for_transaction_receipt(tx_hash)
    
    def to_hex(self, value: int):
        return self.w3.to_hex(value)

    def fetch_gas_price(self, level: str = "medium") -> dict:
        """
        Fetch recommended maxFeePerGas and maxPriorityFeePerGas from Infura's Gas API.
        Level can be 'low', 'medium', or 'high'.
        Returns a dict with:
            {
            "maxFeePerGas": int,        # in Wei
            "maxPriorityFeePerGas": int # in Wei
            }
        """
        url = f"https://gas.api.infura.io/v3/{self.INFURA_API_KEY}/networks/{self.chain.chain_id}/suggestedGasFees"
        # Use retryable_request_fixed instead of requests.get
        resp = retryable_request_fixed("GET", url)

        data = resp.json()

        # Each of these is a string in Gwei, e.g. "32.548678862"
        suggested_max_fee_gwei = Decimal(data[level]["suggestedMaxFeePerGas"])
        suggested_priority_gwei = Decimal(data[level]["suggestedMaxPriorityFeePerGas"])

        # Convert Gwei -> Wei
        max_fee_wei = int(suggested_max_fee_gwei * Decimal(1e9))
        priority_fee_wei = int(suggested_priority_gwei * Decimal(1e9))

        return {
            "maxFeePerGas": max_fee_wei,
            "maxPriorityFeePerGas": priority_fee_wei
        }