from .base import BaseChain

class OfficialBaseChain(BaseChain):
    def __init__(self):
        super().__init__('https://mainnet.base.org')