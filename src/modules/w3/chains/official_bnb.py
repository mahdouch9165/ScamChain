from .bnb import BNBChain

class OfficialBNBChain(BNBChain):
    def __init__(self):
        super().__init__('https://bsc-dataseed.bnbchain.org/')