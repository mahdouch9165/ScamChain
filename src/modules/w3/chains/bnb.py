from .chain import Chain

class BNBChain(Chain):
    def __init__(self, url):
        super().__init__('BNB', 56, url)