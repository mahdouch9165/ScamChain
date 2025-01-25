from ...chains.scanner.chain_scanner import ChainScanner
from ...w3_connector import W3Connector
from ....utils.function_names import get_function_names
from ....utils.ABI import MIN_ERC20_ABI

class Token:
    def __init__(self, address, w3: W3Connector, scanner: ChainScanner):
        self.address = w3.to_checksum_address(address)
        self.code, self.contract_name = scanner.get_contract_source_code_and_name(address)
        # If self.code == "failed", then the contract does not exist
        if self.code == "failed":
            raise ValueError(f"Contract with address {address} does not exist or cannot be found.")
                # check open source
        if len(self.code) == 0:
            self.open_source = False
            raise ValueError(f"Contract with address {address} is closed source.")
        else:
            self.open_source = True
            # save the code as a text file under data/code
            with open(f"data/code/{address}.txt", "w") as f:
                f.write(self.code)
        # get abi
        self.abi = MIN_ERC20_ABI
        
        # get contract instance
        self.contract = w3.get_contract_instance(self.address, self.abi)

        # get token decimals
        self.decimals = w3.get_token_decimals(self.address)

        # get creation details
        contract_creation = scanner.get_contract_creation(self.address)
        self.contract_creator = contract_creation["contractCreator"]
        self.creation_hash = contract_creation["txHash"]
        self.creation_block = contract_creation["blockNumber"]
        self.creation_timestamp = contract_creation["timestamp"]

        # get token functions
        self.functions = get_function_names(self.code)

    def get_balance(self, address):
        balance = self.contract.functions.balanceOf(address).call()
        return balance / (10 ** self.decimals)
    
    def to_dict(self):
        return {
            "address": self.address,
            "open_source": self.open_source,
            "contract_name": self.contract_name,
            "decimals": self.decimals,
            "contract_creator": self.contract_creator,
            "creation_hash": self.creation_hash,
            "creation_block": self.creation_block,
            "creation_timestamp": self.creation_timestamp,
            "functions": self.functions
        }
