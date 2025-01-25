from eth_account import Account
from ..exchange.token.token import Token
Account.enable_unaudited_hdwallet_features()

class Wallet():
    def __init__(self, private_key = None, mnemonic = None):
        if mnemonic:
            self.wallet = Account.from_mnemonic(mnemonic)
            self.key = self.wallet.key
            self.mnemonic = mnemonic
        elif private_key:
            self.wallet = Account.from_key(private_key)
            self.key = private_key
            self.mnemonic = None
        else:
            raise ValueError('Either private_key or mnemonic must be provided')
        self.address = self.wallet.address

    def get_token_balance(self, token: Token):
        return token.get_balance(self.address)
    

    