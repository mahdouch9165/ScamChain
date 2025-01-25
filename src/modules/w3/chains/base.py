from .chain import Chain

class BaseChain(Chain):
    def __init__(self, url):
        super().__init__('Base', 8453, url)