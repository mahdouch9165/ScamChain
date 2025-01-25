from .chain_scanner import *

load_dotenv()

BNB_SCAN_API_KEY = os.getenv("BNB_SCAN_API_KEY")

class BNBScanner(ChainScanner):
    def __init__(self):
        super().__init__()
        self.url = "https://api.bscscan.com/api"
        self.api_key = BNB_SCAN_API_KEY
