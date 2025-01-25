import json
from ....utils.retry_request import *
from dotenv import load_dotenv
import os

class ChainScanner:
    def __init__(self):
        self.url = None
        self.api_key = None

    def get_contract_source_code_and_name(self, contract_address: str):
        """
        Retrieve the source code for a given contract from BaseScan.
        """
        params = {
            "module": "contract",
            "action": "getsourcecode",
            "address": contract_address,
            "apikey": self.api_key
        }
        try:
            response = retryable_request_fixed_basescan(
            method="GET",
            url=self.url,
            attempts=3,
            wait_seconds=2,
            params=params,
            timeout=10
        )
        except Exception as e:
            raise Exception(f"Failed to get contract source code: {e}")
        data = response.json()

        if "result" in data and data["result"]:
            if data["status"] == '0':
                return ("failed", None)
            source_code = data["result"][0]["SourceCode"].strip()
            name = data["result"][0]["ContractName"]
            # If it starts with "{{" and ends with "}}", remove one layer
            if source_code.startswith("{{") and source_code.endswith("}}"):
                source_code = source_code[1:-1]
            try:
                # load dict from str
                code_dict = json.loads(source_code)
                code = ""
                # iterate over code_dict["sources"]
                for source in code_dict["sources"].values():
                    code += source["content"]
                    code += "\n"
            except:
                code = source_code
            return code, name
        else:
            raise Exception(
                f"Request failed or empty result. Status code: {response.status_code}"
            )
        
    def get_contract_abi(self, contract_address: str):
        """
        Retrieve the ABI for a given contract from BaseScan.
        """
        params = {
            "module": "contract",
            "action": "getabi",
            "address": contract_address,
            "apikey": self.api_key
        }
        try:
            response = retryable_request_fixed_basescan(
                method="GET",
                url=self.url,
                attempts=3,
                wait_seconds=2,
                params=params,
                timeout=10
            )
        except Exception as e:
            raise Exception(f"Failed to get contract ABI: {e}")

        data = response.json()
        if "result" in data and data["result"]:
            if data["status"] == '0':
                if data["result"] == "Contract source code not verified":
                    return "closed source"
                return "failed"
            # return the ABI
            abi = json.loads(data["result"])
            return abi
        else:
            raise Exception(
                f"Request failed or empty result. Status code: {response.status_code}"
            )
        
    def get_contract_creation(self, contract_addresses: str):
        """
        Retrieve contract creation information for one or more contract addresses
        from BaseScan. `contract_addresses` can be a single string or a list of addresses.
        """
        # If a list is passed, join by comma. If a single address (string) is passed, just use it directly.
        if isinstance(contract_addresses, list):
            addresses = ",".join(contract_addresses)
        else:
            addresses = contract_addresses  # assume string

        params = {
            "module": "contract",
            "action": "getcontractcreation",
            "contractaddresses": addresses,
            "apikey": self.api_key
        }

        try:
            response = retryable_request_fixed_basescan(
                method="GET",
                url=self.url,
                attempts=3,
                wait_seconds=2,
                params=params,
                timeout=10
            )
        except Exception as e:
            raise Exception(f"Failed to get contract creation data: {e}")

        data = response.json()
        if "result" in data and data["result"]:
            if data["status"] == '0':
                # If status is '0', the result might contain an error message
                return "failed"
            
            # If everything is OK, return the 'result' part which contains 
            # the creation data for the contract(s)
            return data["result"][0]
        else:
            raise Exception(
                f"Request failed or empty result. Status code: {response.status_code}"
            )
